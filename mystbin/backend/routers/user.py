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
import pathlib
import json
from models import payloads, responses

from mystbin_models import MystbinRequest
from utils.ratelimits import limit
from utils.responses import Response, UJSONResponse
from utils.router import Router
from utils import openapi


router = Router()

__p = pathlib.Path("./config.json")
if not __p.exists():
    __p = pathlib.Path("../../config.json")

with __p.open() as __f:
    __config = json.load(__f)

desc = f"""Gets the User object of the currently logged in user.
* Required authentication.

This endpoint falls under the `self` ratelimit bucket.
The `self` bucket has a ratelimit of {__config['ratelimits']['self']}
"""

@router.get("/users/@me")
@openapi.instance.route(openapi.Route(
    "/users/@me",
    "GET",
    "Get Self",
    ["users"],
    None,
    [],
    {
        200: openapi.Response("Success", openapi.User),
        401: openapi.UnauthorizedResponse
    },
    description=desc,
    is_body_required=False
))
@limit("self")
async def get_self(
    request: MystbinRequest,
) -> UJSONResponse | responses.User:
    user = request.state.user
    if not user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    return responses.create_struct(user, responses.User)


desc = f"""Regenerates your token.
* Required authentication.

This endpoint falls under the `tokengen` ratelimit bucket.
The `self` bucket has a ratelimit of {__config['ratelimits']['self']}
"""


@router.post("/users/regenerate")
@openapi.instance.route(openapi.Route(
    "/users/regenerate",
    "POST",
    "Regenerate Token",
    ["users"],
    None,
    [],
    {
        200: openapi.Response("Success", openapi.TokenResponse),
        401: openapi.UnauthorizedResponse
    },
    description=desc,
    is_body_required=False
))
@limit("tokengen")
async def regen_token(request: MystbinRequest) -> UJSONResponse | dict[str, str]:
    if not request.state.user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    token: str | None = await request.app.state.db.regen_token(userid=request.state.user["id"])
    if not token:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    return UJSONResponse({"token": token})


desc = f"""Creates a bookmark on the authorized user's account.
* Required authentication.

This endpoint falls under the `bookmarks` ratelimit bucket.
The `bookmarks` bucket has a ratelimit of {__config['ratelimits']['bookmarks']}
"""


@router.put("/users/bookmarks")
@openapi.instance.route(openapi.Route(
    "/users/bookmarks",
    "PUT",
    "Create Bookmark",
    ["users"],
    openapi.BookmarkPutDelete,
    [],
    {
        204: openapi.Response("Success", None),
        400: openapi.BadRequestResponse,
        401: openapi.UnauthorizedResponse
    },
    description=desc
))
@limit("bookmarks")
async def create_bookmark(request: MystbinRequest) -> Response:
    if not request.state.user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        _data = await request.body()
    except:
        return UJSONResponse({"error": "Bad body"}, status_code=400)
    
    bookmark = payloads.create_struct_from_payload(_data, payloads.BookmarkPutDelete)

    try:
        await request.app.state.db.create_bookmark(request.state.user["id"], bookmark.paste_id)
        return Response(status_code=204)
    except ValueError as e:
        return UJSONResponse({"error": e.args[0]}, status_code=400)


desc = f"""Deletes a bookmark from the authorized user's account.
* Required authentication.

This endpoint falls under the `bookmarks` ratelimit bucket.
The `bookmarks` bucket has a ratelimit of {__config['ratelimits']['bookmarks']}
"""


@router.delete("/users/bookmarks")
@openapi.instance.route(openapi.Route(
    "/users/bookmarks",
    "DELETE",
    "Delete Bookmark",
    ["users"],
    openapi.BookmarkPutDelete,
    [],
    {
        204: openapi.Response("Success", None),
        400: openapi.BadRequestResponse,
        401: openapi.UnauthorizedResponse
    },
    description=desc
))
@limit("bookmarks")
async def delete_bookmark(request: MystbinRequest, bookmark: payloads.BookmarkPutDelete) -> Response:
    if not request.state.user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    if not await request.app.state.db.delete_bookmark(request.state.user["id"], bookmark.paste_id):
        return UJSONResponse({"error": "Bookmark does not exist"}, status_code=400)
    else:
        return Response(status_code=204)


desc = f"""Deletes a bookmark from the authorized user's account.
* Required authentication.

This endpoint falls under the `bookmarks` ratelimit bucket.
The `bookmarks` bucket has a ratelimit of {__config['ratelimits']['bookmarks']}
"""


@router.get("/users/bookmarks")
@openapi.instance.route(openapi.Route(
    "/users/bookmarks",
    "GET",
    "Get Bookmarks",
    ["users"],
    None,
    [],
    {
        200: openapi.Response("Success", openapi.BookmarkResponse),
        401: openapi.UnauthorizedResponse
    },
    description=desc
))
@limit("bookmarks")
async def get_bookmarks(request: MystbinRequest):
    """Fetches all of the authorized users bookmarks
    * Requires authentication
    """
    if not request.state.user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    data = await request.app.state.db.get_bookmarks(request.state.user["id"])
    return UJSONResponse({"bookmarks": data})
