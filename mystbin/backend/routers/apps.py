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

import yarl

from mystbin_models import MystbinRequest
from utils.embed import Embed
from utils.responses import Response, UJSONResponse
from utils.ratelimits import limit
from utils.router import Router
from utils import openapi


router = Router()

ConnectBody = openapi._Component("ConnectBody", [openapi.ComponentProperty("code", "Auth Code", "string", "OAuth", True)], example={"code": "akopfmk334b56jo"})

@limit("apps")
@router.post("/users/connect/discord")
@openapi.instance.route(openapi.Route(
    "/users/connect/discord",
    "POST",
    "Connect Discord",
    ["users"],
    ConnectBody,
    [],
    {
        200: openapi.Response("Success", openapi.TokenResponse),
        400: openapi.BadRequestResponse,
        401: openapi.UnauthorizedResponse
    },
    is_body_required=True,
    exclude_from_default_schema=True
))
async def auth_from_discord(request: MystbinRequest) -> dict[str, str | None] | UJSONResponse:
    """Allows user to authenticate from Discord OAuth."""
    try:
        data = await request.json()
        code = data.get("code", None)
    except:
        return UJSONResponse({"error": "Bad JSON body passed"}, status_code=421)

    if not code:
        return UJSONResponse({"error": "Missing code query"}, status_code=400)

    client_id = request.app.config["apps"]["discord_application_id"]
    client_secret = request.app.config["apps"]["discord_application_secret"]
    url = yarl.URL(request.app.config["site"]["frontend_site"]).with_path("/discord_auth")

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": url,
        "scope": "identify email",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with request.app.state.client.post("https://discord.com/api/v8/oauth2/token", data=data, headers=headers) as resp:
        data = await resp.json()
        token = data["access_token"]

    async with request.app.state.client.get(
        "https://discord.com/api/v8/users/@me",
        headers={"Authorization": f"Bearer {token}"},
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()
        userid = data["id"]
        email = [data["email"]]
        username = f"{data['username']}#{data['discriminator']}"

    if request.state.user is not None:
        token = await request.app.state.db.update_user(request.state.user["id"], discord_id=userid, emails=email)
        return {"token": token}

    elif _id := await request.app.state.db.check_email(email):
        token = await request.app.state.db.update_user(_id, discord_id=userid, emails=email)
        return {"token": token}

    else:
        data = await request.app.state.db.new_user(email, username, userid)
        return {"token": data["token"]}


@router.post("/users/connect/google")
@openapi.instance.route(openapi.Route(
    "/users/connect/google",
    "POST",
    "Connect Google",
    ["users"],
    ConnectBody,
    [],
    {
        200: openapi.Response("Success", openapi.TokenResponse),
        400: openapi.BadRequestResponse,
        401: openapi.UnauthorizedResponse
    },
    is_body_required=True,
    exclude_from_default_schema=True
))
@limit("apps")
async def auth_from_google(request: MystbinRequest) -> dict[str, str] | UJSONResponse:
    """Allows user to authenticate from Google OAuth."""
    try:
        data = await request.json()
        code = data.get("code", None)
    except:
        return UJSONResponse({"error": "Bad JSON body passed"}, status_code=421)

    if not code:
        return UJSONResponse({"error": "Missing code query"}, status_code=400)

    client_id = request.app.config["apps"]["google_application_id"]
    client_secret = request.app.config["apps"]["google_application_secret"]
    url = yarl.URL(request.app.config["site"]["frontend_site"]).with_path("/google_auth")

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": url,
        "grant_type": "authorization_code",
        "code": code,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with request.app.state.client.post("https://oauth2.googleapis.com/token", data=data, headers=headers) as resp:
        resp.raise_for_status()
        data = await resp.json()
        token = data["access_token"]

    async with request.app.state.client.get(
        "https://www.googleapis.com/userinfo/v2/me",
        headers={"Authorization": f"Bearer {token}"},
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()
        email = [data["email"]]
        userid = data["id"]
        username = data.get("name") or data["email"].split("@")[0]

    if request.state.user is not None:
        token = await request.app.state.db.update_user(request.state.user["id"], google_id=userid, emails=email)
        return UJSONResponse({"token": token})

    elif _id := await request.app.state.db.check_email(email):
        token = await request.app.state.db.update_user(_id, google_id=userid, emails=email)
        return UJSONResponse({"token": token})

    else:
        data = await request.app.state.db.new_user(email, username, google_id=userid)
        return UJSONResponse({"token": data["token"]})


@router.post("/users/connect/github")
@openapi.instance.route(openapi.Route(
    "/users/connect/github",
    "POST",
    "Connect Github",
    ["users"],
    ConnectBody,
    [],
    {
        200: openapi.Response("Success", openapi.TokenResponse),
        400: openapi.BadRequestResponse,
        401: openapi.UnauthorizedResponse
    },
    is_body_required=True,
    exclude_from_default_schema=True
))
@limit("apps")
async def auth_from_github(request: MystbinRequest) -> Response | UJSONResponse:
    """Allows user to authenticate with GitHub OAuth."""
    try:
        data = await request.json()
        code = data.get("code", None)
    except:
        return UJSONResponse({"error": "Bad JSON body passed"}, status_code=421)

    if not code:
        return UJSONResponse({"error": "Missing code query"}, status_code=400)

    client_id = request.app.config["apps"]["github_application_id"]
    client_secret = request.app.config["apps"]["github_application_secret"]
    url = yarl.URL(request.app.config["site"]["frontend_site"]).with_path("/github_auth")

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": url,
        "grant_type": "authorization_code",
        "code": code,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    async with request.app.state.client.post(
        "https://github.com/login/oauth/access_token", data=data, headers=headers
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()
        token = data["access_token"]

    async with request.app.state.client.get(
        "https://api.github.com/user", headers={"Authorization": f"Bearer {token}"}
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()
        userid = data["id"]
        username = data["name"] or data["login"]

    async with request.app.state.client.get(
        "https://api.github.com/user/emails",
        headers={"Authorization": f"Bearer {token}"},
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()
        email = []
        for entry in data:
            if "users.noreply.github.com" in entry["email"]:
                continue

            email.append(entry["email"])

    if request.state.user is not None:
        token = await request.app.state.db.update_user(request.state.user["id"], github_id=userid, emails=email)
        return UJSONResponse({"token": token})

    elif _id := await request.app.state.db.check_email(email):
        token = await request.app.state.db.update_user(_id, github_id=userid, emails=email)
        return UJSONResponse({"token": token})

    else:
        data = await request.app.state.db.new_user(email, username, github_id=userid)
        return UJSONResponse({"token": data["token"]})


@router.delete("/users/connect/{app}")
@openapi.instance.route(openapi.Route(
    "/users/connect/{app}",
    "DELETE",
    "Delete Connection",
    ["users"],
    ConnectBody,
    [],
    {
        204: openapi.Response("Success", None),
        400: openapi.BadRequestResponse,
        401: openapi.UnauthorizedResponse
    },
    is_body_required=False,
    exclude_from_default_schema=True
))
@limit("apps")
async def disconnect_app(request: MystbinRequest):
    app: str = request.path_params["app"]
    
    if app not in ("github", "discord", "google"):
        return Response(status_code=404)

    if not request.state.user:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    if not await request.app.state.db.unlink_account(request.state.user["id"], app):
        return UJSONResponse({"error": "Account not linked"}, status_code=400)

    return Response(status_code=204)


@router.post("/callbacks/sentry")
@limit("sentry")
async def sentry_callback(request: MystbinRequest):
    data = await request.json()

    title = data["data"]["issue"]["title"]
    author = {"name": data["action"]}
    description = (
        f"Issue id: {data['data']['issue']['id']}\n"
        f"Times seen: {data['data']['issue']['count']}\n"
        f"Errored at: {data['data']['issue']['culprit']}"
    )
    timestamp = datetime.datetime.strptime(data["data"]["issue"]["lastSeen"], "%Y-%m-%dT%H:%M:%S.%fZ")
    footer = {
        "text": "Last seen at:",
        "icon_url": "https://cdn.discordapp.com/avatars/698366484975714355/9bad78779883b3bd6dfd4022d997e406.png",
    }

    embed = Embed(
        title=title,
        author=author,
        description=description,
        timestamp=timestamp,
        footer=footer,
    )

    if request.app.state.webhook_url:
        await request.app.state.client.post(request.app.state.webhook_url, json={"embeds": [embed.to_dict()]})

    return Response(status_code=204)
