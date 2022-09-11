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
from typing import Dict, Optional, Union

from fastapi import APIRouter
from fastapi.responses import Response, UJSONResponse
from models import errors, payloads, responses

from mystbin_models import MystbinRequest
from utils.ratelimits import limit


router = APIRouter()


@router.get(
    "/users/@me",
    tags=["users"],
    response_model=responses.User,
    responses={
        200: {"model": responses.User},
        401: {"model": errors.Unauthorized},
        403: {"model": errors.Forbidden},
    },
    name="Get current user",
)
@limit("self")
async def get_self(
    request: MystbinRequest,
) -> Union[UJSONResponse, Dict[str, Union[str, int, bool]]]:
    """Gets the User object of the currently logged in user.
    * Requires authentication.
    """

    user = request.state.user
    if not user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    data = responses.User(**user).dict()
    return UJSONResponse(data)


@router.post(
    "/users/regenerate",
    tags=["users"],
    response_model=responses.TokenResponse,
    responses={
        200: {"model": responses.TokenResponse},
        401: {"model": errors.Unauthorized},
        403: {"model": errors.Forbidden},
    },
    name="Regenerate your token",
)
@limit("tokengen")
async def regen_token(request: MystbinRequest) -> Union[UJSONResponse, Dict[str, str]]:
    """Regens the user's token.
    * Requires authentication.
    """
    if not request.state.user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    token: Optional[str] = await request.app.state.db.regen_token(userid=request.state.user["id"])
    if not token:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    return UJSONResponse({"token": token})


@router.put(
    "/users/bookmarks",
    tags=["users"],
    responses={
        201: {"description": "Created bookmark"},
        400: {"model": errors.BadRequest},
        401: {"model": errors.Unauthorized},
        403: {"model": errors.Forbidden},
    },
)
@limit("bookmarks")
async def create_bookmark(request: MystbinRequest, bookmark: payloads.BookmarkPutDelete) -> Response:
    """Creates a bookmark on the authorized user's account
    * Requires authentication.
    """
    if not request.state.user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        await request.app.state.db.create_bookmark(request.state.user["id"], bookmark.paste_id)
        return Response(status_code=201)
    except ValueError as e:
        return UJSONResponse({"error": e.args[0]}, status_code=400)


@router.delete(
    "/users/bookmarks",
    tags=["users"],
    responses={
        204: {"description": "Deleted bookmark"},
        400: {"model": errors.BadRequest},
        401: {"model": errors.Unauthorized},
        403: {"model": errors.Forbidden},
    },
)
@limit("bookmarks")
async def delete_bookmark(request: MystbinRequest, bookmark: payloads.BookmarkPutDelete) -> Response:
    """Deletes a bookmark on the authorized user's account
    * Requires authentication.
    """
    if not request.state.user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    if not await request.app.state.db.delete_bookmark(request.state.user["id"], bookmark.paste_id):
        return UJSONResponse({"error": "Bookmark does not exist"}, status_code=400)
    else:
        return Response(status_code=204)


@router.get(
    "/users/bookmarks",
    tags=["users"],
    response_model=responses.Bookmarks,
    responses={
        200: {"model": responses.Bookmarks},
        400: {"model": errors.BadRequest},
        401: {"model": errors.Unauthorized},
        403: {"model": errors.Forbidden},
    },
)
@limit("bookmarks")
async def get_bookmarks(request: MystbinRequest):
    """Fetches all of the authorized users bookmarks
    * Requires authentication
    """
    if not request.state.user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    data = await request.app.state.db.get_bookmarks(request.state.user["id"])
    return UJSONResponse({"bookmarks": data})
