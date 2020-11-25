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
    filename: str
    syntax: Optional[str] = None
    password: Optional[str] = None
    expires: Optional[datetime.datetime] = None


class _PastePut(BaseModel):
    content: str
    filename: str
    syntax: Optional[str] = None

class ListedPastePut(BaseModel):
    workspace_name: Optional[str] = None
    expires: Optional[datetime.datetime] = None
    password: Optional[str] = None
    files: List[_PastePut]

    class Config:
        schema_extra = {
            "example": {
                "workspace_name": "string",
                "expires": "2020-11-16T13:46:49.215Z",
                "password": "string",
                "files": [{
                    "content": "string",
                    "filename": "string",
                    "syntax": "string",
                },
                    {
                    "content": "another_string",
                    "filename": "another_string",
                    "syntax": "another_string",
                }
                ]
            }
        }


class PastePatch(BaseModel):
    new_content: Optional[str] = None
    new_filename: Optional[str] = None
    new_expires: Optional[datetime.datetime] = None


class PasteDelete(BaseModel):
    pastes: List[str]
