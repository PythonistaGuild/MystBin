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
from __future__ import annotations

from typing import Callable, TypeVar, Literal, Any, TYPE_CHECKING
from starlette.routing import Route

if TYPE_CHECKING:
    from app import MystbinApp

T = TypeVar("T", bound=Callable[..., Any])

class Router:
    def __init__(self) -> None:
        self._routes: list[Route] = []
    
    def route(self, path: str, methods: list[Literal["GET", "POST", "PATCH", "DELETE", "PUT"]]) -> Callable[[T], T]:
        def wraps(fn: T) -> T:
            self._routes.append(Route(path, fn, methods=methods))
            return fn
        
        return wraps
    
    def get(self, path: str) -> Callable[[T], T]:
        return self.route(path, ["GET"])
    
    def post(self, path: str) -> Callable[[T], T]:
        return self.route(path, ["POST"])
    
    def delete(self, path: str) -> Callable[[T], T]:
        return self.route(path, ["DELETE"])
    
    def put(self, path: str) -> Callable[[T], T]:
        return self.route(path, ["PUT"])
    
    def patch(self, path: str) -> Callable[[T], T]:
        return self.route(path, ["PATCH"])
    
    def add_to_app(self, app: MystbinApp) -> None:
        app.router.routes.extend(self._routes)