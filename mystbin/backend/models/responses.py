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
from datetime import datetime
from typing import Type, TypeVar

from msgspec import Struct


__all__ = (
    "create_struct",
    "File",
    "PastePostResponse",
    "PasteGetResponse",
    "PasteGetAll",
    "PasteGetAllResponse",
    "TokenResponse",
    "User",
    "SmallUser",
    "UserCount",
    "UserList",
    "Bookmark",
    "Bookmarks",
)

T = TypeVar("T", bound=Struct)


def create_struct(data: dict, struct: Type[T]) -> T:
    keys = struct.__struct_fields__
    return struct(**{k: v for k, v in data.items() if k in keys})


class File(Struct):
    filename: str
    content: str
    loc: int
    charcount: int
    attachment: str | None


class PastePostResponse(Struct):
    created_at: datetime
    files: list[File]
    id: str
    notice: str | None = None
    author_id: int | None = None
    expires: datetime | None = None


class PasteGetResponse(Struct):
    id: str
    views: int
    files: list[File]
    author_id: int | None
    created_at: datetime
    expires: datetime | None = None
    last_edited: datetime | None = None


class PasteGetAll(Struct):
    id: str
    author_id: int
    created_at: datetime
    edited_at: datetime
    views: int
    has_password: bool
    expires: datetime | None = None


class PasteGetAllResponse(Struct):
    pastes: list[PasteGetAll]


class TokenResponse(Struct):
    token: str


_tokenlistitem_renamer = {"token_name": "name", "token_description": "description", "is_main": "is_web_token"}


def _tokenlistitem_rename_fn(name: str) -> str | None:
    return _tokenlistitem_renamer.get(name, None)


class TokenListItem(Struct, rename=_tokenlistitem_rename_fn):
    id: int
    name: str
    description: str
    is_web_token: bool


class TokenList(Struct):
    tokens: list[TokenListItem]


class User(Struct):
    id: int
    handle: str
    emails: list[str]
    discord_id: str | None
    github_id: str | None
    google_id: str | None
    admin: bool
    gravatar_hash: str | None


class SmallUser(Struct):
    id: int
    handle: str
    authorizations: list[str]
    admin: bool
    subscriber: bool
    banned: bool
    last_seen: str | None
    paste_count: int
    gravatar_hash: str | None


class UserCount(Struct):
    count: int


class UserList(Struct):
    users: list[SmallUser]
    page: int
    page_count: int


class Bookmark(Struct):
    id: str
    created_at: datetime
    expires: datetime
    views: int


class Bookmarks(Struct):
    bookmarks: list[Bookmark]


class Style(Struct):
    primary_bg: str
    secondary_bg: str
    primary_font: str
    secondary_font: str
    accent: str
    prism_theme: str
