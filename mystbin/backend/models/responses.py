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

from attrs import define


__all__ = (
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


@define()
class File:
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

@define()
class PastePostResponse:
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


@define
class PasteGetResponse:
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


@define()
class PasteGetAll:
    id: str
    author_id: int
    created_at: datetime
    views: int
    has_password: bool
    expires: datetime | None = None


@define()
class PasteGetAllResponse:
    pastes: list[PasteGetAll]

@define()
class TokenResponse:
    token: str

@define()
class User:
    id: int
    username: str
    token: str
    emails: list[str]
    discord_id: str | None
    github_id: str | None
    google_id: str | None
    admin: bool
    theme: str
    subscriber: bool


@define()
class SmallUser:
    id: int
    username: str
    authorizations: list[str]
    admin: bool
    theme: str
    subscriber: bool
    banned: bool
    last_seen: str | None
    paste_count: int


@define()
class UserCount:
    count: int


@define()
class UserList:
    users: list[SmallUser]
    page: int
    page_count: int


@define()
class Bookmark:
    id: str
    created_at: datetime
    expires: datetime
    views: int


@define()
class Bookmarks:
    bookmarks: list[Bookmark]
