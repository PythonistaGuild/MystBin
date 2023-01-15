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
from __future__ import annotations

import datetime
from typing import TypeVar, Type
from msgspec import Struct
import msgspec


__all__ = (
    "create_struct_from_payload",
    "PasteFile",
    "RichPasteFile",
    "PastePost",
    "RichPastePost",
    "PastePatch",
    "PasteDelete",
    "BookmarkPutDelete",
)

T = TypeVar("T", bound=Struct)

def create_struct_from_payload(data: str | bytes, struct: Type[T]) -> T:
    return msgspec.json.decode(data, type=struct)

class PasteFile(Struct):
    content: str
    filename: str

    class Config:
        schema_extra = {"example": {"content": "explosions everywhere", "filename": "kaboom.txt"}}


class RichPasteFile(Struct):
    content: str
    filename: str
    attachment: str | None = None

    class Config:
        schema_extra = {
            "example": {"content": "explosions everywhere", "filename": "kaboom.txt", "attachment": "image1.png"}
        }

class PastePost(Struct):
    files: list[PasteFile]
    expires: datetime.datetime | None = None
    password: str | None = None

    class Config:
        schema_extra = {
            "example": {
                "expires": "2020-11-16T13:46:49.215Z",
                "password": None,
                "files": [
                    {"content": "import this", "filename": "foo.py"},
                    {
                        "filename": "doc.md",
                        "content": "**do not use this in production**",
                    },
                ],
            }
        }


class RichPastePost(Struct):
    files: list[RichPasteFile]
    expires: datetime.datetime | None = None
    password: str | None = None

    class Config:
        schema_extra = {
            "example": {
                "expires": "2020-11-16T13:46:49.215Z",
                "password": None,
                "files": [
                    {"content": "import this", "filename": "foo.py", "attachment": None},
                    {"filename": "doc.md", "content": "**do not use this in production**", "attachment": "image2.jpeg"},
                ],
            }
        }


class PastePatch(Struct):
    new_files: list[PasteFile]
    new_expires: datetime.datetime | None = None
    new_password: str | None = None


class PasteDelete(Struct):
    pastes: list[str]


class BookmarkPutDelete(Struct):
    paste_id: str
