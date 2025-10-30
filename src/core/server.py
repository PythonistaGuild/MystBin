"""MystBin. Share code easily.

Copyright (C) 2020-Current PythonistaGuild

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import logging
import pathlib

import aiohttp
import starlette_plus
from starlette.middleware import Middleware
from starlette.routing import Mount, Route
from starlette.schemas import SchemaGenerator
from starlette.staticfiles import StaticFiles

from src.views import APIView, DocsView, HTMXView

from .config import CONFIG
from .database import Database

LOGGER = logging.getLogger(__name__)
STATIC_DIR = pathlib.Path(__file__).parent.parent / "web" / "static"


__all__ = ()


class Application(starlette_plus.Application):
    def __init__(self, *, database: Database, session: aiohttp.ClientSession | None = None) -> None:
        self.database: Database = database
        self.session: aiohttp.ClientSession | None = session
        self.schemas: SchemaGenerator | None = None

        views: list[starlette_plus.View] = [
            HTMXView(self),
            APIView(self),
            DocsView(self),
        ]
        routes: list[Mount | Route] = [Mount("/static", app=StaticFiles(directory=STATIC_DIR), name="static")]

        if redis_key := CONFIG.get("REDIS"):
            limit_url = redis_key["limiter"]
            session_url = redis_key["sessions"]
        else:
            limit_url = None
            session_url = None

        limit_redis = starlette_plus.Redis(url=limit_url)
        sess_redis = starlette_plus.Redis(url=session_url)

        global_limits = [CONFIG["LIMITS"]["global_limit"]]
        middleware = [
            Middleware(
                starlette_plus.middleware.RatelimitMiddleware,
                ignore_localhost=True,
                redis=limit_redis,
                global_limits=global_limits,
            ),
            Middleware(
                starlette_plus.middleware.SessionMiddleware,
                secret=CONFIG["SERVER"]["session_secret"],
                redis=sess_redis,
                max_age=86400,
            ),
        ]

        if CONFIG["SERVER"]["maintenance"]:
            # inject a catch all before any route...
            routes.extend((
                Route("/", self.maint_mode, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]),
                Route("/{path:path}", self.maint_mode, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]),
            ))

        super().__init__(on_startup=[self.event_ready], views=views, routes=routes, middleware=middleware)

    @staticmethod
    async def maint_mode(_: starlette_plus.Request) -> starlette_plus.Response:
        return starlette_plus.FileResponse("web/maint.html")

    @starlette_plus.route("/docs")
    @starlette_plus.route("/documentation")
    async def documentation_redirect(self, _: starlette_plus.Request) -> starlette_plus.Response:  # noqa: PLR6301 # must be a bound method for decoration
        return starlette_plus.RedirectResponse("/api/documentation")

    @starlette_plus.route("/documents", methods=["POST"])
    @starlette_plus.route("/api/documents", methods=["POST"])
    async def documents_redirect(self, _: starlette_plus.Request) -> starlette_plus.Response:  # noqa: PLR6301 # must be a bound method for decoration
        # Compat redirect route...
        return starlette_plus.RedirectResponse("/api/paste", status_code=308)

    async def event_ready(self) -> None:
        self.schemas = SchemaGenerator({
            "openapi": "3.1.0",
            "info": {
                "title": "MystBin API",
                "version": "4.0",
                "summary": "API Documentation",
                "description": "MystBin - Easily share code and text.",
            },
        })
        LOGGER.info("MystBin application has successfully started!")
