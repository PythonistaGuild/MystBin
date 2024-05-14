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
import datetime
import logging
from typing import TYPE_CHECKING, Any, Self

import asyncpg

from core import CONFIG

from . import utils
from .models import FileModel, PasteModel


if TYPE_CHECKING:
    _Pool = asyncpg.Pool[asyncpg.Record]
else:
    _Pool = asyncpg.Pool


logger: logging.Logger = logging.getLogger(__name__)


class Database:
    pool: _Pool

    def __init__(self, *, dsn: str) -> None:
        self._dsn: str = dsn

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def connect(self) -> None:
        try:
            pool: asyncpg.Pool[asyncpg.Record] | None = await asyncpg.create_pool(dsn=self._dsn)
        except Exception as e:
            raise RuntimeError from e

        if not pool:
            raise RuntimeError("Failed to connect to the database... No additional information.")

        with open("schema.sql") as fp:
            await pool.execute(fp.read())

        self.pool = pool
        logger.info("Successfully connected to the database.")

    async def close(self) -> None:
        try:
            await asyncio.wait_for(self.pool.close(), timeout=10)
        except TimeoutError:
            logger.warning("Failed to greacefully close the database connection...")
        else:
            logger.info("Successfully closed the database connection.")

    async def fetch_paste(self, identifier: str, *, password: str | None) -> PasteModel | None:
        assert self.pool

        paste_query: str = """
            UPDATE pastes SET views = views + 1 WHERE id = $1
            RETURNING *,
            CASE WHEN password IS NOT NULL THEN true
            ELSE false END AS has_password,
            CASE WHEN password = CRYPT($2, password) THEN true
            ELSE false END AS password_ok
        """

        file_query: str = """
            SELECT * FROM files WHERE parent_id = $1
        """

        async with self.pool.acquire() as connection:
            record: asyncpg.Record | None = await connection.fetchrow(paste_query, identifier, password)

            if not record:
                return

            paste: PasteModel = PasteModel(record)
            if paste.expires and paste.expires <= datetime.datetime.now(tz=datetime.timezone.utc):
                await connection.execute("DELETE FROM pastes WHERE id = $1", identifier)
                return

            if paste.has_password and not paste.password_ok:
                return paste

            records: list[asyncpg.Record] = await connection.fetch(file_query, identifier)
            paste.files = [FileModel(d) for d in records]

        return paste

    async def create_paste(self, *, data: dict[str, Any]) -> PasteModel:
        assert self.pool

        paste_query: str = """
            INSERT INTO pastes (id, expires, password, safety)
            VALUES ($1, $2, (SELECT crypt($3, gen_salt('bf')) WHERE $3 is not null), $4)
            RETURNING *
        """

        file_query: str = """
            INSERT INTO files (parent_id, content, filename, loc, annotation)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """

        files: list[dict[str, Any]] = data["files"]
        expiry: str | None = data["expires"]
        password: str | None = data["password"]

        async with self.pool.acquire() as connection:
            while True:
                identifier: str = utils.generate_id()
                safety: str = utils.generate_safety_token()

                try:
                    paster: asyncpg.Record | None = await connection.fetchrow(
                        paste_query,
                        identifier,
                        expiry,
                        password,
                        safety,
                    )
                except asyncpg.exceptions.UniqueViolationError:
                    continue
                else:
                    break

            assert paster

            paste: PasteModel = PasteModel(paster)
            async with connection.transaction():
                for index, file in enumerate(files, 1):
                    name: str = (file.get("filename") or f"file_{index}")[-CONFIG["PASTES"]["name_limit"] :]
                    name = "_".join(name.splitlines())

                    content: str = file["content"]
                    loc: int = file["content"].count("\n") + 1
                    annotation: str = ""

                    tokens = [t for t in utils.TOKEN_REGEX.findall(content) if utils.validate_discord_token(t)]
                    if tokens:
                        annotation = "Contains possibly sensitive information: Discord Token(s)"

                    row: asyncpg.Record | None = await connection.fetchrow(
                        file_query, paste.id, content, name, loc, annotation
                    )

                    if row:
                        paste.files.append(FileModel(row))

            return paste

    async def fetch_paste_security(self, *, token: str) -> PasteModel | None:
        query: str = """SELECT * FROM pastes WHERE safety = $1"""

        async with self.pool.acquire() as connection:
            record: asyncpg.Record | None = await connection.fetchrow(query, token)
            if not record:
                return

        paste: PasteModel = PasteModel(record=record)
        if paste.expires and paste.expires <= datetime.datetime.now(tz=datetime.timezone.utc):
            await connection.execute("DELETE FROM pastes WHERE id = $1", token)
            return

        return paste

    async def delete_paste_security(self, *, token: str) -> None:
        query: str = """DELETE FROM pastes WHERE safety = $1"""

        async with self.pool.acquire() as connection:
            await connection.execute(query, token)
