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

import psutil
from asyncpg import Record
from utils.responses import Response, UJSONResponse
from models import responses
import msgspec

from mystbin_models import MystbinRequest
from utils.ratelimits import limit
from utils.router import Router
from utils import openapi


router = Router()


# Statistic consts
PROC = psutil.Process()
START_TIME = datetime.datetime.utcnow()

usernotfound = openapi._Component("ErrorUserNotFound", [openapi.ComponentProperty("error", "Error", "string", required=True)], {"error": "User Not Found"})


@router.get("/admin/users/{user_id:int}")
@openapi.instance.route(openapi.Route(
    "/admin/users/{user_id}",
    "GET",
    "Fetch any user",
    ["admin", "users"],
    None,
    [openapi.RouteParameter("User id", "integer", "user_id", True, "path")],
    {
        200: openapi.Response("User", openapi.User),
        400: openapi.Response("User Not Found", usernotfound),
        401: openapi.UnauthorizedResponse
    },
    is_body_required=False,
    exclude_from_default_schema=True
))
@limit("admin")
async def get_any_user(request: MystbinRequest) -> UJSONResponse:
    """Returns the User object of the passed user_id.
    * Requires admin authentication.
    """
    user_id: int = request.path_params["user_id"]

    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    data: Record | int | None = await request.app.state.db.get_user(user_id=user_id)
    if data and not isinstance(data, int):
        return UJSONResponse(dict(data))
    return UJSONResponse({"error": "The given user was not found"}, status_code=400)

_BanRouteSuccess = openapi._Component("BanRouteSuccess", [openapi.ComponentProperty("success", "Success", "boolean", None, True)], example={"success": True})

@router.post("/admin/users/{user_id:int}/ban")
@openapi.instance.route(openapi.Route(
    "/admin/users/{user_id}/ban",
    "POST",
    "Ban User",
    ["admin", "moderation"],
    None,
    [
        openapi.RouteParameter("User ID", "integer", "user_id", True, "path"),
        openapi.RouteParameter("IP Address", "string", "ip", False, "query"),
        openapi.RouteParameter("Reason", "string", "reason", False, "query"),
    ],
    {
        200: openapi.Response("Success", _BanRouteSuccess),
        400: openapi.Response("User Not Found", usernotfound),
        401: openapi.UnauthorizedResponse
    },
    is_body_required=False,
    exclude_from_default_schema=True
))
@limit("admin")
async def ban_user(request: MystbinRequest) -> UJSONResponse:
    """
    Bans a user from the service
    * Requires admin authentication
    """
    user_id: int = request.path_params["user_id"]
    ip: str | None = request.query_params.get("ip")
    reason: str | None = request.query_params.get("reason")

    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    success = await request.app.state.db.ban_user(user_id, ip, reason)
    return UJSONResponse({"success": success})


@router.post("/admin/users/{user_id:int}/unban")
@openapi.instance.route(openapi.Route(
    "/admin/users/{user_id}/unban",
    "POST",
    "Unban User",
    ["admin", "moderation"],
    None,
    [
        openapi.RouteParameter("User ID", "integer", "user_id", True, "path"),
        openapi.RouteParameter("IP Address", "string", "ip", False, "query")
    ],
    {
        200: openapi.Response("Success", _BanRouteSuccess),
        400: openapi.Response("User Not Found", usernotfound),
        401: openapi.UnauthorizedResponse
    },
    is_body_required=False,
    exclude_from_default_schema=True
))
@limit("admin")
async def unban_user(request: MystbinRequest) -> UJSONResponse:
    """
    Unbans a user from the service
    * Requires admin authentication
    """
    user_id: int = request.path_params["user_id"]
    ip: str | None = request.query_params.get("ip")

    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    success = await request.app.state.db.unban_user(user_id, ip)
    return UJSONResponse({"success": success})


@router.post("/admin/users/{user_id:int}/subscribe")
@openapi.instance.route(openapi.Route(
    "/admin/users/{user_id}/subscribe",
    "POST",
    "Subscribe User",
    ["admin"],
    None,
    [
        openapi.RouteParameter("User ID", "integer", "user_id", True, "path")
    ],
    {
        200: openapi.Response("Success", _BanRouteSuccess),
        401: openapi.UnauthorizedResponse
    },
    is_body_required=False,
    exclude_from_default_schema=True
))
@limit("admin")
async def subscribe_user(request: MystbinRequest) -> UJSONResponse:
    """
    Gives a user subscriber access
    * Requires admin authentication
    """
    user_id: int = request.path_params["user_id"]

    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    success = await request.app.state.db.toggle_subscription(user_id, True)
    return UJSONResponse({"success": success})


@router.post("/admin/users/{user_id:int}/unsubscribe")
@openapi.instance.route(openapi.Route(
    "/admin/users/{user_id}/unsubscribe",
    "POST",
    "Unsubscribe User",
    ["admin"],
    None,
    [
        openapi.RouteParameter("User ID", "integer", "user_id", True, "path")
    ],
    {
        200: openapi.Response("Success", _BanRouteSuccess),
        401: openapi.UnauthorizedResponse
    },
    is_body_required=False,
    exclude_from_default_schema=True
))
@limit("admin")
async def unsubscribe_user(request: MystbinRequest) -> UJSONResponse:
    """
    Revokes a users subscriber access
    * Requires admin authentication
    """
    user_id: int = request.path_params["user_id"]

    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    success = await request.app.state.db.toggle_subscription(user_id, False)
    return UJSONResponse({"success": success})


@router.get("/admin/users")
@openapi.instance.route(openapi.Route(
    "/admin/users",
    "GET",
    "Get Userlist",
    ["admin"],
    None,
    [openapi.RouteParameter("Page", "integer", "page", True, "query")],
    {
        200: openapi.Response("Success", openapi.AdminUserList),
        400: openapi.Response("Request Error", usernotfound),
        401: openapi.UnauthorizedResponse
    },
    is_body_required=False,
    exclude_from_default_schema=True
))
@limit("admin")
async def get_admin_userlist(request: MystbinRequest, page: int = 1) -> UJSONResponse:
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


@router.get("/admin/users/count")
@openapi.instance.route(openapi.Route(
    "/admin/users/count",
    "GET",
    "Get User Count",
    ["admin"],
    None,
    [],
    {
        200: openapi.Response("Success", openapi._Component("AdminUserCount", [openapi.ComponentProperty("count", "Count", "integer", required=True)], {"count": 100})),
        400: openapi.Response("Request Error", usernotfound),
        401: openapi.UnauthorizedResponse
    },
    is_body_required=False,
    exclude_from_default_schema=True
))
@limit("admin")
async def get_admin_usercount(request: MystbinRequest) -> UJSONResponse:
    """
    Returns a count of how many users there are
    * Requires admin authentication.
    """
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    count = await request.app.state.db.get_admin_usercount()
    return UJSONResponse({"count": count})


@router.get("/admin/bans")
@openapi.instance.route(openapi.Route(
    "/admin/bans",
    "GET",
    "Search Bans",
    ["admin", "moderation"],
    None,
    [openapi.RouteParameter("Page", "integer", "page", False, "query"), openapi.RouteParameter("Search", "string", "search", True, "query")],
    {
        200: openapi.Response("Success", openapi.AdminBanList),
        400: openapi.Response("Request Error", usernotfound),
        401: openapi.UnauthorizedResponse
    },
    is_body_required=False,
    exclude_from_default_schema=True
))
@limit("admin")
async def search_bans(request: MystbinRequest) -> UJSONResponse:
    search: str | None = request.query_params.get("search")
    try:
        page: int | None = int(request.query_params.get("page")) # type: ignore
    except:
        page = 1

    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    if search is not None:
        data = await request.app.state.db.search_bans(search=search)
        if isinstance(data, str):
            return UJSONResponse({"reason": data, "searches": []})

        return UJSONResponse({"reason": None, "searches": data})
    else:
        return UJSONResponse(await request.app.state.db.get_bans(page))


@router.post("/admin/bans")
@openapi.instance.route(openapi.Route(
    "/admin/bans",
    "POST",
    "Create Ban",
    ["admin", "moderation"],
    None,
    [
        openapi.RouteParameter("User ID", "integer", "userid", False, "query"),
        openapi.RouteParameter("IP Address", "string", "ip", False, "query"),
        openapi.RouteParameter("Reason", "string", "reason", True, "query")
    ],
    {
        200: openapi.Response("Success", openapi.AdminUserList),
        400: openapi.Response("Request Error", usernotfound),
        401: openapi.UnauthorizedResponse
    },
    is_body_required=False,
    exclude_from_default_schema=True
))
@limit("admin")
async def post_ban(request: MystbinRequest) -> UJSONResponse:
    try:
        reason: str = request.query_params["reason"]
    except:
        return UJSONResponse({"error": "No reason provided"}, status_code=400)
    
    try:
        userid: int | None = int(request.query_params["userid"])
    except:
        userid = None
    
    ip = request.query_params.get("ip")

    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    data = await request.app.state.db.ban_user(ip=ip, userid=userid, reason=reason)
    if data and request.app.redis:
        if ip is not None:
            await request.app.redis.set(f"ban-ip-{ip}", reason, ex=120)

    return UJSONResponse({"success": data})


@router.delete("/admin/bans")
@openapi.instance.route(openapi.Route(
    "/admin/bans",
    "DELETE",
    "Delete Ban",
    ["admin", "moderation"],
    None,
    [
        openapi.RouteParameter("User ID", "integer", "userid", False, "query"),
        openapi.RouteParameter("IP Address", "string", "ip", False, "query")
    ],
    {
        204: openapi.Response("Success", None),
        400: openapi.Response("Request Error", usernotfound),
        401: openapi.UnauthorizedResponse
    },
    is_body_required=False,
    exclude_from_default_schema=True
))
@limit("admin")
async def remove_ban(request: MystbinRequest) -> UJSONResponse | Response:
    ip: str | None = request.query_params.get("ip")
    try:
        userid: int | None = int(request.query_params.get("userid")) # type: ignore
    except:
        userid = None
    
    if not ip and not userid:
        return UJSONResponse({"error": "Bad Request"}, status_code=400)

    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    if await request.app.state.db.unban_user(userid, ip):
        if ip is not None and request.app.redis:
            await request.app.redis.set(f"ban-ip-{ip}", "", ex=120)

        return Response(status_code=204)

    return UJSONResponse({"error": "Ban not found"}, status_code=400)

@router.get("/admin/pastes/{paste_id:str}")
@openapi.instance.route(openapi.Route(
    "/admin/pastes/{paste_id}",
    "GET",
    "Get Paste",
    ["admin", "pastes"],
    None,
    [
        openapi.RouteParameter("Paste ID", "integer", "paste_id", True, "query")
    ],
    {
        200: openapi.Response("Success", openapi.PasteGetResponse),
        400: openapi.Response("Request Error", usernotfound),
        401: openapi.UnauthorizedResponse
    },
    is_body_required=False,
    exclude_from_default_schema=True
))
@limit("admin")
async def get_paste(request: MystbinRequest, paste_id: str) -> Response:
    """Get a paste from MystBin (admin)."""
    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    paste = await request.app.state.db.get_paste(paste_id, None)
    if paste is None:
        return Response(status_code=404)

    resp = responses.PasteGetResponse(**paste)
    return Response(msgspec.json.encode(resp))


@router.get("/admin/pastes")
@openapi.instance.route(openapi.Route(
    "/admin/pastes",
    "GET",
    "Get Pastes Overview",
    ["admin", "pastes"],
    None,
    [
        openapi.RouteParameter("Count Per Page", "integer", "count", True, "query"),
        openapi.RouteParameter("Page", "integer", "page", False, "query"),
        openapi.RouteParameter("Oldest First", "boolean", "oldest_first", False, "query")
    ],
    {
        200: openapi.Response("Success", openapi.PasteGetAllResponse),
        400: openapi.Response("Request Error", usernotfound),
        401: openapi.UnauthorizedResponse
    },
    is_body_required=False,
    exclude_from_default_schema=True
))
@limit("admin")
async def get_all_pastes(request: MystbinRequest) -> Response:
    """
    Get a short version of all pastes in the system
    """
    try:
        count: int = int(request.query_params["count"])
    except:
        return UJSONResponse({"error": "Count parameter not given"}, status_code=400)
    try:
        page: int = int(request.query_params["page"])
    except:
        page = 1
    try:
        _oldest_first: str | None = request.query_params.get("oldest_first")
        if not _oldest_first:
            oldest_first = False
        
        else:
            if _oldest_first.lower() in {"true", "1", "yes"}:
                oldest_first = True
            else:
                oldest_first = False
    except:
        oldest_first = False

    if not request.state.user or not request.state.user["admin"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    if page < 0:
        return UJSONResponse({"error": "Page must be greater than 0"}, status_code=421)
    elif count < 1:
        return UJSONResponse({"error": "Count must be greater than 1"}, status_code=421)

    return UJSONResponse({"pastes": await request.app.state.db.get_all_pastes(page, count, reverse=oldest_first)})
