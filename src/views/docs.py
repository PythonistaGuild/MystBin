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

from typing import TYPE_CHECKING

import starlette_plus

if TYPE_CHECKING:
    from core import Application


class DocsView(starlette_plus.View, prefix="api"):
    def __init__(self, app: Application) -> None:
        self.app: Application = app

    @starlette_plus.route("/documentation")
    async def documentation(self, _: starlette_plus.Request) -> starlette_plus.Response:  # noqa: PLR6301 # must be a bound method for decoration
        headers = {"Access-Control-Allow-Origin": "*"}
        return starlette_plus.FileResponse("web/docs.html", headers=headers)

    @starlette_plus.route("/docs")
    async def documentation_redirect(self, _: starlette_plus.Request) -> starlette_plus.Response:  # noqa: PLR6301 # must be a bound method for decoration
        return starlette_plus.RedirectResponse("/api/documentation")

    @starlette_plus.route("/schema")
    async def openapi_schema(self, request: starlette_plus.Request) -> starlette_plus.Response:
        if not self.app.schemas:
            return starlette_plus.Response(status_code=503)

        return self.app.schemas.OpenAPIResponse(request=request)
