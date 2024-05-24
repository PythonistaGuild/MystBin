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

from __future__ import annotations

import asyncio
import datetime
import logging
from typing import TYPE_CHECKING, Any, Self

import aiohttp
import asyncpg

from core import CONFIG

from . import utils
from .models import FileModel, PasteModel
from .scanners import SecurityInfo, Services


if TYPE_CHECKING:
    _Pool = asyncpg.Pool[asyncpg.Record]
    from types_.config import Github
    from types_.github import PostGist
    from types_.scanner import ScannerSecret
else:
    _Pool = asyncpg.Pool


LOGGER: logging.Logger = logging.getLogger(__name__)


class Database:
    pool: _Pool

    def __init__(self, *, dsn: str, session: aiohttp.ClientSession | None = None, github_config: Github | None) -> None:
        self._dsn: str = dsn
        self.session: aiohttp.ClientSession | None = session
        self._handling_tokens = bool(self.session and github_config)

        if self._handling_tokens:
            LOGGER.info("Setup to handle Discord Tokens.")
            assert github_config  # guarded by if here

            self._gist_token = github_config["token"]
            self._gist_timeout = github_config["timeout"]
            # tokens bucket for gist posting: {paste_id: token\ntoken}
            self.__tokens_bucket: dict[str, str] = {}
            self.__token_lock = asyncio.Lock()
            self.__token_task = asyncio.create_task(self._token_task())

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *_: Any) -> None:
        task: asyncio.Task[None] | None = getattr(self, "__token_task", None)
        if task:
            task.cancel()

        await self.close()

    async def _token_task(self) -> None:
        # won't run unless pre-reqs are met in __init__
        while True:
            if self.__tokens_bucket:
                async with self.__token_lock:
                    await self._post_gist_of_tokens()

            await asyncio.sleep(self._gist_timeout)

    def _handle_discord_tokens(self, tokens: list[str], paste_id: str) -> None:
        if not tokens:
            return

        LOGGER.info(
            "Discord bot token located and added to token bucket. Current bucket size is: %s", len(self.__tokens_bucket)
        )

        self.__tokens_bucket[paste_id] = "\n".join(tokens)

    async def _post_gist_of_tokens(self) -> None:
        assert self.session  # guarded in caller
        json_payload: PostGist = {
            "description": "MystBin found these Discord tokens in a public paste, and posted them here to invalidate them. If you intended to share these, please apply a password to the paste.",
            "files": {},
            "public": True,
        }

        github_headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._gist_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        current_tokens = self.__tokens_bucket
        self.__tokens_bucket = {}

        for paste_id, tokens in current_tokens.items():
            filename = str(datetime.datetime.now(datetime.UTC)) + "-tokens.txt"
            json_payload["files"][filename] = {"content": f"https://mystb.in/{paste_id}:\n{tokens}"}

        success = False

        try:
            async with self.session.post(
                "https://api.github.com/gists", headers=github_headers, json=json_payload
            ) as resp:
                success = resp.ok

                if not success:
                    response_body = await resp.text()
                    LOGGER.error(
                        "Failed to create gist with token bucket with response status code %s and response body:\n\n%s",
                        resp.status,
                        response_body,
                    )
        except (aiohttp.ClientError, aiohttp.ClientOSError) as error:
            success = False
            LOGGER.error("Failed to handle gist creation due to a client or operating system error", exc_info=error)

        if success:
            LOGGER.info("Gist created and invalidated tokens from %s pastes.", len(current_tokens))
        else:
            self.__tokens_bucket.update(current_tokens)

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
        LOGGER.info("Successfully connected to the database.")

    async def close(self) -> None:
        try:
            await asyncio.wait_for(self.pool.close(), timeout=10)
        except TimeoutError:
            LOGGER.warning("Failed to greacefully close the database connection...")
        else:
            LOGGER.info("Successfully closed the database connection.")

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
            INSERT INTO files (parent_id, content, filename, loc, annotation, warning_positions)
            VALUES ($1, $2, $3, $4, $5, $6)
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

                    # Normalise newlines...
                    content: str = file["content"].replace("\r\n", "\n").replace("\r", "\n")
                    loc: int = file["content"].count("\n") + 1

                    positions: list[int] = []
                    extra: str = ""

                    secrets: list[ScannerSecret] = SecurityInfo.scan_file(content)
                    for payload in secrets:
                        service: Services = payload["service"]

                        extra += f"{service.value}, "
                        positions += [t[0] for t in payload["tokens"]]

                        if not password and self._handling_tokens and service is Services.discord:
                            self._handle_discord_tokens(tokens=[t[1] for t in payload["tokens"]], paste_id=paste.id)

                    extra = extra.removesuffix(", ")
                    annotation = f"Contains possibly sensitive data from: {extra}" if extra else ""

                    row: asyncpg.Record | None = await connection.fetchrow(
                        file_query,
                        paste.id,
                        content,
                        name,
                        loc,
                        annotation,
                        sorted(positions),
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
