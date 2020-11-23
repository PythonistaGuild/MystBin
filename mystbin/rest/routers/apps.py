
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
from fastapi import APIRouter, Query, Request
from fastapi.responses import UJSONResponse

from ..models import responses

router = APIRouter()


@router.get("/apps/discord", response_model=responses.TokenResponse, include_in_schema=False)
async def auth_from_discord(request: Request, code: str = Query(None), state: Optional[str] = Query(None)) -> Union[Dict[str, str], UJSONResponse]:
    """Allows user to authenticate from Discord OAuth."""
    if not code:
        return UJSONResponse({"error": "Missing code query"}, status_code=400)

    existing_user = state

    if existing_user:
        try:
            existing_user = int(existing_user)
        except TypeError:
            existing_user = None

    client_id = request.app.config['apps']['discord_application_id']
    client_secret = request.app.config['apps']['discord_application_secret']
    url = yarl.URL(request.app.config['site']
                   ['base_site']).with_path("/apps/discord")

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": url,
        "scope": "identify email"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with request.app.state.client.post("https://discord.com/api/v8/oauth2/token", data=data, headers=headers) as resp:
        data = await resp.json()
        token = data['access_token']

    async with request.app.state.client.get("https://discord.com/api/v8/users/@me", headers={"Authorization": f"Bearer {token}"}) as resp:
        resp.raise_for_status()
        data = await resp.json()
        userid = int(data['id'])
        email = data['email']

    exists = await request.app.state.db.check_email(email)
    if exists:
        existing_user = exists

    if existing_user:
        if not isinstance(existing_user, int):
            existing_user = await request.app.state.db.get_user(token=existing_user)

        if not existing_user or existing_user in (400, 401):
            existing_user = None

        else:
            token = await request.app.state.db.update_user(existing_user, discord_id=userid, email=email)
            if token is None:
                existing_user = None
            else:
                return {"token": token}

    if not existing_user:
        data = await request.app.state.db.new_user(email, userid)
        return {"token": data['token']}


@router.get("/apps/google", response_model=responses.TokenResponse, include_in_schema=False)
async def auth_from_google(request: Request, code: str = Query(None), state: Optional[str] = Query(None)) -> Union[Dict[str, str], UJSONResponse]:
    """Allows user to authenticate from Google OAuth."""
    if not code:
        return UJSONResponse({"error": "Missing code query"}, status_code=400)

    existing_user = state

    if existing_user:
        try:
            existing_user = int(existing_user)
        except TypeError:
            existing_user = None

    client_id = request.app.config['apps']['google_application_id']
    client_secret = request.app.config['apps']['google_application_secret']
    url = yarl.URL(request.app.config['site']
                   ['base_site']).with_path("/apps/google")

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": url,
        "grant_type": "authorization_code",
        "code": code
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with request.app.state.client.post("https://oauth2.googleapis.com/token", data=data, headers=headers) as resp:
        resp.raise_for_status()
        data = await resp.json()
        token = data['access_token']

    async with request.app.state.client.get("https://www.googleapis.com/userinfo/v2/me", headers={"Authorization": f"Bearer {token}"}) as resp:
        resp.raise_for_status()
        data = await resp.json()
        email = data['email']
        userid = data['id']

    await request.app.state.db.get_user(token=existing_user)

    exists = await request.app.state.db.check_email(email)
    if exists:
        existing_user = exists

    if existing_user:
        if not isinstance(existing_user, int):
            existing_user = await request.app.state.db.get_user(token=existing_user)

        if not existing_user or existing_user in (400, 401):
            existing_user = None

        else:
            token = await request.app.state.db.update_user(existing_user, google_id=userid, email=email)
            if token is None:
                existing_user = None
            else:
                return {"token": token}

    if not existing_user:
        data = await request.app.state.db.new_user(email, google_id=userid)
        return {"token": data['token']}


@router.get("/apps/github/{code}", response_model=responses.TokenResponse, include_in_schema=False)
async def auth_from_github(request: Request, code: str = Query(None), state: Optional[str] = Query(None)) -> Union[Dict[str, str], UJSONResponse]:
    """Allows user to authenticate with GitHub OAuth."""
    if not code:
        return UJSONResponse({"error": "Missing code query"}, status_code=400)

    existing_user = state
    if existing_user:
        try:
            existing_user = int(existing_user)
        except TypeError:
            existing_user = None

    client_id = request.app.config['apps']['github_application_id']
    client_secret = request.app.config['apps']['github_application_secret']
    url = yarl.URL(request.app.config['site']
                   ['base_site']).with_path("/apps/github")

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": url,
        "grant_type": "authorization_code",
        "code": code
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded",
               "Accept": "application/json"}

    async with request.app.state.client.post("https://github.com/login/oauth/access_token", data=data,
                                             headers=headers) as resp:
        resp.raise_for_status()
        data = await resp.json()
        token = data['access_token']

    async with request.app.state.client.get("https://api.github.com/user",
                                            headers={"Authorization": f"Bearer {token}"}) as resp:
        resp.raise_for_status()
        data = await resp.json()
        userid = data['id']

    async with request.app.state.client.get("https://api.github.com/user/emails",
                                            headers={"Authorization": f"Bearer {token}"}) as resp:
        resp.raise_for_status()
        data = await resp.json()
        email = None
        for entry in data:
            if "users.noreply.github.com" in entry['email']:
                continue

            if entry['primary']:
                email = entry['email']
                break

    if email:
        exists = await request.app.state.db.check_email(email)
        if exists:
            existing_user = exists

    if existing_user:
        if not isinstance(existing_user, int):
            existing_user = await request.app.state.db.get_user(token=existing_user)

        if not existing_user or existing_user in (400, 401):
            existing_user = None

        else:
            token = await request.app.state.db.update_user(existing_user, github_id=userid, email=email)
            if token is None:
                existing_user = None
            else:
                return {"token": token}

    if not existing_user:
        data = await request.app.state.db.new_user(email, github_id=userid)
        return {"token": data['token']}
