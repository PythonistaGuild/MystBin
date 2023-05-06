from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, TypedDict

import aiohttp
from starlette.requests import Request
from starlette.websockets import WebSocket
from starlette.datastructures import State

from utils.db import Database


if TYPE_CHECKING:
    from app import MystbinApp

__all__ = (
    "MystbinState",
    "MystbinRequest",
)


class _StateUser(TypedDict):
    id: int
    token: str
    emails: list[str]
    discord_id: str | None
    github_id: str | None
    google_id: str | None
    admin: bool
    theme: str
    subscriber: bool
    username: str
    _is_ip_banned: str | None
    _is_user_banned: int | None


class MystbinState(State):
    """Only for db typing."""

    db: Database
    session: aiohttp.ClientSession

class RequestState(State):
    user: _StateUser | None
    token_key: uuid.UUID | None
    token_id: int | None
    user_id: int | None

class MystbinRequest(Request):
    app: MystbinApp
    state: RequestState

class MystbinWebsocket(WebSocket):
    app: MystbinApp
    state: RequestState