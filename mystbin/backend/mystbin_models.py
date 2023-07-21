from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, TypedDict

import aiohttp
from fastapi import Request, Response
from starlette.datastructures import MutableHeaders, State

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
    user: _StateUser | None
    session: aiohttp.ClientSession


class MystbinRequest(Request):
    @property
    def app(self) -> MystbinApp:
        ...


class MystbinMutableHeaders(MutableHeaders):
    def update(self, other: Mapping[str, str]) -> None:
        ...


class MystbinResponse(Response):
    @property
    def headers(self) -> MystbinMutableHeaders:
        ...
