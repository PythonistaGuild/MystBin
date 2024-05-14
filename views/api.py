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
import json
import logging
import re
from typing import TYPE_CHECKING, Any

import aiohttp
import starlette_plus

from core import CONFIG
from core.utils import validate_paste


if TYPE_CHECKING:
    from core import Application
    from types_.config import Github
    from types_.github import PostGist


DISCORD_TOKEN_REGEX: re.Pattern[str] = re.compile(r"[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27,}")

LOGGER = logging.getLogger(__name__)


class APIView(starlette_plus.View, prefix="api"):
    def __init__(self, app: Application, *, github_config: Github | None) -> None:
        self.app: Application = app
        self._handling_tokens = bool(self.app.session and github_config)

        if self._handling_tokens:
            assert github_config  # guarded by if here

            self._gist_token = github_config["token"]
            self._gist_timeout = github_config["timeout"]
            # tokens bucket for gist posting: {paste_id: token\ntoken}
            self.__tokens_bucket: dict[str, str] = {}
            self.__token_lock = asyncio.Lock()
            self.__token_task = asyncio.create_task(self._token_task())

    async def _token_task(self) -> None:
        # won't run unless pre-reqs are met in __init__
        while True:
            if self.__tokens_bucket:
                async with self.__token_lock:
                    await self._post_gist_of_tokens()

            await asyncio.sleep(self._gist_timeout)

    def _handle_discord_tokens(self, *bodies: dict[str, str], paste_id: str) -> None:
        formatted_bodies = "\n".join(b["content"] for b in bodies)

        tokens = list(DISCORD_TOKEN_REGEX.finditer(formatted_bodies))

        if not tokens:
            return

        tokens = "\n".join([m[0] for m in tokens])
        self.__tokens_bucket[paste_id] = tokens

    async def _post_gist_of_tokens(self) -> None:
        assert self.app.session  # guarded in caller
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

        current_tokens = self.__tokens_bucket.copy()
        self.__tokens_bucket = {}

        for paste_id, tokens in current_tokens.items():
            filename = str(datetime.datetime.now(datetime.UTC)) + f"/{paste_id}-tokens.txt"
            json_payload["files"][filename] = {"content": tokens}

        try:
            async with self.app.session.post(
                "https://api.github.com/gists", headers=github_headers, json=json_payload
            ) as resp:
                if not resp.ok:
                    response_body = await resp.text()
                    LOGGER.error(
                        "Failed to create gist with token bucket with response status code %s and request body:-\n\n",
                        resp.status,
                        response_body,
                    )
                    self.__tokens_bucket.update(current_tokens)
                    return
        except (aiohttp.ClientError, aiohttp.ClientOSError):
            LOGGER.info("Gist created and invalidated tokens from %s pastes.", len(current_tokens))

    @starlette_plus.route("/paste/{id}", methods=["GET"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get_day"])
    async def paste_get(self, request: starlette_plus.Request) -> starlette_plus.Response:
        """Fetch a paste.

        ---
        summary: Fetch a paste.
        description:
            Fetches a paste with all relevant meta-data and files.\n\n

            Fetching pastes does not include the `password` or `safety` fields. You only receive the `safety` field
            directly after creating a paste.

        parameters:
            - in: path
              name: id
              schema:
                type: string
              required: true
              description: The paste ID.

            - in: header
              name: Authorization
              schema:
                type: string
                format: basic
              required: false
              description: The password for the paste; if one is required.

        responses:
            200:
                description: The paste meta-data and files.
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                id:
                                    type: string
                                    example: abc123
                                created_at:
                                    type: string
                                    example: 2024-01-01T00:00:00.000000+00:00
                                expires:
                                    type: string
                                views:
                                    type: integer
                                    example: 3
                                has_password:
                                    type: boolean
                                    example: false
                                files:
                                    type: array
                                    items:
                                    type: object
                                    properties:
                                        parent_id:
                                            type: string
                                        content:
                                            type: string
                                        filename:
                                            type: string
                                        loc:
                                            type: integer
                                        charcount:
                                            type: integer
                                        annotation:
                                            type: string

            404:
                description: The paste does not exist or has been previously deleted.
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                error:
                                    type: string

            401:
                description: You are not authorized to view this paste or you provided an incorrect password.
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                error:
                                    type: string
                                    example: Unauthorized.

            429:
                description: You are requesting too fast.
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                error:
                                    type: string
                                    example: You are requesting too fast.
        """
        password: str | None = request.headers.get("authorization", None)
        identifier: str = request.path_params["id"]

        paste = await self.app.database.fetch_paste(identifier, password=password)
        if not paste:
            return starlette_plus.JSONResponse(
                {"error": f'A paste with the id "{identifier}" could not be found or has expired.'}, status_code=404
            )

        if paste.has_password and not paste.password_ok:
            return starlette_plus.JSONResponse({"error": "Unauthorized"}, status_code=401)

        to_return: dict[str, Any] = paste.serialize(exclude=["safety", "password", "password_ok"])
        return starlette_plus.JSONResponse(to_return)

    @starlette_plus.route("/paste", methods=["POST"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_post"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_post_day"])
    async def paste_post(self, request: starlette_plus.Request) -> starlette_plus.Response:
        """Create a paste.

        ---
        summary: Create a paste.
        description:
            Creates a paste with or without multiple files for view on the web or via the API.
            You can use this endpoint to POST valid `JSON` data or `plain-text` content.\n\n\n

            When using `plain-text`, only one file will be created, without a password or expiry.\n\n\n

            Max Character per file is `300_000`.\n\n

            Max file limit is `5`.\n\n

            If the paste is regarded as public, and contains Discord authorization tokens,
            then these will be invalidated upon paste creation.\n\n

        requestBody:
            description: The paste data. `password` and `expires` are optional.
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            files:
                                type: array
                                items:
                                type: object
                                properties:
                                    filename:
                                        type: string
                                        required: false
                                    content:
                                        type: string
                                        required: true
                                example:
                                    - filename: thing.py
                                      content: print(\"Hello World!\")
                                    - content: Some text or code...
                            password:
                                required: false
                                type: string
                                example: null
                            expires:
                                required: false
                                type: string
                                example: null
                text/plain:
                    schema:
                        type: string

        responses:
            200:
                description: The paste meta-data.
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                id:
                                    type: string
                                    example: abc123
                                created_at:
                                    type: string
                                    example: 2024-01-01T00:00:00.000000+00:00
                                expires:
                                    type: string
                                    example: 2024-01-01T00:00:00.000000+00:00
                                safety:
                                    type: string
            400:
                description: The paste data was invalid.
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                error:
                                    type: string
                                    example: The reason the paste was invalid.
            429:
                description: You are requesting too fast.
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                error:
                                    type: string
                                    example: You are requesting too fast.
        """

        content_type: str | None = request.headers.get("content-type", None)
        body: dict[str, Any] | str
        data: dict[str, Any]

        if content_type == "application/json":
            try:
                body = await request.json()
            except json.JSONDecodeError:
                return starlette_plus.JSONResponse({"error": "Invalid JSON provided."}, status_code=400)
        else:
            body = (await request.body()).decode(encoding="UTF-8")

        data = {"files": [{"content": body, "filename": None}]} if isinstance(body, str) else body

        if resp := validate_paste(data):
            return resp

        expiry_str: str | None = data.get("expires", None)

        try:
            expiry: datetime.datetime | None = datetime.datetime.fromisoformat(expiry_str) if expiry_str else None
        except Exception as e:
            return starlette_plus.JSONResponse({"error": f'Unable to parse "expiry" parameter: {e}'}, status_code=400)

        data["expires"] = expiry
        password = data.get("password")
        data["password"] = password

        paste = await self.app.database.create_paste(data=data)

        if not password:
            # if the user didn't provide a password (a public paste)
            # we check for discord tokens
            self._handle_discord_tokens(*data["files"], paste_id=paste.id)

        to_return: dict[str, Any] = paste.serialize(exclude=["password", "password_ok"])
        to_return.pop("files", None)

        return starlette_plus.JSONResponse(to_return, status_code=200)

    @starlette_plus.route("/security/info/{token}")
    async def security_info(self, request: starlette_plus.Request) -> starlette_plus.Response:
        token: str | None = request.path_params.get("token", None)
        if not token:
            return starlette_plus.JSONResponse({"error": "Unauthorized."}, status_code=401)

        paste = await self.app.database.fetch_paste_security(token=token)
        if not paste:
            return starlette_plus.JSONResponse(
                {"error": "A paste was not found with the provided token, or has expired or been deleted."},
                status_code=404,
            )

        delete: str = f"{CONFIG['SERVER']['domain']}/api/security/delete/{token}"
        info: str = f"{CONFIG['SERVER']['domain']}/api/security/info/{token}"
        data: dict[str, str] = {
            "token": paste.safety,
            "delete": delete,
            "info": info,
            "extra": "Visiting the delete URL will remove the paste instantly.",
        }

        return starlette_plus.JSONResponse(data, status_code=200)

    @starlette_plus.route("/security/delete/{token}", methods=["GET"])
    async def security_delete(self, request: starlette_plus.Request) -> starlette_plus.Response:
        """Delete a paste.

        ---
        summary: Delete a paste.
        description:
            Deletes a paste with the associated safety token.\n\n

            This action is not reversible.

        parameters:
            - in: path
              name: token
              schema:
                type: string
              required: true
              description: The safety token received when creating the paste.


        responses:
            200:
                description: The paste was successfully deleted.
                content:
                    text/plain:
                        schema:
                            type: string

            401:
                description: You are not authorized to delete this paste.
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                error:
                                    type: string
                                    example: Unauthorized.
        """
        token: str | None = request.path_params.get("token", None)
        if not token:
            return starlette_plus.JSONResponse({"error": "Unauthorized."}, status_code=401)

        await self.app.database.delete_paste_security(token=token)
        return starlette_plus.Response("Ok", status_code=200)
