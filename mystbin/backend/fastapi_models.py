from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Request
from starlette.datastructures import State
from utils.db import Database


if TYPE_CHECKING:
    from app import MystbinApp

__all__ = (
    "MystbinState",
    "MystbinRequest",
)


class MystbinState(State):
    """Only for db typing."""

    db: Database


class MystbinRequest(Request):
    app: MystbinApp
