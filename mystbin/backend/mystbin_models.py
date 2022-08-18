from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, TypedDict

from fastapi import Request
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
    token: Optional[str]
    emails: Optional[List[str]]
    discord_id: Optional[str]
    github_id: Optional[str]
    google_id: Optional[str]
    admin: bool
    theme: str
    subscriber: bool
    username: Optional[str]
    _is_ip_banned: Optional[str]
    _is_user_banned: Optional[int]


class MystbinState(State):
    """Only for db typing."""

    db: Database
    user: _StateUser


class MystbinRequest(Request):
    app: MystbinApp
