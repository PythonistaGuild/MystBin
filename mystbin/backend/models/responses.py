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

from pydantic import BaseModel


class File(BaseModel):
    filename: str
    content: str
    loc: int
    charcount: int
    tab_id: int | None
    image: str | None

    class Config:
        schema_extra = {
            "example": {
                "filename": "foo.py",
                "content": "import datetime\\nprint(datetime.datetime.utcnow())",
                "loc": 2,
                "charcount": 49,
                "tab_id": 0,
                "url": "...",
            }
        }


class PastePostResponse(BaseModel):
    id: str
    author_id: int | None = None
    created_at: datetime
    expires: datetime | None = None
    files: list[File]
    notice: str | None

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
                    }
                ],
                "notice": "Found discord tokens and sent them to https://gist.github.com/Rapptz/c4324f17a80c94776832430007ad40e6 to be invalidated",
            }
        }


class PasteGetResponse(BaseModel):
    id: str
    author_id: int | None
    created_at: datetime
    expires: datetime | None = None
    last_edited: datetime | None = None
    views: int
    files: list[File]

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
                    }
                ],
            }
        }


class PasteGetAllResponse(BaseModel):
    id: str
    loc: int
    charcount: int
    created_at: datetime
    expires: datetime | None = None
    has_password: bool


class TokenResponse(BaseModel):
    token: str


class User(BaseModel):
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


class SmallUser(BaseModel):
    id: int
    username: str
    authorizations: list[str]
    admin: bool
    theme: str
    subscriber: bool
    banned: bool
    last_seen: str | None
    paste_count: int


class UserCount(BaseModel):
    count: int


class UserList(BaseModel):
    users: list[SmallUser]
    page: int
    page_count: int


class Bookmark(BaseModel):
    id: str
    created_at: datetime
    expires: datetime
    views: int


class Bookmarks(BaseModel):
    bookmarks: list[Bookmark]
