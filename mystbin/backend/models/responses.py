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
from typing import List, Optional

from pydantic import BaseModel


class _File(BaseModel):
    filename: str
    content: str
    syntax: Optional[str] = None
    loc: int
    charcount: int


class PastePostResponse(BaseModel):
    id: str
    author_id: Optional[int] = None
    created_at: datetime
    expires: Optional[datetime] = None
    files: List[_File]
    notice: Optional[str]


class PastePatchResponse(BaseModel):
    id: str
    expires: Optional[datetime] = None


class PasteGetResponse(BaseModel):
    id: str
    created_at: datetime
    expires: Optional[datetime] = None
    last_edited: Optional[datetime] = None
    views: int
    pastes: List[_File]


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
