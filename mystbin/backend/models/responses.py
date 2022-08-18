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
from typing import List, Literal, Optional

from pydantic import BaseModel


class File(BaseModel):
    filename: str
    content: str
    loc: int
    charcount: int

    class Config:
        schema_extra = {
            "example": {
                "filename": "foo.py",
                "content": "import datetime\\nprint(datetime.datetime.utcnow())",
                "loc": 2,
                "charcount": 49
            }
        }


class PastePostResponse(BaseModel):
    id: str
    author_id: Optional[int] = None
    created_at: datetime
    expires: Optional[datetime] = None
    files: List[File]
    notice: Optional[str]

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
                        "charcount": 49
                    }
                ],
                "notice": "Found discord tokens and sent them to https://gist.github.com/Rapptz/c4324f17a80c94776832430007ad40e6 to be invalidated"
            }
        }


class PastePatchResponse(BaseModel):
    result: Literal["ok"]


class PasteGetResponse(BaseModel):
    id: str
    author_id: Optional[int]
    created_at: datetime
    expires: Optional[datetime] = None
    last_edited: Optional[datetime] = None
    views: int
    files: List[File]

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
                        "charcount": 49
                    }
                ]
            }
        }


class PasteGetAllResponse(BaseModel):
    id: str
    loc: int
    charcount: int
    created_at: datetime
    expires: Optional[datetime] = None
    has_password: bool


class TokenResponse(BaseModel):
    token: str


class User(BaseModel):
    id: int
    username: str
    token: str
    emails: List[str]
    discord_id: Optional[str]
    github_id: Optional[str]
    google_id: Optional[str]
    admin: bool
    theme: str
    subscriber: bool


class SmallUser(BaseModel):
    id: int
    username: str
    authorizations: List[str]
    admin: bool
    theme: str
    subscriber: bool
    banned: bool
    last_seen: Optional[str]
    paste_count: int


class UserCount(BaseModel):
    count: int


class UserList(BaseModel):
    users: List[SmallUser]
    page: int
    page_count: int


class Bookmark(BaseModel):
    id: str
    created_at: datetime
    expires: datetime
    views: int


class Bookmarks(BaseModel):
    bookmarks: List[Bookmark]
