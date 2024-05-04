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

import datetime
import json
from typing import TYPE_CHECKING, Any

import starlette_plus

from core import CONFIG
from core.utils import validate_paste


if TYPE_CHECKING:
    from core import Application


class APIView(starlette_plus.View, prefix="api"):
    def __init__(self, app: Application) -> None:
        self.app: Application = app

    @starlette_plus.route("/paste/{id}", methods=["GET"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get_day"])
    async def paste_get(self, request: starlette_plus.Request) -> starlette_plus.Response:
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
        data["password"] = data.get("password", None)

        paste = await self.app.database.create_paste(data=data)
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

    @starlette_plus.route("/security/delete/{token}", methods=["GET", "DELETE", "POST"])
    async def security_delete(self, request: starlette_plus.Request) -> starlette_plus.Response:
        token: str | None = request.path_params.get("token", None)
        if not token:
            return starlette_plus.JSONResponse({"error": "Unauthorized."}, status_code=401)

        await self.app.database.delete_paste_security(token=token)
        return starlette_plus.Response("Ok", status_code=200)
