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
import msgspec

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

Version changed: 4.0

Changed in version 4.0
- Removed the `token` attribute from the response payload
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
) -> Response:
    user = request.state.user
    if not user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    return Response(msgspec.json.encode(responses.create_struct(user, responses.User))) # type: ignore


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
async def delete_bookmark(request: MystbinRequest) -> Response:
    if not request.state.user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)
    
    payload = await request.body()

    try:
        bookmark = payloads.create_struct_from_payload(payload, payloads.BookmarkPutDelete)
    except (msgspec.DecodeError, msgspec.ValidationError) as e:
        return UJSONResponse({"error": e.args[0]}, status_code=400)

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
async def get_bookmarks(request: MystbinRequest) -> Response:
    """Fetches all of the authorized users bookmarks
    * Requires authentication
    """
    if not request.state.user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    data = await request.app.state.db.get_bookmarks(request.state.user["id"])
    return UJSONResponse({"bookmarks": data})


desc = f"""Lists tokens available on your account.
This does NOT return actual tokens or authentication data, only metadata about tokens you've created.
* Required authentication.

This endpoint falls under the `self` ratelimit bucket.
The `self` bucket has a ratelimit of {__config['ratelimits']['self']}

Version added: 4.0
"""

@router.get("/users/tokens")
@openapi.instance.route(openapi.Route(
    "/users/tokens",
    "GET",
    "Get Tokens",
    ["users"],
    None,
    [],
    {
        200: openapi.Response("Success", openapi.TokenListResponse),
        401: openapi.UnauthorizedResponse
    },
    description=desc,
    is_body_required=False
))
@limit("self")
async def get_tokens(request: MystbinRequest):
    if not request.state.user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)
    
    data = await request.app.state.db.get_tokens(request.state.user["id"])
    return UJSONResponse(responses.TokenList([responses.TokenListItem(
        id=x["id"],
        name=x["token_name"],
        description=x["token_description"],
        is_web_token=x["is_main"])
        for x in data]
    ))


desc = f"""Regenerates a token under your account.
* Required authentication.

This endpoint falls under the `tokengen` ratelimit bucket.
The `tokengen` bucket has a ratelimit of {__config['ratelimits']['tokengen']}

Version changed: 4.0

Changed in version 4.0:
- endpoint moved from /users/regenerate to users/tokens
- endpoint now has a required token_id query param
- endpoint changed from POST to PATCH
"""

@router.patch("/users/tokens")
@openapi.instance.route(openapi.Route(
    "/users/tokens",
    "PATCH",
    "Regenerate Token",
    ["users"],
    None,
    [
        openapi.RouteParameter("Token ID", "integer", "token_id", True, "query")
    ],
    {
        200: openapi.Response("Success", openapi.TokenResponse),
        400: openapi.BadRequestResponse,
        401: openapi.UnauthorizedResponse
    },
    description=desc,
    is_body_required=False
))
@limit("tokengen")
async def regen_token(request: MystbinRequest) -> UJSONResponse:
    if not request.state.user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        token_id = int(request.query_params["token_id"])
    except:
        return UJSONResponse({"error": "bad query parameter 'token_id'"}, status_code=400)

    token: str | None = await request.app.state.db.regen_token(userid=request.state.user["id"], token_id=token_id)
    if not token:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    return UJSONResponse({"token": token})


desc = f"""Creates a new token under your account.
* Required authentication.

This endpoint falls under the `tokengen` ratelimit bucket.
The `tokengen` bucket has a ratelimit of {__config['ratelimits']['tokengen']}

Version added: 4.0
"""

@router.post("/users/tokens")
@openapi.instance.route(openapi.Route(
    "/users/tokens",
    "POST",
    "Create Token",
    ["users"],
    openapi.TokenPost,
    [],
    {
        200: openapi.Response("Success", openapi.TokenPostResponse),
        400: openapi.BadRequestResponse,
        401: openapi.UnauthorizedResponse
    },
    description=desc,
))
@limit("tokengen")
async def delete_token(request: MystbinRequest) -> UJSONResponse:
    if not request.state.user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        _body = await request.body()
        data = payloads.create_struct_from_payload(_body, payloads.TokenPost)
    except (msgspec.DecodeError, msgspec.ValidationError) as e:
        return UJSONResponse({"error": e.args[0]}, status_code=400)
    except:
        return UJSONResponse({"error": "bad body passed"}, status_code=400)

    resp = await request.app.state.db.create_token(request.state.user["id"], data.name, data.description)
    if resp is None:
        return UJSONResponse({"error": "Name or description are not within permitted lengths"}, status_code=400)
    
    return UJSONResponse({"name": data.name, "id": resp[1], "token": resp[0]})


desc = f"""Deletes a token from your account.
* Required authentication.

This endpoint falls under the `tokengen` ratelimit bucket.
The `tokengen` bucket has a ratelimit of {__config['ratelimits']['tokengen']}

Version added: 4.0
"""

@router.delete("/users/tokens")
@openapi.instance.route(openapi.Route(
    "/users/tokens",
    "DELETE",
    "Delete Token",
    ["users"],
    None,
    [
        openapi.RouteParameter("Token ID", "integer", "token_id", True, "query")
    ],
    {
        204: openapi.Response("Success", None),
        400: openapi.BadRequestResponse,
        401: openapi.UnauthorizedResponse
    },
    description=desc,
))
@limit("tokengen")
async def new_token(request: MystbinRequest) -> Response:
    if not request.state.user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        token_id = int(request.query_params["token_id"])
    except:
        return UJSONResponse({"error": "bad query parameter 'token_id'"}, status_code=400)

    if await request.app.state.db.delete_token(request.state.user["id"], token_id=token_id):
        return Response(status_code=204)
    
    return UJSONResponse({"error": "Unauthorized"}, status_code=401)
