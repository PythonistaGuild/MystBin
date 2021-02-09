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

import yarl
from fastapi import APIRouter, Query, Request, Body
from fastapi.responses import UJSONResponse, Response
from models import responses
from utils.ratelimits import limit

router = APIRouter()

@router.post(
    "/users/connect/discord", response_model=responses.TokenResponse, include_in_schema=False
)
@limit("apps", "zones.apps")
async def auth_from_discord(
    request: Request, code: str = Body(None)
) -> Union[Dict[str, str], UJSONResponse]:
    """Allows user to authenticate from Discord OAuth."""
    if not code:
        return UJSONResponse({"error": "Missing code query"}, status_code=400)

    client_id = request.app.config["apps"]["discord_application_id"]
    client_secret = request.app.config["apps"]["discord_application_secret"]
    url = yarl.URL(request.app.config["site"]["base_site"]).with_path("/users/connect/discord")

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": url,
        "scope": "identify email",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with request.app.state.client.post(
        "https://discord.com/api/v8/oauth2/token", data=data, headers=headers
    ) as resp:
        data = await resp.json()
        token = data["access_token"]

    async with request.app.state.client.get(
        "https://discord.com/api/v8/users/@me",
        headers={"Authorization": f"Bearer {token}"},
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()
        userid = int(data["id"])
        email = data["email"]

    if request.state.user is not None:
        token = await request.app.state.db.update_user(
            request.state.user['id'], discord_id=userid, email=email
        )
        return {"token": token}

    else:
        data = await request.app.state.db.new_user(email, userid)
        return UJSONResponse({"token": data["token"]})


@router.post(
    "/users/connect/google", response_model=responses.TokenResponse, include_in_schema=False
)
@limit("apps", "zones.apps")
async def auth_from_google(
    request: Request, code: str = Body(None)
) -> Union[Dict[str, str], UJSONResponse]:
    """Allows user to authenticate from Google OAuth."""
    if not code:
        return UJSONResponse({"error": "Missing code query"}, status_code=400)

    client_id = request.app.config["apps"]["google_application_id"]
    client_secret = request.app.config["apps"]["google_application_secret"]
    url = yarl.URL(request.app.config["site"]["base_site"]).with_path("/users/connect/google")

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": url,
        "grant_type": "authorization_code",
        "code": code,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with request.app.state.client.post(
        "https://oauth2.googleapis.com/token", data=data, headers=headers
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()
        token = data["access_token"]

    async with request.app.state.client.get(
        "https://www.googleapis.com/userinfo/v2/me",
        headers={"Authorization": f"Bearer {token}"},
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()
        email = data["email"]
        userid = data["id"]


    if request.state.user is not None:
        token = await request.app.state.db.update_user(
            request.state.user['id'], google_id=userid, email=email
        )
        return UJSONResponse({"token": token})

    else:
        data = await request.app.state.db.new_user(email, google_id=userid)
        return UJSONResponse({"token": data["token"]})


@router.post(
    "/users/connect/github",
    response_model=responses.TokenResponse,
    include_in_schema=False,
)
@limit("apps", "zones.apps")
async def auth_from_github(
    request: Request, code: str = Body(None)
) -> Union[Dict[str, str], UJSONResponse]:
    """Allows user to authenticate with GitHub OAuth."""
    if not code:
        return UJSONResponse({"error": "Missing code query"}, status_code=400)

    client_id = request.app.config["apps"]["github_application_id"]
    client_secret = request.app.config["apps"]["github_application_secret"]
    url = yarl.URL(request.app.config["site"]["base_site"]).with_path("/users/connect/github")

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
        token = await request.app.state.db.update_user(
            request.state.user['id'], github_id=userid, email=email
        )
        return UJSONResponse({"token": token})

    else:
        data = await request.app.state.db.new_user(email, github_id=userid)
        return UJSONResponse({"token": data["token"]})

@router.post("/callbacks/sentry", include_in_schema=False)
@limit("sentry")
async def sentry_callback(request: Request):
    data = await request.json()
    if not request.app.config['sentry']['discord_webhook']:
        return Response(status_code=204)

    v = await request.app.state.client.post(request.app.config['sentry']['discord_webhook'], json={"text": str(data)})
    v.raise_for_status()
    v.close()
    return Response(status_code=204)