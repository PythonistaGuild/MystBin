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
from typing import Union, Dict

from asyncpg import Record
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from models import Unauthorized, User


router = APIRouter()
auth_model = HTTPBearer()


@router.get("/admin/user/{user_id}", tags=["admin"], response_model=User, responses={
    200: {"model": User},
    401: {"model": Unauthorized}},
    include_in_schema=False
)
async def get_any_user(request: Request, user_id: int, authorization: str = Depends(auth_model)) -> Union[JSONResponse, Dict[str, str]]:
    """ Returns the User object of the passed user_id.
    * Requires admin authentication.
    """
    if not await request.app.state.db.ensure_admin(authorization.credentials):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    data: Union[Record, int] = await request.app.state.db.get_user(user_id)
    return dict(data)
