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
    syntax: Optional[str] = None
    loc: int
    charcount: int

class PastePostResponse(BaseModel):
    id: str
    author_id: Optional[int] = None
    created_at: datetime
    expires: Optional[datetime] = None
    files: List[_File]


class PastePatchResponse(BaseModel):
    id: str
    nick: Optional[str] = None
    expires: Optional[datetime] = None


class PasteGetResponse(BaseModel):
    id: str
    content: str
    nick: Optional[str] = None
    syntax: Optional[str] = None
    created_at: datetime
    expires: Optional[datetime] = None


class PasteGetAllResponse(BaseModel):
    id: str
    nick: Optional[str] = None
    syntax: Optional[str] = None
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
    discord_id: str
    github_id: str
    google_id: str
    admin: bool
    theme: str
    subscriber: bool
    banned: bool
