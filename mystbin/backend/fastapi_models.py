from typing import TYPE_CHECKING
from .utils.db import Database

from starlette.datastructures import State
from fastapi import Request

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
