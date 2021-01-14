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

from asyncpg import Record
from fastapi import APIRouter, Depends, Request
from fastapi.responses import UJSONResponse
from fastapi.security import HTTPBearer
from models import errors, responses
from utils.ratelimits import limit

router = APIRouter()
auth_model = HTTPBearer()


@router.get(
    "/users/me",
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
    request: Request, authorization: str = Depends(auth_model)
) -> Union[UJSONResponse, Dict[str, Union[str, int, bool]]]:
    """Gets the User object of the currently logged in user.
    * Requires authentication.
    """

    user = request.state.user
    if not user:
        return UJSONResponse({"error": "Forbidden"}, status_code=403)

    return UJSONResponse(responses.User(**user).dict())


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
async def regen_token(
    request: Request, authorization: str = Depends(auth_model)
) -> Union[UJSONResponse, Dict[str, str]]:
    """Regens the user's token.
    * Requires authentication.
    """
    if not request.state.user:
        return UJSONResponse({"error": "Forbidden"}, status_code=403)

    token: Optional[str] = await request.app.state.db.regen_token(
        userid=request.state.user['id']
    )
    if not token:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    return {"token": token}
