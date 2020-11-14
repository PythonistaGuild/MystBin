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
import datetime
from typing import List, Optional

from pydantic import BaseModel


__all__ = (
    "BadRequest",
    "Forbidden",
    "NotFound",
    "PastePost",
    "PastePatch",
    "PasteDelete",
    "PastePatchResponse",
    "PastePostResponse",
    "PasteGetResponse",
    "PasteGetAllResponse",
    "TokenResponse",
    "Unauthorized",
    "User",
)


class Unauthorized(BaseModel):
    error: str = "Unauthorized"


class Forbidden(BaseModel):
    error: str = "Forbidden"


class NotFound(BaseModel):
    error: str = "Not Found"


class BadRequest(BaseModel):
    error: str = "Bad Request"
    reason: str = None


class PastePost(BaseModel):
    content: str
    syntax: Optional[str] = None
    nick: Optional[str] = None
    password: Optional[str] = None


class PastePatch(BaseModel):
    new_content: Optional[str] = None
    new_nick: Optional[str] = None
    new_expires: Optional[datetime.datetime] = None


class PasteDelete(BaseModel):
    pastes: List[str]


class PastePostResponse(BaseModel):
    id: str
    nick: Optional[str] = None
    syntax: Optional[str] = None
    created_at: datetime.datetime
    expires: Optional[datetime.datetime] = None


class PastePatchResponse(BaseModel):
    id: str
    nick: Optional[str] = None
    expires: Optional[datetime.datetime] = None


class PasteGetResponse(BaseModel):
    id: str
    content: str
    nick: Optional[str] = None
    syntax: Optional[str] = None
    created_at: datetime.datetime
    expires: Optional[datetime.datetime] = None


class PasteGetAllResponse(BaseModel):
    id: str
    nick: Optional[str] = None
    syntax: Optional[str] = None
    loc: int
    charcount: int
    created_at: datetime.datetime
    expires: Optional[datetime.datetime] = None
    has_password: bool


class TokenResponse(BaseModel):
    token: str


class User(BaseModel):
    id: int
    token: str
    emails: List[str]
    discord_id: str
    github_id: str
    google_id: str
    admin: bool
    theme: str
    subscriber: bool
    banned: bool
