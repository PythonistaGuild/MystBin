"""Copyright(C) 2020-present PythonistaGuild

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
from typing import Any
from starlette.responses import Response as Response, JSONResponse

import msgspec
import ujson

class UJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        if isinstance(content, msgspec.Struct):
            return msgspec.json.encode(content)
        
        return ujson.dumps(
            content,
            ensure_ascii=False
        ).encode("utf-8")
