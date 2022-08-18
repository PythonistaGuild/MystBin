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
import os
import sys
from typing import Any, Callable, Coroutine, Dict, Optional

import aiohttp
import aioredis
import sentry_sdk
import ujson
from fastapi import FastAPI, Request, Response
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette_prometheus import metrics, PrometheusMiddleware

from routers import admin, apps, pastes, user
from utils import ratelimits, cli as _cli
from utils.db import Database


class MystbinApp(FastAPI):
    """Subclassed API for Mystbin."""

    redis: Optional[aioredis.Redis]
    cli: Optional[_cli.CLIHandler] = None

    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None, config: Optional[pathlib.Path] = None):
        self.loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop_policy().get_event_loop()

        if not config:
            config = pathlib.Path("config.json")
            if not config.exists():
                config = pathlib.Path("../../config.json")
            
        with open(config) as f:
            self.config: Dict[str, Dict[str, Any]] = ujson.load(f)

        super().__init__(
            title="MystBin",
            version="3.0.0",
            description="MystBin backend server",
            loop=self.loop,
            redoc_url="/docs",
            docs_url=None,
        )
        self.should_close = False


app = MystbinApp()
METHODS = ("DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT")


@app.middleware("http")
async def request_stats(request: Request, call_next):
    if request.method == "OPTIONS":
        raise RuntimeError("blah")
        return Response(headers={
            "Access-Control-Allowed-Headers": request.headers.get("Access-Control-Request-Headers", ""),
            "Access-Control-Allowed-Method": ", ".join(METHODS),
            "Access-Control-Allowed-Origin": app.config["site"]["frontend_site"],
            "Access-Control-Max-Age": "600",
            "Vary": "Origin",
        })
    request.app.state.request_stats["total"] += 1

    if request.url.path != "/admin/stats":
        request.app.state.request_stats["latest"] = datetime.datetime.utcnow()

    response = await call_next(request)
    return response

async def cors_middleware(request: Request, call_next: Callable[[Request], Coroutine[Any, Any, Response]]):
    headers={
        "Access-Control-Allow-Headers": request.headers.get("Access-Control-Request-Headers", ""),
        "Access-Control-Allow-Methods": ", ".join(METHODS),
        "Access-Control-Allow-Origin": app.config["site"]["frontend_site"],
        "Access-Control-Max-Age": "600",
        "Vary": "Origin",
    }
    
    if request.method == "OPTIONS":
        return Response(headers=headers)
    
    resp = await call_next(request)
    resp.headers.update(headers)
    return resp


@app.on_event("startup")
async def app_startup():
    """Async app startup."""
    app.state.db = await Database(app.config).__ainit__()
    app.state.client = aiohttp.ClientSession()
    app.state.request_stats = {"total": 0, "latest": datetime.datetime.utcnow()}
    app.state.webhook_url = app.config["sentry"].get("discord_webhook", None)

    if app.config["redis"]["use-redis"]:
        app.redis = aioredis.Redis(
            host=app.config["redis"]["host"],
            port=app.config["redis"]["port"],
            username=app.config["redis"]["user"],
            password=app.config["redis"]["password"],
            db=app.config["redis"]["db"]
        )
    
    ratelimits.limiter.startup(app)
    app.middleware("http")(ratelimits.limiter.middleware)
    app.middleware("http")(cors_middleware)

    nocli = pathlib.Path(".nocli")
    if nocli.exists():
        return
    
    print()

    app.cli = _cli.CLIHandler(app.state.db)
    app.loop.create_task(app.cli.parse_cli())


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

#app.add_middleware(PrometheusMiddleware)
#app.add_route("/metrics/", metrics)
