"""MystBin. Share code easily.

Copyright (C) 2020-Current PythonistaGuild

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import datetime
from collections.abc import Iterator, Mapping
from typing import Any

import asyncpg

__all__ = ("FileModel", "PasteModel")


class BaseModel(Mapping[str, Any]):
    __slots__ = ("record",)

    def __init__(self, record: asyncpg.Record | dict[str, Any], /) -> None:
        self.record: dict[str, Any] = dict(record)

    def __getitem__(self, key: str) -> Any:  # noqa: ANN401 # this is due to the dynamic nature of the mapping and Record types.
        return self.record[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.record)

    def __len__(self) -> int:
        return len(self.record)

    def serialize(self, *, exclude: list[str] | None = None) -> dict[str, Any]:
        exclude = exclude or ["file_index"]

        new: dict[str, Any] = {}

        for key, value in self.record.items():
            if key in exclude:
                continue

            if isinstance(value, datetime.datetime):
                new[key] = value.isoformat()
            else:
                new[key] = value

        if isinstance(self, PasteModel) and self.files:
            new["files"] = [f.serialize() for f in self.files]

        return new


class FileModel(BaseModel):
    """Model that represents a mystbin File."""

    def __init__(self, record: asyncpg.Record | dict[str, Any]) -> None:
        super().__init__(record)

        self.parent_id: str = record["parent_id"]
        self.content: str = record["content"]
        self.filename: str = record["filename"]
        self.loc: int = record["loc"]
        self.charcount: int = record["charcount"]
        self.index: int = record["file_index"]
        self.annotation: str | None = record["annotation"]
        self.warning_positions: list[int] = record["warning_positions"]


class PasteModel(BaseModel):
    """Model that represents a mystbin Paste."""

    def __init__(self, record: asyncpg.Record) -> None:
        super().__init__(record)

        self.id: str = record["id"]
        self.created_at: datetime.datetime = record["created_at"]
        self.expires: datetime.datetime | None = record["expires"]
        self.password: str | None = record["password"]
        self.views: int = record["views"]
        self.safety: str = record["safety"]
        self.has_password: bool | None = record.get("has_password", None)
        self.password_ok: bool | None = record.get("password_ok", None)
        self.files: list[FileModel] = []
