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

from attrs import define


__all__ = (
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "BadRequest",
)

@define()
class Unauthorized:
    error: str = "Unauthorized"
    notice: str

    class Config:
        schema_extras = {"example": {"error": "Unauthorized", "notice": "You must be signed in to use this route"}}


@define()
class Forbidden:
    error: str = "Forbidden"


@define()
class NotFound:
    error: str = "Not Found"


@define()
class BadRequest:
    error: str = "Bad Request"
    reason: str | None = None
