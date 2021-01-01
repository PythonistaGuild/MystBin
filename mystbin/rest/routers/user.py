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
from typing import Dict, Union

from asyncpg import Record
from fastapi import APIRouter, Depends, Request
from fastapi.responses import UJSONResponse
from fastapi.security import HTTPBearer

from models import errors, responses

router = APIRouter()
auth_model = HTTPBearer()


@router.get("/user", tags=["users"], response_model=responses.User, responses={
    200: {"model": responses.User},
    401: {"model": errors.Unauthorized},
    403: {"model": errors.Forbidden}},
    name="Get current user"
)
async def get_self(request: Request, authorization: str = Depends(auth_model)) -> Union[UJSONResponse, Dict[str, Union[str, int, bool]]]:
    """Gets the User object of the currently logged in user.
    * Requires authentication.
    """
    if not authorization:
        return UJSONResponse({"error": "Forbidden"}, status_code=403)

    data: Union[Record, int] = await request.app.state.db.get_user(token=authorization.credentials)
    if not data or data in {400, 401}:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    return dict(data)


@router.post("/user/token-gen", tags=['users'], response_model=responses.TokenResponse, responses={
    200: {"model": responses.TokenResponse},
    401: {"model": errors.Unauthorized},
    403: {"model": errors.Forbidden}},
    name="Regenerate your token"
)
async def regen_token(request: Request, authorization: str = Depends(auth_model)) -> Union[UJSONResponse, Dict[str, str]]:
    """Regens the user's token.
    * Requires authentication.
    """
    if not authorization:
        return UJSONResponse({"error": "Forbidden"}, status_code=403)

    token: Optional[str] = await request.app.state.db.regen_token(token=authorization.credentials)
    if not token:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    return {"token": token}
