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

import asyncio
import logging

import aiohttp
import starlette_plus
import uvicorn

from src import core

starlette_plus.setup_logging(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

__all__ = ()


async def main() -> None:
    async with (
        aiohttp.ClientSession() as session,
        core.Database(
            dsn=core.CONFIG["DATABASE"]["dsn"], session=session, github_config=core.CONFIG.get("GITHUB")
        ) as database,
    ):
        app: core.Application = core.Application(database=database)

        host: str = core.CONFIG["SERVER"]["host"]
        port: int = core.CONFIG["SERVER"]["port"]

        config: uvicorn.Config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            access_log=False,
            forwarded_allow_ips="*",
        )
        server: uvicorn.Server = uvicorn.Server(config)

        await server.serve()


try:
    asyncio.run(main())
except KeyboardInterrupt:
    LOGGER.info("Closing the MystBin application due to KeyboardInterrupt.")
