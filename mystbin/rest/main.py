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
from typing import Any, Dict

import aiohttp
import sentry_sdk
import slowapi
import toml
from fastapi import FastAPI, Request
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from routers import admin, apps, pastes, user
from utils import ratelimits
from utils.db import Database


class MystbinApp(FastAPI):
    """Subclassed API for Mystbin."""

    def __init__(self, *, loop: asyncio.AbstractEventLoop = None):
        loop = loop or asyncio.get_event_loop()
        self.config: Dict[str, Dict[str, Any]] = toml.load(pathlib.Path("config.toml"))
        super().__init__(
            title="MystBin",
            version="3.0.0",
            description="MystBin backend server",
            loop=loop,
        )
        self.state.limiter = ratelimits.global_limiter
        self.add_exception_handler(
            ratelimits.RateLimitExceeded, slowapi._rate_limit_exceeded_handler
        )


app = MystbinApp()


@app.middleware("http")
async def request_stats(request: Request, call_next):
    request.app.state.request_stats["total"] += 1
    request.app.state.request_stats["latest"] = datetime.datetime.utcnow()

    response = await call_next(request)
    return response


@app.on_event("startup")
async def app_startup():
    """ Async app startup. """
    app.state.db = await Database(app).__ainit__()
    app.state.client = aiohttp.ClientSession()
    app.state.request_stats = {"total": 0, "latest": None}


app.include_router(admin.router)
app.include_router(apps.router)
app.include_router(pastes.router)
app.include_router(user.router)


sentry_dsn = app.config['sentry']['dsn']

if sentry_dsn:
    sentry_sdk.init(dsn=sentry_dsn,  traces_sample_rate=app.config['sentry']['dsn'], attach_stacktrace=True)
    app.add_middleware(SentryAsgiMiddleware)
