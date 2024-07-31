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
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import unquote, urlsplit

import asyncpg
import bleach
import starlette_plus

from core import CONFIG
from core.utils import natural_time, validate_paste


if TYPE_CHECKING:
    from starlette.datastructures import FormData

    from core import Application


with open("web/paste.html") as fp:
    PASTE_HTML: str = fp.read()


class HTMXView(starlette_plus.View, prefix="htmx"):
    def __init__(self, app: Application) -> None:
        self.app: Application = app

    def highlight_code(self, *, files: list[dict[str, Any]]) -> str:
        html: str = ""

        for index, file in enumerate(files):
            filename = bleach.clean(file["filename"], attributes=[], tags=[])
            filename = "_".join(filename.splitlines())

            raw_url: str = f'/raw/{file["parent_id"]}'
            annotation: str = file["annotation"] or ""
            positions: list[int] = file.get("warning_positions", [])
            original: str = file["content"]

            parts: list[str] = annotation.split(":")
            annotation = parts.pop(0)

            extra: str = (
                f"""<span class="annotationSecond" data-text="Discord tokens will be invalidated automatically">{parts[0]}"""
                if parts
                else ""
            )
            annotations: str = (
                f'<small class="annotations">❌ {annotation}{": " + extra if extra else ""}</small>'
                if annotation
                else ""
            )

            position: int = 0
            next_pos: int | None = positions.pop(0) if positions else None

            numbers: list[str] = []
            for n, line in enumerate(original.splitlines(), 1):
                length: int = len(line)

                if next_pos is not None and position <= next_pos <= position + length:
                    numbers.append(
                        f"""<tr data-ln="{n}"><td class="lineNumRow" onclick="highlightLine(event, '{index}', '{n}')">{n}</td><td class="lineWarn"></td></tr>"""
                    )

                    try:
                        next_pos = positions.pop(0)
                    except IndexError:
                        next_pos = None

                else:
                    numbers.append(
                        f"""<tr data-ln="{n}"><td class="lineNumRow" onclick="highlightLine(event, '{index}', '{n}')">{n}</td></tr>"""
                    )

                position += length + 1

            content = bleach.clean(
                original.replace("<!", "&lt;&#33;").replace("&#xa;", "&amp;#xa;"),
                attributes=[],
                tags=[],
                strip_comments=False,
            )

            lines: str = f"""<table class="lineNums"><tbody>\n{"".join(numbers)}\n</tbody></table>"""
            html += f"""
            <div id="__paste_a_{index}" class="pasteArea">
                <div class="pasteHeader">
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        <span class="filenameArea">{filename}</span>
                        <span class="pasteButton" onclick="hideFile(this, {index})">Hide</span>
                        <span id="__paste_copy_{index}" class="pasteButton" onclick="copyFile({index})">Copy</span>
                        <a class="pasteButton" href="{raw_url}/{index + 1}">Raw</a>
                    </div>
                </div>
                {annotations}
                <pre id="__paste_c_{index}" class="fileContent" style="display: flex; flex-grow: 1;">{lines}<code>{content}</code></pre>
            </div>"""

        return html

    def check_discord(self, request: starlette_plus.Request) -> starlette_plus.Response | None:
        agent: str = request.headers.get("user-agent", "")
        if "discordbot" in agent.lower():
            return starlette_plus.Response(status_code=204)

    @starlette_plus.route("/", prefix=False)
    async def home(self, request: starlette_plus.Request) -> starlette_plus.Response:
        if resp := self.check_discord(request=request):
            return resp

        return starlette_plus.FileResponse("web/index.html")

    @starlette_plus.route("/protected/{id}", prefix=False)
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get_day"])
    async def protected_paste(self, request: starlette_plus.Request) -> starlette_plus.Response:
        return starlette_plus.FileResponse("web/password.html")

    @starlette_plus.route("/{id}", prefix=False)
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get_day"])
    async def paste(self, request: starlette_plus.Request) -> starlette_plus.Response:
        if resp := self.check_discord(request=request):
            return resp

        identifier: str = request.path_params.get("id", "pass")
        htmx_url: str | None = request.headers.get("HX-Current-URL", None)

        if htmx_url and identifier == "pass":
            identifier = urlsplit(htmx_url).path.removeprefix("/protected/")

        not_found: str = """
            <div class="notFound">
                <h2>404 - This page or paste could not be found</h2>
                <a href="/">Return Home...</a>
            </div>
        """

        password: str = unquote(request.query_params.get("pastePassword", ""))
        paste = await self.app.database.fetch_paste(identifier, password=password)

        if not paste:
            return starlette_plus.HTMLResponse(PASTE_HTML.format(__PASTES__=not_found))

        if paste.has_password and not paste.password_ok:
            if not password:
                return starlette_plus.RedirectResponse(f"/protected/{identifier}")

            error_headers: dict[str, str] = {"HX-Retarget": "#errorResponse", "HX-Reswap": "outerHTML"}
            return starlette_plus.HTMLResponse(
                """<span id="errorResponse">Incorrect Password.</span>""",
                headers=error_headers,
            )

        data: dict[str, Any] = paste.serialize(exclude=["password", "password_ok"])
        files: list[dict[str, Any]] = data["files"]
        created_delta: datetime.timedelta = datetime.datetime.now(tz=datetime.timezone.utc) - paste.created_at.replace(
            tzinfo=datetime.timezone.utc
        )

        url: str = f"/{identifier}"
        raw_url: str = f"/raw/{identifier}"
        security_html: str = ""

        stored: list[str] = request.session.get("pastes", [])
        if identifier in stored:
            security_url: str = f"/api/security/info/{data['safety']}"

            security_html = f"""
            <div class="identifierHeaderSection">
                <a class="security" href="{security_url}">Security Info</a>
            </div>"""

        html: str = f"""
        <div class="identifierHeader">
            <div class="identifierHeaderLeft">
                <a href="{url}">/{identifier}</a>
                <span>Created {natural_time(created_delta)}...</span>
            </div>
            {security_html}
            <div class="identifierHeaderSection">
                <a href="{raw_url}">Raw</a>
                <!-- <a href="#">Download</a> -->
            </div>
        </div>
        """

        html += await asyncio.to_thread(self.highlight_code, files=files)
        if htmx_url and password:
            return starlette_plus.HTMLResponse(html, headers={"HX-Replace-Url": f"{url}?pastePassword={password}"})

        return starlette_plus.HTMLResponse(PASTE_HTML.format(__PASTES__=html), media_type="text/html")

    @starlette_plus.route("/raw/{id}", prefix=False)
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get_day"])
    async def paste_raw(self, request: starlette_plus.Request) -> starlette_plus.Response:
        if resp := self.check_discord(request=request):
            return resp

        password: str | None = request.headers.get("authorization", None)
        identifier: str = request.path_params["id"]

        htmx_url: str | None = request.headers.get("HX-Current-URL", None)
        if identifier == "0" and htmx_url:
            identifier = htmx_url.removeprefix(f"{request.url.scheme}://{request.url.hostname}/")

        headers: dict[str, str] = {"HX-Redirect": f"/raw/{identifier}"}
        paste = await self.app.database.fetch_paste(identifier, password=password)

        if not paste:
            return starlette_plus.JSONResponse(
                {"error": f'A paste with the id "{identifier}" could not be found or has expired.'},
                status_code=404,
                headers=headers,
            )

        if paste.has_password and not paste.password_ok:
            return starlette_plus.JSONResponse(
                {"error": "Unauthorized. Raw pastes can not be viewed when protected by passwords."},
                status_code=401,
                headers=headers,
            )

        to_return: dict[str, Any] = paste.serialize(exclude=["safety", "password", "password_ok"])
        text: str = "\n\n\n\n".join([f"# MystBin ! - {f['filename']}\n{f['content']}" for f in to_return["files"]])

        return starlette_plus.PlainTextResponse(text, headers=headers)

    @starlette_plus.route("/raw/{id}/{page:int}", prefix=False)
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_get_day"])
    async def paste_raw_page(self, request: starlette_plus.Request) -> starlette_plus.Response:
        if resp := self.check_discord(request=request):
            return resp

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

    @starlette_plus.route("/save", methods=["POST"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_post"])
    @starlette_plus.limit(**CONFIG["LIMITS"]["paste_post_day"])
    async def htmx_save(self, request: starlette_plus.Request) -> starlette_plus.Response:
        if resp := self.check_discord(request=request):
            return resp

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

            try:
                inner["filename"] = names[n].encode("UTF-8").decode("UTF-8") or None
                inner["content"] = contents[n].encode("UTF-8").decode("UTF-8")
            except Exception:
                return starlette_plus.HTMLResponse(
                    """<span id="errorResponse">400: File/Filename contains invalid characters.</span>""",
                    headers=error_headers,
                )
            data["files"].append(inner)

        if not data["files"]:
            return starlette_plus.HTMLResponse(
                """<span id="errorResponse">400: Missing files or data to paste.</span>""",
                headers=error_headers,
            )

        if resp := validate_paste(data):
            json_: dict[str, Any] = json.loads(resp.body)  # type: ignore Can only be memoryview when specifically used.
            return starlette_plus.HTMLResponse(
                f"""<span id="errorResponse">{resp.status_code}: {json_["error"]}</span>""",
                headers=error_headers,
            )

        data["expires"] = None  # TODO: Add this to Frontend...
        data["password"] = password or None

        try:
            paste = await self.app.database.create_paste(data=data)
        except asyncpg.CharacterNotInRepertoireError:
            return starlette_plus.HTMLResponse(
                """<span id="errorResponse">400: File/Filename contains invalid characters.</span>""",
                headers=error_headers,
            )

        to_return: dict[str, Any] = paste.serialize(exclude=["password", "password_ok"])
        identifier: str = to_return["id"]

        url: str = f"/{identifier}"

        try:
            (request.session["pastes"].append(identifier))
        except (KeyError, AttributeError):
            request.session["pastes"] = [identifier]
        else:
            request.session["pastes"] = request.session["pastes"][-5:]

        return starlette_plus.HTMLResponse("", headers={"HX-Redirect": url})
