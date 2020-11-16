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


class PastePost(BaseModel):
    content: str
    syntax: Optional[str] = None
    nick: Optional[str] = None
    password: Optional[str] = None
    expires: Optional[datetime.datetime] = None


class ListedPastePut(BaseModel):
    data: List[PastePost]

    class Config:
        schema_extra = {
            "example": {
                "data": [{
                    "content": "string",
                    "syntax": "string",
                    "nick": "string",
                    "password": "string",
                    "expires": "2020-11-16T13:46:49.215Z"
                },
                    {
                    "content": "another_string",
                    "syntax": "another_string",
                    "nick": "another_string",
                    "password": "another_string",
                    "expires": "2020-11-16T13:46:49.215Z"
                }
                ]
            }
        }


class PastePatch(BaseModel):
    new_content: Optional[str] = None
    new_nick: Optional[str] = None
    new_expires: Optional[datetime.datetime] = None


class PasteDelete(BaseModel):
    pastes: List[str]
