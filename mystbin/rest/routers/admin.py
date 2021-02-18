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
import datetime
from typing import Dict, Optional, Union

import psutil
from asyncpg import Record
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response, UJSONResponse
from fastapi.security import HTTPBearer
from models import errors, responses
from utils.ratelimits import limit

router = APIRouter()
auth_model = HTTPBearer()


# Statistic consts
PROC = psutil.Process()
START_TIME = datetime.datetime.utcnow()


@router.get(
    "/admin/users/{user_id}",
    tags=["admin"],
    response_model=responses.User,
    responses={
        200: {"model": responses.User},
        401: {"model": errors.Unauthorized},
        400: {"response": {"example": {"error": "The given user was not found"}}},
    },
    #    include_in_schema=False,
)
@limit("admin")
async def get_any_user(
    request: Request, user_id: int, authorization: str = Depends(auth_model)
) -> Union[UJSONResponse, Dict[str, str]]:
    """Returns the User object of the passed user_id.
    * Requires admin authentication.
    """
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    data: Optional[Union[Record, int]] = await request.app.state.db.get_user(
        user_id=user_id
    )
    if data:
        return UJSONResponse(dict(data))
    return UJSONResponse({"error": "The given user was not found"}, status_code=400)


@router.post(
    "/admin/users/{user_id}/ban",
    tags=["admin"],
    #             include_in_schema=False
)
@limit("admin", "admin")
async def ban_user(
    request: Request,
    user_id: int,
    ip: str = None,
    reason: str = None,
    authorization: str = Depends(auth_model),
) -> UJSONResponse:
    """
    Bans a user from the service
    * Requires admin authentication
    """
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    success = await request.app.state.db.ban_user(user_id, ip, reason)
    return UJSONResponse({"success": success})


@router.post(
    "/admin/users/{user_id}/unban",
    tags=["admin"],
    #             include_in_schema=False
)
@limit("admin", "admin")
async def unban_user(
    request: Request,
    user_id: int,
    ip: str = None,
    authorization: str = Depends(auth_model),
) -> UJSONResponse:
    """
    Unbans a user from the service
    * Requires admin authentication
    """
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    success = await request.app.state.db.unban_user(user_id, ip)
    return UJSONResponse({"success": success})


@router.post(
    "/admin/users/{user_id}/subscribe",
    tags=["admin"],
    #    include_in_schema=False
)
@limit("admin", "admin")
async def subscribe_user(
    request: Request, user_id: int, authorization: str = Depends(auth_model)
) -> UJSONResponse:
    """
    Gives a user subscriber access
    * Requires admin authentication
    """
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    success = await request.app.state.db.toggle_subscription(user_id, True)
    return UJSONResponse({"success": success})


@router.post(
    "/admin/users/{user_id}/unsubscribe",
    tags=["admin"],
    #    include_in_schema=False
)
@limit("admin", "admin")
async def unsubscribe_user(
    request: Request, user_id: int, authorization: str = Depends(auth_model)
) -> UJSONResponse:
    """
    Revokes a users subscriber access
    * Requires admin authentication
    """
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    success = await request.app.state.db.toggle_subscription(user_id, False)
    return UJSONResponse({"success": success})


@router.get(
    "/admin/users",
    tags=["admin"],
    response_model=responses.UserList,
    responses={200: {"model": responses.UserList}, 401: {"model": errors.Unauthorized}},
    #    include_in_schema=False,
)
@limit("admin", "admin")
async def get_admin_userlist(
    request: Request, page: int = 1, authorization: str = Depends(auth_model)
):
    """
    Returns a list of smaller user objects
    * Requires admin authentication.
    """
    if page < 1:
        return UJSONResponse({"error": "page must be >= 1"}, status_code=400)

    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    data = await request.app.state.db.get_admin_userlist(page)
    return UJSONResponse(data)


@router.get(
    "/admin/bans",
    tags=["admin"],
    #    include_in_schema=False
)
@limit("admin", "admin")
async def search_bans(request: Request, search: str = None, page: int = 1):
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    if search is not None:
        data = await request.app.state.db.search_bans(search=search)
        if isinstance(data, str):
            return UJSONResponse({"reason": data, "searches": []})

        return UJSONResponse({"reason": None, "searches": data})
    else:
        return UJSONResponse(await request.app.state.db.get_bans(page))


@router.post(
    "/admin/bans",
    tags=["admin"],
    #    include_in_schema=False
)
@limit("admin", "admin")
async def post_ban(request: Request, reason: str, ip: str = None, userid: int = None):
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    data = await request.app.state.db.ban_user(ip=ip, userid=userid, reason=reason)
    return UJSONResponse({"success": data})


@router.delete(
    "/admin/bans",
    tags=["admin"],
    #    include_in_schema=False
)
@limit("admin", "admin")
async def remove_ban(request: Request, ip: str = None, userid: int = None):
    if not ip and not userid:
        return UJSONResponse({"error": "Bad Request"}, status_code=400)

    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    if await request.app.state.db.unban_user(userid, ip):
        return Response(status_code=204)

    return Response(status_code=400)


@router.get(
    "/admin/recent",
    tags=["admin"],
    #    include_in_schema=False
)
@limit("admin", "admin")
async def get_recent_pastes(
    request: Request, offset: int = 0, oldest_first: bool = False
):
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    return UJSONResponse({"recent": await request.app.state.db.get_recent_pastes(offset, reverse=oldest_first)})


@router.get(
    "/admin/stats",
    tags=["admin"],
    #    include_in_schema=False
)
@limit("admin", "admin")
async def get_server_stats(request: Request):
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    data = {
        "memory": PROC.memory_full_info().uss / 1024 ** 2,
        "memory_percent": PROC.memory_percent(memtype="uss"),
        "cpu_percent": PROC.cpu_percent(),
        "uptime": (datetime.datetime.utcnow() - START_TIME).total_seconds(),
        "total_pastes": (await request.app.state.db.get_paste_count())[0]["count"],
        "requests": request.app.state.request_stats["total"],
        "latest_request": request.app.state.request_stats["latest"].isoformat(),
    }

    return UJSONResponse(data, status_code=200)
