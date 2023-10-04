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
from utils.responses import Response, VariableResponse
from utils.router import Router
from utils import openapi


router = Router()

__p = pathlib.Path("./config.json")
if not __p.exists():
    __p = pathlib.Path("../../config.json")

with __p.open() as __f:
    __config = json.load(__f)

desc = f"""Gets the User object of the currently logged in user.
* Requires authentication.

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
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)

    return VariableResponse(responses.create_struct(user, responses.User), request) # type: ignore


desc = f"""Update the User object of the currently logged in user.
* Requires authentication.

Any 400 errors from this endpoint should be shown to the user.

This endpoint falls under the `self` ratelimit bucket.
The `self` bucket has a ratelimit of {__config['ratelimits']['self']}

Version added: 4.0
"""

@router.patch("/users/@me")
@openapi.instance.route(openapi.Route(
    "/users/@me",
    "PATCH",
    "Update Self",
    ["users"],
    None,
    [
        openapi.RouteParameter("New Handle", "string", "handle", True, "query")
    ],
    {
        204: openapi.Response("Success", None),
        401: openapi.UnauthorizedResponse
    },
    description=desc,
    is_body_required=False
))
@limit("self")
async def update_self(
    request: MystbinRequest,
) -> Response:
    user = request.state.user
    if not user:
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)

    try:
        handle = request.query_params["handle"].strip()
    except:
        return VariableResponse({"error": "Missing 'handle' query parameter"}, request, status_code=400)
    
    exc: str = ""

    if len(handle) > 32:
        exc += "Handle must be less that 32 characters. "
    if handle.lower() != handle:
        exc += "Handle must be lower cased. "
    if handle.replace(" ", "-") != handle:
        exc += "Handle cannot have spaces. "
    if handle in request.app.config.get("banned_handles", ()):
        exc += "Handle is unavailable. "
    if any(x in handle for x in "!@#$%^&*(){}[]+=<>,/?\\'\""): # slow but neccesary
        exc += "Handle cannot contain special characters. "
    
    if exc:
        return VariableResponse({"error": exc}, request, status_code=400)
    
    status = await request.app.state.db.update_user_handle(user["id"], handle)

    if not status:
        return VariableResponse({"error": "Handle is unavailable"}, request, status_code=400)

    return Response(status_code=204)


desc = f"""Deletes the authorized user's account.
* Required authentication.

This endpoint falls under the `self` ratelimit bucket.
The `self` bucket has a ratelimit of {__config['ratelimits']['self']}.
Not that it matters after deleting your account.
"""

@router.delete("/users/@me")
@openapi.instance.route(openapi.Route(
    "/users/@me",
    "DELETE",
    "Delete Self",
    ["users"],
    None,
    [],
    {
        204: openapi.Response("Deleted", None),
        401: openapi.UnauthorizedResponse
    },
    description=desc,
    is_body_required=False
))
@limit("self")
async def delete_self(request: MystbinRequest) -> Response:
    user = request.state.user
    if not user:
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)

    await request.app.state.db.delete_user(user["id"], True) # TODO: do we want to allow deletion of all pastes tied to account?
    return Response(status_code=204)
    


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
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)
    
    try:
        _data = await request.body()
    except:
        return VariableResponse({"error": "Bad body"}, request, status_code=400)
    
    bookmark = payloads.create_struct_from_payload(_data, payloads.BookmarkPutDelete)

    try:
        await request.app.state.db.create_bookmark(request.state.user["id"], bookmark.paste_id)
        return Response(status_code=204)
    except ValueError as e:
        return VariableResponse({"error": e.args[0]}, request, status_code=400)


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
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)
    
    payload = await request.body()

    try:
        bookmark = payloads.create_struct_from_payload(payload, payloads.BookmarkPutDelete)
    except (msgspec.DecodeError, msgspec.ValidationError) as e:
        return VariableResponse({"error": e.args[0]}, request, status_code=400)

    if not await request.app.state.db.delete_bookmark(request.state.user["id"], bookmark.paste_id):
        return VariableResponse({"error": "Bookmark does not exist"}, request, status_code=400)
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
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)

    data = await request.app.state.db.get_bookmarks(request.state.user["id"])
    return VariableResponse({"bookmarks": data}, request)


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
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)
    
    data = await request.app.state.db.get_tokens(request.state.user["id"])
    return VariableResponse(responses.TokenList([responses.TokenListItem(
        id=x["id"],
        name=x["token_name"],
        description=x["token_description"],
        is_web_token=x["is_main"])
        for x in data]
    ), request)


desc = f"""Regenerates a token under your account.
* Required authentication.

This endpoint falls under the `tokengen` ratelimit bucket.
The `tokengen` bucket has a ratelimit of {__config['ratelimits']['tokengen']}

Version changed: 4.0

Changed in version 4.0:
- endpoint moved from /users/regenerate to /users/tokens
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
async def regen_token(request: MystbinRequest) -> VariableResponse:
    if not request.state.user:
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)
    
    try:
        token_id = int(request.query_params["token_id"])
    except:
        return VariableResponse({"error": "bad query parameter 'token_id'"}, request, status_code=400)

    token: str | None = await request.app.state.db.regen_token(userid=request.state.user["id"], token_id=token_id)
    if not token:
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)

    return VariableResponse({"token": token}, request)


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
async def delete_token(request: MystbinRequest) -> VariableResponse:
    if not request.state.user:
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)
    
    try:
        _body = await request.body()
        data = payloads.create_struct_from_payload(_body, payloads.TokenPost)
    except (msgspec.DecodeError, msgspec.ValidationError) as e:
        return VariableResponse({"error": e.args[0]}, request, status_code=400)
    except:
        return VariableResponse({"error": "bad body passed"}, request, status_code=400)

    resp = await request.app.state.db.create_token(request.state.user["id"], data.name, data.description)
    if resp is None:
        return VariableResponse({"error": "Name or description are not within permitted lengths"}, request, status_code=400)
    
    return VariableResponse({"name": data.name, "id": resp[1], "token": resp[0]}, request)


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
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)
    
    try:
        token_id = int(request.query_params["token_id"])
    except:
        return VariableResponse({"error": "bad query parameter 'token_id'"}, request, status_code=400)

    if await request.app.state.db.delete_token(request.state.user["id"], token_id=token_id):
        return Response(status_code=204)
    
    return VariableResponse({"error": "Unauthorized"}, request, status_code=401)

desc = f"""Gets all pastes associated with a token.
* Required authentication.

This endpoint falls under the `self` ratelimit bucket.
The `self` bucket has a ratelimit of {__config['ratelimits']['self']}

Version added: 4.0
"""

@router.get("/users/@token")
@openapi.instance.route(openapi.Route(
    "/users/@token",
    "GET",
    "Get Token Pastes",
    ["users", "pastes"],
    None,
    [
        openapi.RouteParameter("Token ID", "integer", "token_id", True, "query")
    ],
    {
        200: openapi.Response("Success", openapi.PasteGetAllResponse),
        400: openapi.BadRequestResponse,
        401: openapi.UnauthorizedResponse,
        403: openapi.ForbiddenResponse
    },
    description=desc,
    is_body_required=False
))
@limit("self")
async def get_pastes_for_token(request: MystbinRequest) -> VariableResponse:
    if not request.state.user:
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)
    
    try:
        token_id = int(request.query_params["token_id"])
    except:
        return VariableResponse({"error": "bad query parameter 'token_id'"}, request, status_code=400)
    
    pastes = await request.app.state.db.get_token_pastes(request.state.user["id"], token_id)
    if pastes is None:
        return VariableResponse({"error": "Token ID was not created by the requesting user"}, request, status_code=403)
    
    return VariableResponse(responses.PasteGetAllResponse(pastes=pastes), request)


desc = f"""Gets all pastes from a user.
* Required authentication.

This endpoint fetches all pastes from a user.
If you are fetching your own pastes, this will return both public and private pastes.
Otherwise, it will only return public pastes.

This endpoint falls under the `getpastes` ratelimit bucket.
The `getpaste` bucket has a ratelimit of {__config['ratelimits']['getpaste']}

Version added: 4.0
"""

@router.get("/users/{handle:str}/pastes")
@openapi.instance.route(openapi.Route(
    "/users/{handle}/pastes",
    "GET",
    "Get User Pastes",
    ["users", "pastes"],
    None,
    [
        openapi.RouteParameter("User's Handle", "string", "handle", True, "path"),
        openapi.RouteParameter("Page", "integer", "page", True, "query"),
        openapi.RouteParameter("Show private pastes", "boolean", "private", False, "query")
    ],
    {
        200: openapi.Response("Success", openapi.PasteGetAllResponse),
        400: openapi.BadRequestResponse,
        403: openapi.ForbiddenResponse
    },
    description=desc,
    is_body_required=False
))
@limit("getpaste")
async def get_user_pastes(request: MystbinRequest) -> VariableResponse:
    handle = request.path_params["handle"]
    try:
        page = int(request.query_params["page"])
    except KeyError:
        page = 1
    except:
        return VariableResponse({"error": "Invalid 'page' parameter provided"}, request, status_code=400)
    
    try:
        private = request.query_params["private"] in ("1", "y", "true", "t", "yes")
    except KeyError:
        private = False
    except:
        return VariableResponse({"error": "Invalid 'private' parameter provided"}, request, status_code=400)
    
    if private and (not request.state.user or request.state.user["handle"] != handle):
        return VariableResponse({"error": "Cannot fetch another user's private pastes"}, request, status_code=400)

    pastes = await request.app.state.db.get_all_user_pastes(None, 50, page, author_handle=handle, public_only=not private)

    return VariableResponse(responses.PasteGetAllResponse(pastes=pastes), request)


desc = f"""Gets the custom style the user has set.
* Required authentication.

This endpoint falls under the `self` ratelimit bucket.
The `self` bucket has a ratelimit of {__config['ratelimits']['self']}

Version added: 4.0
"""

@router.get("/users/style")
@openapi.instance.route(openapi.Route(
    "/users/style",
    "GET",
    "Get Custom Styles",
    ["users"],
    None,
    [],
    {
        200: openapi.Response("Success", openapi.Style),
        204: openapi.Response("No Style", None),
        401: openapi.UnauthorizedResponse
    },
    description=desc,
    is_body_required=False
))
@limit("self")
async def get_user_style(request: MystbinRequest) -> Response | VariableResponse:
    if not request.state.user:
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)
    
    style = await request.app.state.db.get_user_style(request.state.user["id"])
    if style is None:
        return Response(status_code=204)
    
    return VariableResponse(style, request)


desc = f"""Allows the user to set a custom style that will show up on the frontend.
* Required authentication.

This endpoint falls under the `self` ratelimit bucket.
The `self` bucket has a ratelimit of {__config['ratelimits']['self']}

Version added: 4.0
"""

@router.post("/users/style")
@openapi.instance.route(openapi.Route(
    "/users/style",
    "POST",
    "Set Custom Style",
    ["users"],
    openapi.Style,
    [],
    {
        204: openapi.Response("Success", None),
        400: openapi.BadRequestResponse,
        401: openapi.UnauthorizedResponse
    },
    description=desc,
    is_body_required=False
))
@limit("self")
async def set_user_style(request: MystbinRequest) -> Response | VariableResponse:
    if not request.state.user:
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)

    try:    
        style = payloads.create_struct_from_payload(await request.body(), responses.Style)
    except msgspec.DecodeError as e:
        return VariableResponse({"error": e.args[0]}, request, status_code=400)
    
    style = await request.app.state.db.set_user_style(request.state.user["id"], style)
    return Response(status_code=204)
