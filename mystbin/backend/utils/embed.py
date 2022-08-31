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


class Embed:
    def __init__(
        self,
        *,
        title: str | None = None,
        description: str | None = None,
        colour: int = 0,
        author: dict[str, str] | None = None,
        timestamp: datetime.datetime | None = None,
        footer: dict[str, str] | None = None,
    ) -> None:
        self.title = title
        self.description = description
        self.colour = colour
        self.author = author
        self.timestamp = timestamp
        self.footer = footer

    def to_dict(self) -> dict[str, str | int | dict[str, str]]:
        final = {}
        final["type"] = "rich"
        final["color"] = self.colour
        if self.title:
            final["title"] = self.title
        if self.description:
            final["description"] = self.description
        if self.author:
            final["author"] = self.author
        if self.timestamp:
            final["timestamp"] = (
                self.timestamp.astimezone(tz=datetime.timezone.utc).isoformat()
                if self.timestamp.tzinfo
                else self.timestamp.replace(tzinfo=datetime.timezone.utc).isoformat()
            )
        if self.footer:
            final["footer"] = self.footer

        return final
