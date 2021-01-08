"""
MIT License

Copyright (c) 2020 Laurent Savaete

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

This simply makes the keyfunc and is_exempt func async functions
"""

import asyncio
import datetime
import functools
import inspect
import itertools
import json
import logging
import sys
import time
import warnings
from email.utils import formatdate, parsedate_to_datetime
from functools import wraps
from typing import (
    Any,
    Coroutine,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    Iterator
)

import asyncpg
from limits import RateLimitItem, parse_many  # type: ignore
from limits.errors import ConfigurationError  # type: ignore
from limits.storage import Storage  # type: ignore
from limits.storage import MemoryStorage, storage_from_string
from limits.strategies import STRATEGIES, RateLimiter  # type: ignore
from starlette.applications import Starlette
from starlette.config import Config
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from slowapi.errors import RateLimitExceeded
from slowapi.util import get_ipaddr

import slowapi
from slowapi.extension import StrOrCallableStr
from . import tokens



class Limit(object):
    """
    simple wrapper to encapsulate limits and their context
    """

    def __init__(
        self,
        limit: RateLimitItem,
        key_func: Callable[..., str],
        scope: Optional[Union[str, Callable[..., str]]],
        per_method: bool,
        methods: Optional[List[str]],
        error_message: Optional[Union[str, Callable[..., str]]],
        exempt_when: Optional[Callable[..., Coroutine]],
        override_defaults: bool,
    ) -> None:
        self.limit = limit
        self.key_func = key_func
        self.__scope = scope
        self.per_method = per_method
        self.methods = methods
        self.error_message = error_message
        self.exempt_when = exempt_when
        self.override_defaults = override_defaults

    async def is_exempt(self, request) -> bool:
        """
        Check if the limit is exempt.
        Return True to exempt the route from the limit.
        """
        return await self.exempt_when(request) if self.exempt_when is not None else False

    @property
    def scope(self) -> str:
        # flack.request.endpoint is the name of the function for the endpoint
        # FIXME: how to get the request here?
        if self.__scope is None:
            return ""
        else:
            return (
                self.__scope(request.endpoint)  # noqa
                if callable(self.__scope)
                else self.__scope
            )

class LimitGroup(object):
    """
    represents a group of related limits either from a string or a callable that returns one
    """

    def __init__(
        self,
        limit_provider: Union[str, Callable[..., str]],
        key_function: Callable[..., str],
        scope: Optional[Union[str, Callable[..., str]]],
        per_method: bool,
        methods: Optional[List[str]],
        error_message: Optional[Union[str, Callable[..., str]]],
        exempt_when: Optional[Callable[..., bool]],
        override_defaults: bool,
    ):
        self.__limit_provider = limit_provider
        self.__scope = scope
        self.key_function = key_function
        self.per_method = per_method
        self.methods = methods and [m.lower() for m in methods] or methods
        self.error_message = error_message
        self.exempt_when = exempt_when
        self.override_defaults = override_defaults

    async def iterate(self, request: Request) -> Iterator[Limit]:
        limit_items: List[RateLimitItem] = parse_many(
            await self.__limit_provider(request)
            if inspect.iscoroutinefunction(self.__limit_provider)
            else self.__limit_provider
        )
        for lmt in limit_items:
            yield Limit(
                lmt,
                self.key_function,
                self.__scope,
                self.per_method,
                self.methods,
                self.error_message,
                self.exempt_when,
                self.override_defaults,
            )

    def __iter__(self):
        raise ValueError("aaaaaa")


class Limiter(slowapi.Limiter):
    async def __evaluate_limits(
        self, request: Request, endpoint: str, limits: List[Limit]
    ) -> None:
        failed_limit = None
        limit_for_header = None
        for lim in limits:
            limit_scope = lim.scope or endpoint
            if await lim.is_exempt(request):
                continue
            if lim.methods is not None and request.method.lower() not in lim.methods:
                continue
            if lim.per_method:
                limit_scope += ":%s" % request.method

            if "request" in inspect.signature(lim.key_func).parameters.keys():
                limit_key = await lim.key_func(request)
            else:
                limit_key = await lim.key_func()

            args = [limit_key, limit_scope]
            if all(args):
                if self._key_prefix:
                    args = [self._key_prefix] + args
                if not limit_for_header or lim.limit < limit_for_header[0]:
                    limit_for_header = (lim.limit, args)
                if not self.limiter.hit(lim.limit, *args):
                    self.logger.warning(
                        "ratelimit %s (%s) exceeded at endpoint: %s",
                        lim.limit,
                        limit_key,
                        limit_scope,
                    )
                    failed_limit = lim
                    limit_for_header = (lim.limit, args)
                    break
            else:
                self.logger.error(
                    "Skipping limit: %s. Empty value found in parameters.", lim.limit
                )
                continue
        # keep track of which limit was hit, to be picked up for the response header
        request.state.view_rate_limit = limit_for_header

        if failed_limit:
            raise RateLimitExceeded(failed_limit)

    async def _check_request_limit(
        self,
        request: Request,
        endpoint_func: Callable[..., Any],
        in_middleware: bool = True,
    ) -> None:
        """
        Determine if the request is within limits
        """
        endpoint = request["path"] or ""
        # view_func = current_app.view_functions.get(endpoint, None)
        view_func = endpoint_func

        name = "%s.%s" % (view_func.__module__, view_func.__name__) if view_func else ""
        # cases where we don't need to check the limits
        if (
            not endpoint
            or not self.enabled
            # or we are sending a static file
            # or view_func == current_app.send_static_file
            or name in self._exempt_routes
            or any(fn() for fn in self._request_filters)
        ):
            return
        limits: List[Limit] = []
        dynamic_limits: List[Limit] = []

        if not in_middleware:
            limits = self._route_limits[name] if name in self._route_limits else []
            dynamic_limits = []
            if name in self._dynamic_route_limits:
                for lim in self._dynamic_route_limits[name]:
                    try:
                        l = []
                        async for x in lim.iterate(request):
                            l.append(x)
                        dynamic_limits.extend(l)
                    except ValueError as e:
                        self.logger.error(
                            "failed to load ratelimit for view function %s (%s)",
                            name,
                            e,
                        )

        try:
            all_limits: List[Limit] = []
            if self._storage_dead and self._fallback_limiter:
                if in_middleware and name in self.__marked_for_limiting:
                    pass
                else:
                    if self.__should_check_backend() and self._storage.check():
                        self.logger.info("Rate limit storage recovered")
                        self._storage_dead = False
                        self.__check_backend_count = 0
                    else:
                        all_limits = list(itertools.chain(*self._in_memory_fallback))
            if not all_limits:
                route_limits: List[Limit] = limits + dynamic_limits
                all_limits = (
                    list(itertools.chain(*self._application_limits))
                    if in_middleware
                    else []
                )
                all_limits += route_limits
                combined_defaults = all(
                    not limit.override_defaults for limit in route_limits
                )
                if (
                    not route_limits
                    and not (in_middleware and name in self.__marked_for_limiting)
                    or combined_defaults
                ):
                    all_limits += list(itertools.chain(*self._default_limits))
            # actually check the limits, so far we've only computed the list of limits to check
            await self.__evaluate_limits(request, endpoint, all_limits)
        except Exception as e:  # no qa
            if isinstance(e, RateLimitExceeded):
                raise
            if self._in_memory_fallback_enabled and not self._storage_dead:
                self.logger.warn(
                    "Rate limit storage unreachable - falling back to"
                    " in-memory storage"
                )
                self._storage_dead = True
                await self._check_request_limit(request, endpoint_func, in_middleware)
            else:
                if self._swallow_errors:
                    self.logger.exception("Failed to rate limit. Swallowing error")
                else:
                    raise

    def __limit_decorator(
        self,
        limit_value: StrOrCallableStr,
        key_func: Optional[Callable[..., str]] = None,
        shared: bool = False,
        scope: Optional[StrOrCallableStr] = None,
        per_method: bool = False,
        methods: Optional[List[str]] = None,
        error_message: Optional[str] = None,
        exempt_when: Optional[Callable[..., bool]] = None,
        override_defaults: bool = True,
    ) -> Callable[..., Any]:

        _scope = scope if shared else None

        def decorator(func: Callable[..., Response]) -> Callable[..., Response]:
            keyfunc = key_func or self._key_func
            name = f"{func.__module__}.{func.__name__}"
            dynamic_limit = None
            static_limits: List[Limit] = []
            if callable(limit_value):
                dynamic_limit = LimitGroup(
                    limit_value,
                    keyfunc,
                    _scope,
                    per_method,
                    methods,
                    error_message,
                    exempt_when,
                    override_defaults,
                )
            else:
                try:
                    static_limits = list(
                        LimitGroup(
                            limit_value,
                            keyfunc,
                            _scope,
                            per_method,
                            methods,
                            error_message,
                            exempt_when,
                            override_defaults,
                        )
                    )
                except ValueError as e:
                    self.logger.error(
                        "Failed to configure throttling for %s (%s)", name, e,
                    )
            self.__marked_for_limiting.setdefault(name, []).append(func)
            if dynamic_limit:
                self._dynamic_route_limits.setdefault(name, []).append(dynamic_limit)
            else:
                self._route_limits.setdefault(name, []).extend(static_limits)

            connection_type: Optional[str] = None
            sig = inspect.signature(func)
            for idx, parameter in enumerate(sig.parameters.values()):
                if parameter.name == "request" or parameter.name == "websocket":
                    connection_type = parameter.name
                    break
            else:
                raise Exception(
                    f'No "request" or "websocket" argument on function "{func}"'
                )

            if asyncio.iscoroutinefunction(func):
                # Handle async request/response functions.
                @functools.wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Response:
                    # get the request object from the decorated endpoint function
                    request = kwargs.get("request", args[idx] if args else None)
                    if not isinstance(request, Request):
                        raise Exception(
                            "parameter `request` must be an instance of starlette.requests.Request"
                        )

                    if self._auto_check and not getattr(
                        request.state, "_rate_limiting_complete", False
                    ):
                        await self._check_request_limit(request, func, False)
                        request.state._rate_limiting_complete = True
                    response = await func(*args, **kwargs)  # type: ignore
                    if not isinstance(response, Response):
                        # get the response object from the decorated endpoint function
                        self._inject_headers(
                            kwargs.get("response"), request.state.view_rate_limit  # type: ignore
                        )
                    else:
                        self._inject_headers(response, request.state.view_rate_limit)
                    return response

                return async_wrapper

            else:
                raise ValueError("Don't make sync callbacks")

        return decorator


async def ratelimit_key(request: Request) -> str:
    auth = request.headers.get("Authorization", None)
    if not auth:
        return request.headers.get("X-Forwarded-For", None) or request.client.host

    userid = tokens.get_user_id(auth)
    if not userid:  # must be a fake token, so just ignore it and go by ip
        return request.headers.get("X-Forwarded-For", None) or request.client.host

    return str(userid)

async def _ignores_ratelimits(request: Request):
    if not hasattr(request.state, "user"):
        request.state.user = None

        auth = request.headers.get("Authorization", None)
        if not auth:
            return False

        user = await request.app.state.db.get_user(token=auth)
        if not isinstance(user, asyncpg.Record):
            return False

        request.state.user = user

    if request.state.user and request.state.user['admin']:
        return True

    return False

def limit(t, scope=None):
    async def _limit_key(request: Request) -> str:
        _t = t

        if not hasattr(request.state, "user"):
            request.state.user = user = None

            auth = request.headers.get("Authorization", None)
            if auth:
                user = await request.app.state.db.get_user(token=auth)
                if isinstance(user, asyncpg.Record):
                    request.state.user = user
                else:
                    user = None
        else:
            user = request.state.user

        if user:
            _t = ("authed_" if not user['subscriber'] else "subscriber_") + _t

        try:
            return request.app.config['ratelimits'][_t]
        except KeyError:
            return request.app.config['ratelimits'][t]

    if scope:
        return global_limiter.shared_limit(_limit_key, scope=scope, key_func=ratelimit_key, exempt_when=_ignores_ratelimits) # noqa
    return global_limiter.limit(_limit_key, key_func=ratelimit_key, exempt_when=_ignores_ratelimits) # noqa

global_limiter = Limiter(ratelimit_key, headers_enabled=True, in_memory_fallback_enabled=True)