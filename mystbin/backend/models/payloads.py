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


class PasteFile(BaseModel):
    content: str
    filename: str


class PastePut(BaseModel):
    expires: Optional[datetime.datetime] = None
    password: Optional[str] = None
    files: List[PasteFile]

    class Config:
        schema_extra = {
            "example": {
                "expires": "2020-11-16T13:46:49.215Z",
                "password": "string",
                "files": [
                    {
                        "content": "string",
                        "filename": "string"
                    },
                    {
                        "content": "another_string",
                        "filename": "another_string",
                    },
                ],
            }
        }


class PastePatch(BaseModel):
    new_expires: Optional[datetime.datetime] = None
    new_password: Optional[str] = None
    new_files: List[PasteFile]


class PasteDelete(BaseModel):
    pastes: List[str]


class BookmarkPutDelete(BaseModel):
    paste_id: str
