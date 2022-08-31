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

import datetime
import pathlib
import subprocess
from hashlib import sha256
from hmac import HMAC, compare_digest

import psutil
import ujson
from asyncpg import Record
from fastapi import APIRouter
from fastapi.responses import Response, UJSONResponse
from models import errors, responses

from mystbin_models import MystbinRequest
from utils.db import _recursive_hook as recursive_hook
from utils.ratelimits import limit


router = APIRouter()


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
    include_in_schema=False,
)
@limit("admin")
async def get_any_user(request: MystbinRequest, user_id: int) -> UJSONResponse | dict[str, str]:
    """Returns the User object of the passed user_id.
    * Requires admin authentication.
    """
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    data: Record | int | None = await request.app.state.db.get_user(user_id=user_id)
    if data and not isinstance(data, int):
        return UJSONResponse(dict(data))
    return UJSONResponse({"error": "The given user was not found"}, status_code=400)


@router.post("/admin/users/{user_id}/ban", tags=["admin"], include_in_schema=False)
@limit("admin")
async def ban_user(
    request: MystbinRequest,
    user_id: int,
    ip: str | None = None,
    reason: str | None = None,
) -> UJSONResponse:
    """
    Bans a user from the service
    * Requires admin authentication
    """
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    success = await request.app.state.db.ban_user(user_id, ip, reason)
    return UJSONResponse({"success": success})


@router.post("/admin/users/{user_id}/unban", tags=["admin"], include_in_schema=False)
@limit("admin")
async def unban_user(
    request: MystbinRequest,
    user_id: int,
    ip: str | None = None,
) -> UJSONResponse:
    """
    Unbans a user from the service
    * Requires admin authentication
    """
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    success = await request.app.state.db.unban_user(user_id, ip)
    return UJSONResponse({"success": success})


@router.post("/admin/users/{user_id}/subscribe", tags=["admin"], include_in_schema=False)
@limit("admin")
async def subscribe_user(request: MystbinRequest, user_id: int) -> UJSONResponse:
    """
    Gives a user subscriber access
    * Requires admin authentication
    """
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    success = await request.app.state.db.toggle_subscription(user_id, True)
    return UJSONResponse({"success": success})


@router.post("/admin/users/{user_id}/unsubscribe", tags=["admin"], include_in_schema=False)
@limit("admin")
async def unsubscribe_user(request: MystbinRequest, user_id: int) -> UJSONResponse:
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
    response_model=responses.Userlist,
    responses={200: {"model": responses.Userlist}, 401: {"model": errors.Unauthorized}},
    include_in_schema=False,
)
@limit("admin")
async def get_admin_userlist(request: MystbinRequest, page: int = 1):
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
    "/admin/users/count",
    tags=["admin"],
    response_model=responses.UserCount,
    responses={
        200: {"model": responses.UserCount},
        401: {"model": errors.Unauthorized},
    },
    include_in_schema=False,
)
@limit("admin")
async def get_admin_usercount(request: MystbinRequest):
    """
    Returns a count of how many users there are
    * Requires admin authentication.
    """
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    count = await request.app.state.db.get_admin_usercount()
    return UJSONResponse({"count": count})


@router.get("/admin/bans", tags=["admin"], include_in_schema=False)
@limit("admin")
async def search_bans(request: MystbinRequest, search: str | None = None, page: int = 1):
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    if search is not None:
        data = await request.app.state.db.search_bans(search=search)
        if isinstance(data, str):
            return UJSONResponse({"reason": data, "searches": []})

        return UJSONResponse({"reason": None, "searches": data})
    else:
        return UJSONResponse(await request.app.state.db.get_bans(page))


@router.post("/admin/bans", tags=["admin"], include_in_schema=False)
@limit("admin")
async def post_ban(
    request: MystbinRequest,
    reason: str,
    ip: str | None = None,
    userid: int | None = None,
):
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    data = await request.app.state.db.ban_user(ip=ip, userid=userid, reason=reason)
    return UJSONResponse({"success": data})


@router.delete("/admin/bans", tags=["admin"], include_in_schema=False)
@limit("admin")
async def remove_ban(request: MystbinRequest, ip: str | None = None, userid: int | None = None) -> UJSONResponse | Response:
    if not ip and not userid:
        return UJSONResponse({"error": "Bad Request"}, status_code=400)

    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    if await request.app.state.db.unban_user(userid, ip):
        return Response(status_code=204)

    return Response(status_code=400)


@router.get("/admin/stats", tags=["admin"], include_in_schema=False)
@limit("admin")
async def get_server_stats(request: MystbinRequest):
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    data = {
        "memory": PROC.memory_full_info().uss / 1024**2,
        "memory_percent": PROC.memory_percent(memtype="uss"),
        "cpu_percent": PROC.cpu_percent(),
        "uptime": (datetime.datetime.utcnow() - START_TIME).total_seconds(),
        "total_pastes": await request.app.state.db.get_paste_count(),
        "requests": request.app.state.request_stats["total"],
        "latest_request": request.app.state.request_stats["latest"].isoformat(),
    }

    return UJSONResponse(data, status_code=200)


@router.post("/admin/release_hook", tags=["admin"], include_in_schema=False)
@limit("admin")
async def release_hook(request: MystbinRequest):

    config = pathlib.Path("config.json")
    if not config.exists():
        config = pathlib.Path("../../config.json")

    with open(config) as f:
        config = ujson.load(f)

    SECRET = config["github_secret"].encode()

    received_sign = request.headers.get("X-Hub-Signature-256").split("sha256=")[-1].strip()
    expected_sign = HMAC(key=SECRET, msg=await request.body(), digestmod=sha256).hexdigest()
    if not compare_digest(received_sign, expected_sign):
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    command = "cd /root/MystBin/; git pull;"
    subprocess.run(command, stdout=subprocess.PIPE, shell=True)

    return Response(status_code=200)


@router.get(
    "/admin/pastes/{paste_id}",
    tags=["admin"],
    response_model=responses.PasteGetResponse,
    responses={
        200: {"model": responses.PasteGetResponse},
        401: {"model": errors.Unauthorized},
        404: {"model": errors.NotFound},
    },
    name="Retrieve paste file(s)",
    include_in_schema=False,
)
@limit("admin")
async def get_paste(request: MystbinRequest, paste_id: str, password: str | None = None) -> Response:
    """Get a paste from MystBin."""
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    paste = await request.app.state.db.get_paste(paste_id, password)
    if paste is None:
        return Response(status_code=404)

    resp = responses.PasteGetResponse(**paste)
    return UJSONResponse(recursive_hook(resp.dict()))


@router.get("/admin/pastes", tags=["admin"], include_in_schema=False)
@limit("admin")
async def get_all_pastes(request: MystbinRequest, count: int, page: int = 0, oldest_first: bool = False):
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    if page < 0:
        return UJSONResponse({"error": "Page must be greater than 0"}, status_code=421)
    elif count < 1:
        return UJSONResponse({"error": "Count must be greater than 1"}, status_code=421)

    return UJSONResponse({"pastes": await request.app.state.db.get_all_pastes(page, count, reverse=oldest_first)})
