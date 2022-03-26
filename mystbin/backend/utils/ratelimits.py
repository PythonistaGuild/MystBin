from __future__ import annotations
import asyncio
import functools
from itertools import count
import time
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Iterator, List, Optional, Union, cast

import aioredis
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.routing import Match

from . import tokens

if TYPE_CHECKING:
    from main import MystbinApp

class IPBanned(Exception):
    pass

class NoRedisConnection(Exception):
    pass

time_units = {
    "second": 1,
    "minute": 60,
    "hour": 60 * 60,
    "day": 60 * 60 * 24,
    "week": 60 * 60 * 24 * 7,
    "month": 60 * 60 * 24 * 30,
    "year": 60 * 60 * 24 * 365
}

class BaseLimitBucket:
    def __init__(self, app: MystbinApp, key: str, count: int, per: int) -> None:
        self.count = count
        self.per = per
    
    async def _clear_dead_keys(self) -> None:
        raise NotImplementedError
    
    async def hit(self) -> tuple[bool, int]:
        raise NotImplementedError
    
    async def is_limited(self) -> bool:
        raise NotImplementedError
    
    @property
    def reset_at(self):
        raise NotImplementedError

class InMemoryLimitBucket(BaseLimitBucket):
    """
    The in-memory bucket uses the "leaky bucket" method.
    As such, there is no reset time.
    """

    __slots__ = ("count", "per", "hits")

    def __init__(self, app: MystbinApp, key: str, count: int, per: int) -> None:
        self.count = count
        self.per = per
        self.hits: list[int | float] = []
    
    async def _clear_dead_keys(self) -> None:
        dead_t = time.time() - self.per
        for key in self.hits:
            if key <= dead_t:
                self.hits.remove(key)

    async def hit(self) -> tuple[bool, int]:
        await self._clear_dead_keys()
        self.hits.append(time.time())
        return len(self.hits) >= self.count, len(self.hits)
    
    async def is_limited(self) -> bool:
        return len(self.hits) >= self.count
    
    @property
    def reset_at(self):
        return 0

class RedisLimitBucket(BaseLimitBucket):
    """
    The redis bucket uses the "window" method.
    """

    __slots__ = ("key", "count", "per", "app", "reset")

    def __init__(self, app: MystbinApp, key: str, count: int, per: int) -> None:
        self.app = app
        self.key = key
        self.count = count
        self.per = per
        self.reset: Optional[int] = None
    
    async def _clear_dead_keys(self) -> None:
        pass # we don't actually need this, keys will be deleted on their own by redis

    async def hit(self) -> tuple[bool, int]:
        if not self.app.redis:
            raise NoRedisConnection()
        
        value: Optional[int] = await self.app.redis.get(self.key)        

        if value is None:
            val = await self.app.redis.incr(self.key)
            await self.app.redis.expire(self.key, self.per)
            self.reset = round(time.time()) + self.per
        
        else:
            val = await self.app.redis.incr(self.key)
                
        return val >= self.count, val
    
    async def is_limited(self) -> bool:
        if not self.app.redis:
            raise NoRedisConnection()
        
        t = await self.app.redis.get(self.key)
        return t >= self.count if t is not None else False
    
    @property
    def reset_at(self):
        return self.reset

_CT = Callable[..., Coroutine[Any, Any, Response]]

class Limiter:        
    def startup(self, app: MystbinApp) -> None:
        self.app = app
        self._keys: dict[str, BaseLimitBucket] = {}
        self._zone_cache: dict[str, tuple[int, int]] = {}
        self._endpoints: dict[str, Optional[str]] = {}

        stragegy = app.config["redis"]["use-redis"]
        if not stragegy:
            self.bucket_cls = InMemoryLimitBucket
        else:
            self.bucket_cls = RedisLimitBucket
    
    async def get_key(self, zone: str, request: Request) -> str:
        zone = await ratelimit_zone_key(zone, request)
        key = ratelimit_id_key(request)
        return f"{zone}%{key}"
    
    async def get_bucket(self, zone: str, key: str, request: Request) -> BaseLimitBucket:
        if key in self._keys:
            return self._keys[key]
        
        lims = self._zone_cache.get(zone)
        if not lims:
            lims = parse_ratelimit(await get_zone(zone, request))

        bucket = self.bucket_cls(self.app, key, lims[0], lims[1])
        self._keys[key] = bucket

        return bucket
    
    async def middleware(self, request: Request, call_next: _CT) -> Response:
        zone: Optional[str] = None

        for route in self.app.routes:
            match, _ = route.matches(request.scope)
            if match == Match.FULL and hasattr(route, "endpoint"):
                handler = route.endpoint # type: ignore
                zone = getattr(handler, "__zone__", None)

        if not await _ignores_ratelimits(request):
            key = await self.get_key("global", request)
            bucket = await self.get_bucket("global", key, request)

            is_limited, keys_used = await bucket.hit()
            headers = {
                "X-Global-Ratelimit-Used": str(keys_used),
                "X-Global-Ratelimit-Reset": str(bucket.reset_at),
                "X-Global-Ratelimit-Max": str(bucket.count),
                "X-Global-Ratelimit-Available": str(bucket.count - keys_used),
                "X-Ratelimit-Used": "0",
                "X-Ratelimit-Reset": "0",
                "X-Ratelimit-Max": "1",
                "X-Ratelimit-Available": "1"
            }

            if is_limited:
                return Response(status_code=429, headers=headers)
            
            if zone is not None:
                key = await self.get_key(zone, request)
                bucket = await self.get_bucket(zone, key, request)

                is_limited, keys_used = await bucket.hit()
                headers.update({
                    "X-Ratelimit-Used": str(keys_used),
                    "X-Ratelimit-Reset": str(bucket.reset_at),
                    "X-Ratelimit-Max": str(bucket.count),
                    "X-Ratelimit-Available": str(bucket.count - keys_used)
                })

                if is_limited:
                    return Response(status_code=429, headers=headers)
            
            resp = await call_next(request)
            resp.headers.update(headers)
            return resp
        
        else:
            headers = {
                "X-Global-Ratelimit-Used": "0",
                "X-Global-Ratelimit-Reset": "0",
                "X-Global-Ratelimit-Max": "1",
                "X-Global-Ratelimit-Available": "1",
                "X-Ratelimit-Used": "0",
                "X-Ratelimit-Reset": "0",
                "X-Ratelimit-Max": "1",
                "X-Ratelimit-Available": "1"
            }
            resp = await call_next(request)
            resp.headers.update(headers)
            return resp


def parse_ratelimit(limit: str) -> tuple[int, int]:
    _per, units = limit.split("/", 1)
    
    per: int = int(_per)
    transformed_units: int = time_units[units]
    return per, transformed_units

async def _fetch_user(request: Request):
    host = request.headers.get("X-Forwarded-For") or request.client.host

    auth = request.headers.get("Authorization", None)
    if not auth:
        query = "SELECT * FROM bans WHERE ip = $1"
        bans = await request.app.state.db._do_query(query, host)
        if bans:
            raise IPBanned
        return

    query = """
            SELECT users.*, bans.ip as _is_ip_banned , bans.userid as _is_user_banned
            FROM users
            FULL OUTER JOIN bans
            ON ip = $2
            OR userid = users.id
            WHERE token = $1;
            """

    user = await request.app.state.db._do_query(query, auth.replace("Bearer ", ""), host)
    if not user:
        return

    user = user[0]
    if user["_is_ip_banned"] or user["_is_user_banned"]:
        raise IPBanned

    request.state.user = user


async def _ignores_ratelimits(request: Request):
    if not hasattr(request.state, "user"):
        request.state.user = None
        await _fetch_user(request)

    if request.state.user and request.state.user["admin"]:
        return True

    return False

async def ratelimit_zone_key(zone: str, request: Request) -> str:
    _zone = zone

    if not hasattr(request.state, "user"):
        request.state.user = None
        await _fetch_user(request)

    user = request.state.user

    if user:
        _zone = ("authed_" if not user["subscriber"] else "premium_") + zone

    return _zone

async def get_zone(zone: str, request: Request) -> str:
    zone = await ratelimit_zone_key(zone, request)
    try:
        return request.app.config["ratelimits"][zone]
    except:
        return request.app.config["ratelimits"][zone.replace("authed_", "").replace("premium_", "")]

def ratelimit_id_key(request: Request) -> str:
    auth = request.headers.get("Authorization", None)
    if not auth:
        return request.headers.get("X-Forwarded-For", None) or request.client.host

    userid = tokens.get_user_id(auth.replace("Bearer ", ""))
    if not userid:  # must be a fake token, so just ignore it and go by ip
        return request.headers.get("X-Forwarded-For", None) or request.client.host

    return str(userid)

def limit(zone: Optional[str] = None):
    def wrapped(cb):
        cb.__zone__ = zone
        return cb
    
    return wrapped

limiter = Limiter()