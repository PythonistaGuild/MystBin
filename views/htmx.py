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
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import unquote

import bleach
import humanize
import starlette_plus

from core import CONFIG
from core.utils import validate_paste


if TYPE_CHECKING:
    from starlette.datastructures import FormData

    from core import Application


class HTMXView(starlette_plus.View, prefix="htmx"):
    def __init__(self, app: Application) -> None:
        self.app: Application = app

    def highlight_code(self, filename: str, content: str, *, index: int, raw_url: str, annotation: str) -> str:
        filename = bleach.clean(filename, attributes=[], tags=[])
        content = bleach.clean(content, attributes=[], tags=[])

        annotations: str = f'<small class="annotations">❌ {annotation}</small>' if annotation else ""

        return f"""
        <div id="__paste_a_{index}" class="pasteArea">
            <div class="pasteHeader">
                <div style="display: flex; gap: 1rem; align-items: center;">
                    <span class="filenameArea">{filename}</span>
                    <span class="pasteButton" onclick="hideFile(this, {index})">Hide</span>
                    <span id="__paste_copy_{index}" class="pasteButton" onclick="copyFile({index})">Copy</span>
                    <a class="pasteButton" href="{raw_url}/{index + 1}">Raw</a>
                </div>
            </div>
            {annotations}
            <pre id="__paste_c_{index}" class="fileContent"><code>{content}</code></pre>
        </div>"""

    @starlette_plus.route("/", prefix=False)
    async def home(self, request: starlette_plus.Request) -> starlette_plus.Response:
        return starlette_plus.FileResponse("web/index.html")

    @starlette_plus.route("/{id}", prefix=False)
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get_day"])
    async def paste(self, request: starlette_plus.Request) -> starlette_plus.Response:
        return starlette_plus.FileResponse("web/paste.html")

    @starlette_plus.route("/raw/{id}", prefix=False)
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get_day"])
    async def paste_raw(self, request: starlette_plus.Request) -> starlette_plus.Response:
        password: str | None = request.headers.get("authorization", None)
        identifier: str = request.path_params["id"]

        paste = await self.app.database.fetch_paste(identifier, password=password)
        if not paste:
            return starlette_plus.JSONResponse(
                {"error": f'A paste with the id "{identifier}" could not be found or has expired.'},
                status_code=404,
            )

        if paste.has_password and not paste.password_ok:
            return starlette_plus.JSONResponse(
                {"error": "Unauthorized. Raw pastes can not be viewed when protected by passwords."},
                status_code=401,
            )

        to_return: dict[str, Any] = paste.serialize(exclude=["safety", "password", "password_ok"])
        text: str = "\n\n\n\n".join([f"# MystBin ! - {f['filename']}\n{f['content']}" for f in to_return["files"]])

        return starlette_plus.PlainTextResponse(text)

    @starlette_plus.route("/raw/{id}/{page:int}", prefix=False)
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get_day"])
    async def paste_raw_page(self, request: starlette_plus.Request) -> starlette_plus.Response:
        password: str | None = request.headers.get("authorization", None)
        identifier: str = request.path_params["id"]
        page: int = max(request.path_params["page"], 1)

        paste = await self.app.database.fetch_paste(identifier, password=password)
        if not paste:
            return starlette_plus.JSONResponse(
                {"error": f'A paste with the id "{identifier}" could not be found or has expired.'},
                status_code=404,
            )

        if paste.has_password and not paste.password_ok:
            return starlette_plus.JSONResponse(
                {"error": "Unauthorized. Raw pastes can not be viewed when protected by passwords."},
                status_code=401,
            )

        to_return: dict[str, Any] = paste.serialize(exclude=["safety", "password", "password_ok"])

        try:
            text: str = to_return["files"][page - 1]["content"]
        except IndexError:
            return starlette_plus.JSONResponse({"error": f"This file does not exist on paste: '{identifier}'"})

        return starlette_plus.PlainTextResponse(text)

    @starlette_plus.route("/fetch")
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get_day"])
    async def fetch_paste(self, request: starlette_plus.Request) -> starlette_plus.Response:
        no_reload: bool = request.query_params.get("noReload", False) == "true"
        password: str = unquote(request.query_params.get("pastePassword", ""))

        identifier_quoted: str | None = request.query_params.get("id", None)
        if not identifier_quoted:
            return starlette_plus.HTMLResponse("<h1>404 - That paste was not Found!</h1>")

        identifier: str = unquote(identifier_quoted).replace("/", "")
        paste = await self.app.database.fetch_paste(identifier, password=password)

        if not paste:
            return starlette_plus.HTMLResponse("<h1>404 - That paste was not Found!</h1>")

        if paste.has_password and not paste.password_ok:
            error_headers: dict[str, str] = {"HX-Retarget": "#errorResponse", "HX-Reswap": "outerHTML"}

            if no_reload:
                return starlette_plus.HTMLResponse(
                    """<span id="errorResponse">Incorrect Password.</span>""",
                    headers=error_headers,
                )

            return starlette_plus.FileResponse("web/password.html")

        data: dict[str, Any] = paste.serialize(exclude=["safety", "password", "password_ok"])
        files: list[dict[str, Any]] = data["files"]
        created_delta: datetime.timedelta = datetime.datetime.now(tz=datetime.timezone.utc) - paste.created_at.replace(
            tzinfo=datetime.timezone.utc
        )

        url: str = f"{CONFIG['SERVER']['domain']}/{identifier}"
        raw_url: str = f"{CONFIG['SERVER']['domain']}/raw/{identifier}"

        html: str = f"""
        <div class="identifierHeader">
            <div class="identifierHeaderLeft">
                <a href="{url}">/{identifier}</a>
                <span>Created {humanize.naturaltime(created_delta)}...</span>
            </div>
            <div class="identifierHeaderSection">
                <a href="{raw_url}">Raw</a>
                <!-- <a href="#">Download</a> -->
            </div>
        </div>
        """
        for i, file in enumerate(files):
            html += self.highlight_code(
                file["filename"],
                file["content"],
                index=i,
                raw_url=raw_url,
                annotation=file["annotation"],
            )

        return starlette_plus.HTMLResponse(html)

    @starlette_plus.route("/save", methods=["POST"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_post"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_post_day"])
    async def htmx_save(self, request: starlette_plus.Request) -> starlette_plus.Response:
        form: FormData = await request.form()
        multi = form.multi_items()

        password: str = cast(str, multi.pop()[1])
        names: list[str] = cast(list[str], [i[1] for i in multi if i[0] == "fileName"])
        contents: list[str] = cast(list[str], [i[1] for i in multi if i[0] == "fileContent"])

        error_headers: dict[str, str] = {"HX-Retarget": "#errorResponse"}

        if len(names) != len(contents):
            return starlette_plus.HTMLResponse(
                """<span id="errorResponse">400: Invalidated paste data.</span>""",
                headers=error_headers,
            )

        data: dict[str, Any] = {"files": []}
        for n in range(len(names)):
            if not contents[n]:
                continue

            inner: dict[str, str | None] = {}

            inner["filename"] = names[n] or None
            inner["content"] = contents[n]
            data["files"].append(inner)

        if not data["files"]:
            return starlette_plus.HTMLResponse(
                """<span id="errorResponse">400: Missing files or data to paste.</span>""",
                headers=error_headers,
            )

        if resp := validate_paste(data):
            json_: dict[str, Any] = json.loads(resp.body)
            return starlette_plus.HTMLResponse(
                f"""<span id="errorResponse">{resp.status_code}: {json_["error"]}</span>""",
                headers=error_headers,
            )

        data["expires"] = None  # TODO: Add this to Frontend...
        data["password"] = password or None

        paste = await self.app.database.create_paste(data=data)
        to_return: dict[str, Any] = paste.serialize(exclude=["password", "password_ok"])
        files: list[dict[str, Any]] = to_return["files"]

        identifier: str = to_return["id"]
        raw_url: str = f"{CONFIG['SERVER']['domain']}/raw/{identifier}"

        inner_html: str = ""
        for i, file in enumerate(files):
            inner_html += self.highlight_code(
                file["filename"],
                file["content"],
                index=i,
                raw_url=raw_url,
                annotation=file["annotation"],
            )

        url: str = f"{CONFIG['SERVER']['domain']}/{identifier}"
        security_url: str = f"{CONFIG['SERVER']['domain']}/api/security/info/{to_return['safety']}"

        created_delta: datetime.timedelta = datetime.datetime.now(tz=datetime.timezone.utc) - paste.created_at.replace(
            tzinfo=datetime.timezone.utc
        )

        headers: dict[str, str] = {"HX-Push-Url": url}
        html: str = f"""
        <div id="content" class="content">
            <div class="identifierHeader">
                <div class="identifierHeaderLeft">
                    <a href="{url}">/{identifier}</a>
                    <span>Created {humanize.naturaltime(created_delta)}...</span>
                </div>
                <div class="identifierHeaderSection">
                    <a class="security" href="{security_url}">Security Info</a>
                </div>
                <div class="identifierHeaderSection">
                    <a href="{raw_url}">Raw</a>
                    <!-- <a href="#">Download</a> -->
                </div>
            </div>
            <div id="pastecontainer" class="pasteContainer">{inner_html}</div>
        </div>"""

        return starlette_plus.HTMLResponse(html, headers=headers)
