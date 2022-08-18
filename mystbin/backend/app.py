"""Copyright(C) 2020 PythonistaGuild

This file is part of MystBin.

MystBin is free software: you can redistribute it and / or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

MystBin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY
without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with MystBin.  If not, see <https://www.gnu.org/licenses/>.
"""
import asyncio
import datetime
import pathlib
from typing import Any, Callable, Coroutine, Dict, Optional, Tuple

import aiohttp
import aioredis
import sentry_sdk
import ujson
from fastapi import FastAPI, Response
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from mystbin_models import MystbinRequest, MystbinState
from routers import admin, apps, pastes, user
from utils import cli as _cli, ratelimits
from utils.db import Database


METHODS: Tuple[str, ...] = ("DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT")


class MystbinApp(FastAPI):
    """Subclassed API for Mystbin."""

    redis: Optional[aioredis.Redis]
    cli: Optional[_cli.CLIHandler] = None
    state: MystbinState

    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None, config: Optional[pathlib.Path] = None):
        self.loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop_policy().get_event_loop()
        super().__init__(
            title="MystBin",
            version="3.0.0",
            description="MystBin backend server",
            loop=self.loop,
            redoc_url="/docs",
            docs_url=None,
        )

        if not config:
            config = pathlib.Path("config.json")
            if not config.exists():
                config = pathlib.Path("../../config.json")

        with open(config) as f:
            self.config: Dict[str, Dict[str, Any]] = ujson.load(f)
        self.should_close = False
        self.add_middleware(BaseHTTPMiddleware, dispatch=self.request_stats)
        self.add_event_handler("startup", func=self.app_startup)

    async def cors_middleware(
        self,
        request: MystbinRequest,
        call_next: Callable[[MystbinRequest], Coroutine[Any, Any, Response]],
    ):
        headers = {
            "Access-Control-Allow-Headers": request.headers.get("Access-Control-Request-Headers", ""),
            "Access-Control-Allow-Methods": ", ".join(METHODS),
            "Access-Control-Allow-Origin": self.config["site"]["frontend_site"],
            "Access-Control-Max-Age": "600",
            "Vary": "Origin",
        }

        if request.method == "OPTIONS":
            return Response(headers=headers)

        resp = await call_next(request)
        resp.headers.update(headers)
        return resp

    async def request_stats(self, request: MystbinRequest, call_next):
        request.app.state.request_stats["total"] += 1

        if request.url.path != "/admin/stats":
            request.app.state.request_stats["latest"] = datetime.datetime.utcnow()

        response = await call_next(request)
        return response

    async def app_startup(self):
        """Async app startup."""
        self.state.db = await Database(self.config).__ainit__()
        self.state.client = aiohttp.ClientSession()
        self.state.request_stats = {"total": 0, "latest": datetime.datetime.utcnow()}
        self.state.webhook_url = self.config["sentry"].get("discord_webhook", None)

        if self.config["redis"]["use-redis"]:
            self.redis = aioredis.Redis(
                host=self.config["redis"]["host"],
                port=self.config["redis"]["port"],
                username=self.config["redis"]["user"],
                password=self.config["redis"]["password"],
                db=self.config["redis"]["db"],
            )

        ratelimits.limiter.startup(self)
        self.middleware("http")(ratelimits.limiter.middleware)
        self.middleware("http")(self.cors_middleware)

        nocli = pathlib.Path(".nocli")
        if nocli.exists():
            return

        print()

        self.cli = _cli.CLIHandler(self.state.db)
        self.loop.create_task(self.cli.parse_cli())


app = MystbinApp()

app.include_router(admin.router)
app.include_router(apps.router)
app.include_router(pastes.router)
app.include_router(user.router)


try:
    sentry_dsn = app.config["sentry"]["dsn"]
except KeyError:
    pass
else:
    traces_sample_rate = app.config["sentry"].get("traces_sample_rate", 0.3)
    sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=traces_sample_rate, attach_stacktrace=True)

    app.add_middleware(SentryAsgiMiddleware)

# app.add_middleware(PrometheusMiddleware)
# app.add_route("/metrics/", metrics)
