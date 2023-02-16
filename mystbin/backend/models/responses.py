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
from typing import TypeVar, Type
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

    class Config:
        schema_extra = {
            "example": {
                "filename": "foo.py",
                "content": "import datetime\\nprint(datetime.datetime.utcnow())",
                "loc": 2,
                "charcount": 49,
                "attachment": "https://mystbin.b-cdn.com/umbra_sucks.jpeg",
            }
        }

class PastePostResponse(Struct):
    created_at: datetime
    files: list[File]
    id: str
    notice: str | None = None
    author_id: int | None = None
    expires: datetime | None = None

    class Config:
        schema_extra = {
            "example": {
                "id": "FlyingHighKites",
                "author_id": None,
                "created_at": "2020-11-16T13:46:49.215Z",
                "expires": None,
                "files": [
                    {
                        "filename": "foo.py",
                        "content": "import datetime\\nprint(datetime.datetime.utcnow())",
                        "loc": 2,
                        "charcount": 49,
                        "attachment": "https://mystbin.b-cdn.com/umbra_sucks.jpeg",
                    }
                ],
                "notice": "Found discord tokens and sent them to https://gist.github.com/Rapptz/c4324f17a80c94776832430007ad40e6 to be invalidated",
            }
        }


class PasteGetResponse(Struct):
    id: str
    views: int
    files: list[File]
    author_id: int | None
    created_at: datetime
    expires: datetime | None = None
    last_edited: datetime | None = None

    class Config:
        schema_extra = {
            "example": {
                "id": "FlyingHighKites",
                "author_id": None,
                "created_at": "2020-11-16T13:46:49.215Z",
                "expires": None,
                "last_edited": "2020-11-20T0:46:0.215Z",
                "views": 48,
                "files": [
                    {
                        "filename": "foo.py",
                        "content": "import datetime\\nprint(datetime.datetime.utcnow())",
                        "loc": 2,
                        "charcount": 49,
                        "attachment": "https://mystbin.b-cdn.com/umbra_sucks.jpeg",
                    }
                ]
            }
        }


class PasteGetAll(Struct):
    id: str
    author_id: int
    created_at: datetime
    views: int
    has_password: bool
    expires: datetime | None = None


class PasteGetAllResponse(Struct):
    pastes: list[PasteGetAll]

class TokenResponse(Struct):
    token: str

_tokenlistitem_renamer = {
    "token_name": "name",
    "token_description": "description",
    "is_main": "is_web_token"
}

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
    username: str
    emails: list[str]
    discord_id: str | None
    github_id: str | None
    google_id: str | None
    admin: bool
    theme: str
    subscriber: bool


class SmallUser(Struct):
    id: int
    username: str
    authorizations: list[str]
    admin: bool
    theme: str
    subscriber: bool
    banned: bool
    last_seen: str | None
    paste_count: int


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
