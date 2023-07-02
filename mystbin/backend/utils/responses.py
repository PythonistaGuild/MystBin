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
from starlette.requests import Request
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

class VariableResponse(Response):
    def __init__(self, content: Any, request: Request, status_code: int = 200, headers: dict[str, str] | None = None) -> None:
        self.accept_type = request.headers.get("Accept", "application/json")
        super().__init__(content, status_code, headers)

    def render(self, content: Any) -> bytes:
        if self.accept_type not in self.encoders:
            if "*/*" in self.accept_type:
                return self._encode_json(content)
            
            return f"'{self.accept_type}' is not a supported encoding. " \
                f"try one of the following: {', '.join(self.encoders.keys())}".encode() # cant have fstrings and byte strings lol
        
        return self.encoders[self.accept_type](self, content)

    def _encode_json(self, content: Any) -> bytes:
        return msgspec.json.encode(content)
    
    def _encode_msgpack(self, content: Any) -> bytes:
        return msgspec.msgpack.encode(content)

    def _encode_toml(self, content: Any) -> bytes:
        return msgspec.toml.encode({"response": content})
    
    def _encode_yaml(self, content: Any) -> bytes:
        return msgspec.yaml.encode(content)
    
    encoders = {
        "application/json": _encode_json,
        "application/msgpack": _encode_msgpack,
        "application/toml": _encode_toml,
        "application/yaml": _encode_yaml
    }


# we do a little monkeypatching
import tomli_w._writer
from tomli_w._writer import Context

def format_literal(obj: object, ctx: Context, *, nest_level: int = 0) -> str:
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, (int, float, tomli_w._writer.date, tomli_w._writer.datetime)): # type: ignore
        return str(obj)
    if isinstance(obj, tomli_w._writer.Decimal): # type: ignore
        return tomli_w._writer.format_decimal(obj)
    if isinstance(obj, tomli_w._writer.time): # type: ignore
        if obj.tzinfo:
            raise ValueError("TOML does not support offset times")
        return str(obj)
    if isinstance(obj, str):
        return tomli_w._writer.format_string(obj, allow_multiline=ctx.allow_multiline)
    if isinstance(obj, tomli_w._writer.ARRAY_TYPES):
        return tomli_w._writer.format_inline_array(obj, ctx, nest_level)
    if isinstance(obj, dict):
        return tomli_w._writer.format_inline_table(obj, ctx)
    if isinstance(obj, type(None)):
        return '"NULL"'
    raise TypeError(f"Object of type {type(obj)} is not TOML serializable")

tomli_w._writer.format_literal = format_literal