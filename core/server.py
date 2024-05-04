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

import starlette_plus
from starlette.middleware import Middleware
from starlette.staticfiles import StaticFiles

from core.database import Database
from views import *

from .config import CONFIG


logger: logging.Logger = logging.getLogger(__name__)


class Application(starlette_plus.Application):
    def __init__(self, *, database: Database) -> None:
        self.database: Database = database

        views: list[starlette_plus.View] = [HTMXView(self), APIView(self)]
        routes = [starlette_plus.Mount("/static", app=StaticFiles(directory="web/static"), name="static")]

        limit_redis = starlette_plus.Redis(url=CONFIG["REDIS"]["limiter"]) if CONFIG["REDIS"]["limiter"] else None
        # sess_redis = starlette_plus.Redis(url=CONFIG["REDIS"]["sessions"]) if CONFIG["REDIS"]["sessions"] else None

        global_limits = [CONFIG["LIMITS"]["global_limit"]]
        middleware = [
            Middleware(
                starlette_plus.middleware.RatelimitMiddleware,
                ignore_localhost=True,
                redis=limit_redis,
                global_limits=global_limits,
            )
        ]

        super().__init__(on_startup=[self.event_ready], views=views, routes=routes, middleware=middleware)

    async def event_ready(self) -> None:
        logger.info("MystBin application has successfully started!")
