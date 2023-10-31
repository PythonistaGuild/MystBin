"""Copyright(C) 2020 PythonistaGuild

This file is part of MystBin.

MystBin is free software: you can redistribute it and / or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

MystBin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY
without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with MystBin.  If not, see <https://www.gnu.org/licenses/>.
"""
from __future__ import annotations

import pathlib
import json

from asyncpg import Record
from models import responses

from mystbin_models import MystbinRequest
from utils import openapi
from utils.ratelimits import limit
from utils.responses import Response, VariableResponse
from utils.router import Router


__p = pathlib.Path("./config.json")
if not __p.exists():
    __p = pathlib.Path("../../config.json")

with __p.open() as __f:
    __config = json.load(__f)

del __p, __f  # micro-opt, don't keep unneeded variables in-ram


router = Router()


desc = f"""Delete a paste using a Safety Token.

When you create a paste you will receive a token named "safety_token", this token is displayed **only once**.

This endpoint has no direct ratelimit bucket, and falls only under the global ratelimit.
The global ratelimit is {__config['ratelimits']['global']}, and {__config['ratelimits']["authed_global"]} when logged in.
"""


@router.delete("/safety/delete/{safety_token}")
@openapi.instance.route(
    openapi.Route(
        "/safety/delete/{safety_token}",
        "DELETE",
        "Delete Paste with Safety Token",
        ["safety"],
        None,
        [openapi.RouteParameter("Safety Token", "string", "safety_token", True, "path")],
        {
            200: openapi.Response("Success", openapi.SafetyDeleteResponse),
            404: openapi.NotFoundResponse,
        },
        description=desc,
    )
)
@limit()
async def safety_delete(request: MystbinRequest) -> Response:
    safety_token: str = request.path_params["safety_token"]

    deleted: Record = await request.app.state.db.delete_paste("", safety=safety_token)
    if not deleted:
        return VariableResponse({"error": "Not Found"}, request, status_code=404)
    
    resp = responses.create_struct(deleted, responses.SafetyDelete)
    return VariableResponse(resp, request, status_code=200)
