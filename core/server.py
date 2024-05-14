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

import aiohttp
import starlette_plus
from starlette.middleware import Middleware
from starlette.routing import Mount, Route
from starlette.schemas import SchemaGenerator
from starlette.staticfiles import StaticFiles

from core.database import Database
from views import *

from .config import CONFIG


logger: logging.Logger = logging.getLogger(__name__)


class Application(starlette_plus.Application):
    def __init__(self, *, database: Database, session: aiohttp.ClientSession | None = None) -> None:
        self.database: Database = database
        self.session: aiohttp.ClientSession | None = session
        self.schemas: SchemaGenerator | None = None

        views: list[starlette_plus.View] = [
            HTMXView(self),
            APIView(self, github_config=CONFIG.get("GITHUB")),
            DocsView(self),
        ]
        routes: list[Mount | Route] = [Mount("/static", app=StaticFiles(directory="web/static"), name="static")]

        limit_redis = starlette_plus.Redis(url=CONFIG["REDIS"]["limiter"]) if CONFIG["REDIS"]["limiter"] else None
        sess_redis = starlette_plus.Redis(url=CONFIG["REDIS"]["sessions"]) if CONFIG["REDIS"]["sessions"] else None

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
            routes.append(Route("/", self.maint_mode, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]))
            routes.append(
                Route("/{path:path}", self.maint_mode, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
            )

        super().__init__(on_startup=[self.event_ready], views=views, routes=routes, middleware=middleware)

    @staticmethod
    async def maint_mode(request: starlette_plus.Request) -> starlette_plus.Response:
        return starlette_plus.FileResponse("web/maint.html")

    @starlette_plus.route("/docs")
    @starlette_plus.route("/documentation")
    async def documentation_redirect(self, request: starlette_plus.Request) -> starlette_plus.Response:
        return starlette_plus.RedirectResponse("/api/documentation")

    @starlette_plus.route("/documents", methods=["POST"])
    @starlette_plus.route("/api/documents", methods=["POST"])
    async def documents_redirect(self, request: starlette_plus.Request) -> starlette_plus.Response:
        # Compat redirect route...
        return starlette_plus.RedirectResponse("/api/paste", status_code=308)

    async def event_ready(self) -> None:
        self.schemas = SchemaGenerator(
            {
                "openapi": "3.1.0",
                "info": {
                    "title": "MystBin API",
                    "version": "4.0",
                    "summary": "API Documentation",
                    "description": "MystBin - Easily share code and text.",
                },
            }
        )
        logger.info("MystBin application has successfully started!")
