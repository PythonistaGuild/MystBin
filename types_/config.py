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

from typing import NotRequired, TypedDict

import starlette_plus


class Server(TypedDict):
    host: str
    port: int
    domain: str
    session_secret: str
    maintenance: bool


class Database(TypedDict):
    dsn: str


class Redis(TypedDict):
    limiter: str
    sessions: str


class Limits(TypedDict):
    paste_get: starlette_plus.RateLimitData
    paste_get_day: starlette_plus.RateLimitData
    paste_post: starlette_plus.RateLimitData
    paste_post_day: starlette_plus.RateLimitData
    global_limit: starlette_plus.RateLimitData


class Pastes(TypedDict):
    char_limit: int
    file_limit: int
    name_limit: int


class Github(TypedDict):
    token: str
    timeout: float


class Config(TypedDict):
    SERVER: Server
    DATABASE: Database
    REDIS: NotRequired[Redis]
    LIMITS: Limits
    PASTES: Pastes
    GITHUB: NotRequired[Github]
