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
import inspect
from typing import Literal, Any, Callable, TypeVar

T = TypeVar("T")

class OpenAPI:
    def __init__(self) -> None:
        self.routes: list[Route] = []
        self.components: list[_Component] = []
    
    def route(self, r: Route) -> Callable[[T], T]:
        self.routes.append(r)

        def wraps(fn: T) -> T: # probably do something with this later
            if not r.description and fn.__doc__:
                r.description = inspect.cleandoc(fn.__doc__)

            return fn
        
        return wraps

    def render_spec(
        self,
        title: str,
        description: str,
        version: str,
        is_public_schema: bool
    ) -> dict[str, Any]:
        components = {}
        paths = {}
        resp = {
            "openapi": "3.0.2",
            "info": {
                "title": title,
                "description": description,
                "version": version
            },
            "paths": paths,
            "components": {
                "schemas": components
            }
        }

        for component in self.components:
            components[component.title] = component.render()

        for route in self.routes:
            if route.exclude_from_default_schema and is_public_schema:
                continue
            
            if route.route not in paths:
                paths[route.route] = {}
            
            paths[route.route][route.method.lower()] = route.render()
        
        return resp

instance = OpenAPI()

class ComponentProperty:
    __slots__ = ("name", "title", "type", "format", "required")
    def __init__(
        self,
        name: str,
        title: str,
        type: Literal["string", "boolean", "integer", "date-time"],
        format: str | None = ...,
        required: bool = False
    ) -> None:
        self.name = name
        self.title = title
        self.type = type
        self.format = format
        self.required = required
    
    def render(self) -> dict:
        resp: dict[str, Any] = {
            "title": self.title,
            "type": self.type
        }
        if self.format is not ...:
            resp["format"] = self.format
        
        return resp


class ComponentArrayProperty:
    __slots__ = ("name", "title", "items", "required")
    def __init__(self, name: str, title: str, required: bool, items: dict | _Component) -> None:
        self.name = name
        self.title = title
        self.items = items
        self.required = required
    
    def render(self) -> dict:
        return {
            "title": self.title,
            "type": "array",
            "items": self.items if isinstance(self.items, dict) else {"$ref": f"#/components/schemas/{self.items.title}"}
        }


class _Component:
    title: str
    properties: list[ComponentProperty | ComponentArrayProperty]
    type: Literal["object"]
    example: Any | None

    def __init__(self, title: str, properties: list[ComponentProperty | ComponentArrayProperty], example: Any = ...) -> None:
        self.title: str = title
        self.properties = properties
        self.type = "object"
        self.example = example

        instance.components.append(self)
    
    def render(self) -> dict:
        resp: dict[str, Any] = {
            "title": self.title,
            "type": self.type,
            "properties": {x.name: x.render() for x in self.properties}
        }

        if self.example is not Ellipsis:
            resp["example"] = self.example
        
        required = [x.name for x in self.properties if x.required]

        if required:
            resp["required"] = required
        
        return resp


class Response:
    def __init__(self, description: str, response_model: _Component | None, response_type: str = "application/json") -> None:
        self.description = description
        self.response_model = response_model
        self.response_type = response_type
    
    def render(self) -> dict:
        return {
            "description": self.description,
            "content": {
                self.response_type: {
                    "schema": {
                        "$ref": f"#/components/schemas/{self.response_model.title}"
                    } if self.response_model else {}
                }
            }
        }


class RouteParameter:
    __slots__ = ("title", "type", "name", "required", "location")

    def __init__(
        self,
        title: str, # external
        type: Literal["string", "integer", "boolean"],
        param_name: str, # internal
        required: bool,
        loc: Literal["path", "query"]
    ) -> None:
        self.title = title
        self.type = type
        self.name = param_name
        self.required = required
        self.location = loc
    
    def render(self) -> dict:
        return {
            "name": self.name,
            "in": self.location,
            "required": self.required,
            "schema": {
                "title": self.title,
                "type": self.type
            }
        }


class Route:
    __slots__ = ("route", "method", "summary", "description", "tags", "request_body", "body_content_type", "is_body_required", "responses", "deprecated", "parameters", "exclude_from_default_schema")

    def __init__(
        self,
        route: str,
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
        summary: str,
        tags: list[str],
        request_body: _Component | None,
        parameters: list[RouteParameter],
        responses: dict[int, Response],
        description: str | None = None,
        body_content_type: str = "application/json",
        is_body_required: bool = True,
        exclude_from_default_schema: bool = False,
        deprecated: bool = False
    ) -> None:
        self.route = route
        self.method = method
        self.summary = summary
        self.description = description
        self.tags = tags
        self.request_body = request_body
        self.body_content_type = body_content_type
        self.is_body_required = is_body_required
        self.responses = responses
        self.parameters = parameters
        self.exclude_from_default_schema = exclude_from_default_schema
        self.deprecated = deprecated
    
    def render(self) -> dict:
        resp: dict[str, Any] = {
            "deprecated": self.deprecated,
            "summary": self.summary,
            "description": self.description,
            "operationId": f"{self.method}_{self.route.strip('/').replace('/', '_')}",
            "tags": self.tags,
            "responses": {
                str(status): resp.render() for status, resp in self.responses.items()
            }
        }
        if self.parameters:
            resp["parameters"] = [x.render() for x in self.parameters]
            
        if self.request_body:
            resp["requestBody"] = {
                "required": self.is_body_required,
                "content": {
                    self.body_content_type: {
                        "schema": {
                            "$ref": f"#/components/schemas/{self.request_body.title}"
                        }
                    }
                }
            }
        
        return resp

UnauthorizedResponse = Response("Unauthorized", _Component("UnauthorizedComponent", [ComponentProperty("error", "Error", "string")], example={"error": "Unauthorized"}))
ForbiddenResponse = Response("Forbidden", _Component("ForbiddenComponent", [ComponentProperty("error", "Error", "string")], example={"error": "Forbidden"}))
BadRequestResponse = Response("Bad Request", _Component("BadRequestComponent", [ComponentProperty("error", "Error", "string")], example={"error": "Bad Request"}))
NotFoundResponse = Response("Not Found", _Component("BadRequestComponent", [ComponentProperty("error", "Error", "string")], example={"error": "Paste Not Found"}))

ValidationErrorResponse = Response("Validation Error", _Component("ValidationErrorComponent", [
    ComponentProperty("error", "Error", "string", required=True),
    ComponentProperty("location", "Location", "string", required=False)
    ],
    example={"error": "Expected `str`, got `bool`", "location": "$.files[0].content"}))

# mystbin base models

User = _Component("User", properties=[
    ComponentProperty("id", "ID", "integer", required=True),
    ComponentProperty("username", "Username", "string", required=True),
    ComponentProperty("discord_id", "Discord ID", "string", "Linked Account", required=False),
    ComponentProperty("github_id", "Github ID", "string", "Linked Account", required=False),
    ComponentProperty("google_id", "Google ID", "string", "Linked Account", required=False),
    ComponentProperty("admin", "Admin", "boolean", "Is admin", required=True),
    ComponentProperty("theme", "Theme", "string", required=True),
    ComponentProperty("subscriber", "Subscriber", "boolean", required=True),
    ComponentArrayProperty("emails", "Emails", required=True, items={"type": "string"})
])

SmallUser = _Component("SmallUser", properties=[
    ComponentProperty("id", "ID", "integer", required=True),
    ComponentProperty("username", "Username", "string", required=True),
    ComponentProperty("admin", "Admin", "boolean", "Is admin", required=True),
    ComponentProperty("theme", "Theme", "string", required=True),
    ComponentProperty("subscriber", "Subscriber", "boolean", required=True),
    ComponentProperty("banned", "Is Banned", "boolean", required=True),
    ComponentProperty("paste_count", "Paste Count", "integer", required=True),
])

AdminUserList = _Component("UserList", properties=[
    ComponentProperty("page", "Page", "integer", required=True),
    ComponentProperty("page_count", "Page Count", "integer", required=True),
    ComponentArrayProperty("users", "Users", True, items=SmallUser)
])

AdminBans = _Component("AdminBans", [
    ComponentProperty("ip", "IP", "string", required=False),
    ComponentProperty("userid", "User ID", "integer", required=False),
    ComponentProperty("reason", "Reason", "string", required=True)
], example={"ip": None, "userid": 1234, "reason": "nerd"})

AdminBanList = _Component("AdminBanList", properties=[
    ComponentProperty("reason", "Reason", "string", required=False),
    ComponentArrayProperty("searches", "Search", True, items=AdminBans)
])

File = _Component("File", properties=[
    ComponentProperty("filename", "Filename", "string", required=True),
    ComponentProperty("content", "Content", "string", required=True),
    ComponentProperty("loc", "Lines of content", "integer", required=True),
    ComponentProperty("charcount", "Character Count", "integer", required=True),
    ComponentProperty("attachment", "Attachment", "string")
], example={
                "filename": "foo.py",
                "content": "import datetime\\nprint(datetime.datetime.utcnow())",
                "loc": 2,
                "charcount": 49,
                "attachment": "https://mystbin.b-cdn.com/umbra_sucks.jpeg",
            })

UploadRichPasteFile = _Component("UploadRichPasteFile", properties=[
    ComponentProperty("content", "Content", "string", required=True),
    ComponentProperty("filename", "Filename", "string", required=True),
    ComponentProperty("attachment", "Attachment", "string", required=False)
    ], example={"content": "explosions everywhere", "filename": "kaboom.txt", "attachment": "image.png"})

UploadPasteFile = _Component("UploadPasteFile", properties=[
    ComponentProperty("content", "Content", "string", required=True),
    ComponentProperty("filename", "Filename", "string", required=True)
    ], example={"content": "explosions everywhere", "filename": "kaboom.txt"})

PastePost = _Component("PastePost", properties=[
    ComponentProperty("expires", "Expires", "date-time", required=False),
    ComponentProperty("password", "Password", "string", required=False),
    ComponentArrayProperty("files", "Files", required=True, items=UploadPasteFile),
    ComponentProperty("requester_id", "Requester ID", "integer", required=False),
    ComponentProperty("requester_slug", "Requester Slug", "string", required=False),
    ComponentProperty("private", "Private Paste", "boolean", required=False)
], example={
                "expires": "2020-11-16T13:46:49.215Z",
                "password": None,
                "private": False,
                "files": [
                    {"content": "import this", "filename": "foo.py"},
                    {
                        "filename": "doc.md",
                        "content": "**do not use this in production**",
                    },
                ],
            })

RichPastePost = _Component("RichPastePost", properties=[
    ComponentProperty("expires", "Expires", "date-time", required=False),
    ComponentProperty("password", "Password", "string", required=False),
    ComponentArrayProperty("files", "Files", required=True, items=UploadRichPasteFile),
    ComponentProperty("requester_id", "Requester ID", "integer", required=False),
    ComponentProperty("requester_slug", "Requester Slug", "string", required=False),
], example={
                "expires": "2020-11-16T13:46:49.215Z",
                "password": None,
                "files": [
                    {"content": "import this", "filename": "foo.py", "attachment": None},
                    {"filename": "doc.md", "content": "**do not use this in production**", "attachment": "image2.jpeg"},
                ],
            })

PastePatch = _Component("PastePatch", properties=[
    ComponentProperty("new_expires", "New Expiry", "date-time", required=False),
    ComponentProperty("new_password", "New Password", "string", required=False),
    ComponentArrayProperty("new_files", "New Files", required=True, items=UploadPasteFile)
], example={"new_password": "abc123", "new_files": [{"content": "foo", "filename": "bar.txt"}]})

PasteDelete = _Component("PasteDelete", properties=[
    ComponentArrayProperty("pastes", "Paste IDs", required=True, items={"type": "string"})
], example={"pastes": ["ThreeRandomWords"]})

PasteDeleteResponse = Response("Success", _Component("PasteDeleteResponseComponent", [
    ComponentArrayProperty("succeeded", "Succeeded", True, {"type": "string"}),
    ComponentArrayProperty("failed", "Failed", True, {"type": "string"})
], example={"succeded": ["foo"], "failed": ["bar"]}))

BookmarkPutDelete = _Component("BookmarkPutDelete", properties=[
    ComponentProperty("paste_id", "Paste ID", "string", required=True)
], example={"paste_id": "ThreeRandomWords"})

PastePostResponse = _Component("PastePostResponse", properties=[
    ComponentProperty("created_at", "Created At", "date-time", required=True),
    ComponentProperty("id", "ID", "string", required=True),
    ComponentProperty("notice", "Notice", "string", required=False),
    ComponentProperty("author_id", "Author ID", "integer", required=False),
    ComponentProperty("expires", "Expires", "date-time", required=False),
    ComponentArrayProperty("files", "Files", True, File)
], example={
                "id": "FlyingHighKites",
                "author_id": None,
                "created_at": "2020-11-16T13:46:49.215Z",
                "expires": None,
                "files": [
                    {
                        "filename": "foo.py",
                        "content": "import datetime\\nprint(datetime.datetime.utcnow())",
                        "loc": 2,
                        "charcount": 49,
                        "attachment": "https://mystbin.b-cdn.com/umbra_sucks.jpeg",
                    }
                ],
                "notice": "Found discord tokens and sent them to https://gist.github.com/Rapptz/c4324f17a80c94776832430007ad40e6 to be invalidated",
            })

PasteGetResponse = _Component("PasteGetResponse", properties=[
    ComponentProperty("created_at", "Created At", "date-time", required=True),
    ComponentProperty("id", "ID", "string", required=True),
    ComponentProperty("views", "View Count", "integer", required=True),
    ComponentProperty("author_id", "Author ID", "integer", required=False),
    ComponentProperty("expires", "Expires", "date-time", required=False),
    ComponentProperty("last_edited", "Last Edit", "date-time", required=False),
    ComponentArrayProperty("files", "Files", True, File)
], example={
                "id": "FlyingHighKites",
                "author_id": None,
                "created_at": "2020-11-16T13:46:49.215Z",
                "expires": None,
                "last_edited": "2020-11-20T0:46:0.215Z",
                "views": 48,
                "files": [
                    {
                        "filename": "foo.py",
                        "content": "import datetime\\nprint(datetime.datetime.utcnow())",
                        "loc": 2,
                        "charcount": 49,
                        "attachment": "https://mystbin.b-cdn.com/umbra_sucks.jpeg",
                    }
                ]
            })

PasteGetAllResponse = _Component("PasteGetAll", properties=[
    ComponentArrayProperty("pastes", "Pastes", True, items=
        _Component("PasteGetAllField", properties=[
        ComponentProperty("id", "ID", "string", required=True),
        ComponentProperty("author_id", "Author ID", "integer", required=False),
        ComponentProperty("created_at", "Created At", "date-time", required=True),
        ComponentProperty("views", "Views", "integer", required=True),
        ComponentProperty("has_password", "Has Password", "boolean", required=True),
        ComponentProperty("expires", "Expires", "date-time", required=False),
        ComponentProperty("private", "Private Paste", "boolean", required=True)
    ]))
])

TokenResponse = _Component("TokenResponse", properties=[ComponentProperty("token", "Token", "string", required=True)])
TokenListResponseTokens = ComponentArrayProperty("tokens", "Tokens", True,
    _Component("TokenListResponseTokens", [
        ComponentProperty("id", "Token ID", "integer", required=True),
        ComponentProperty("name", "Token Name", "string", required=True),
        ComponentProperty("description", "Token Description", "string", required=True),
        ComponentProperty("is_web_token", "Is token used on website", "boolean", required=True)
    ]
))
TokenListResponse = _Component("TokenListResponse", properties=[TokenListResponseTokens])

LoginTokenResponse = TokenResponse = _Component("LoginTokenResponse", properties=[
    ComponentProperty("token", "Token", "string", required=True),
    ComponentProperty("needs_handle_modal", "Needs Handle Modal", "boolean", required=True),
    ComponentProperty("handle", "Current Handle", "string", required=True),
    ])

TokenPost = _Component("TokenPost", properties=[
    ComponentProperty("name", "Name", "string", "3-32", required=True),
    ComponentProperty("description", "Description", "string", "0-256")
])
TokenPostResponse = _Component("TokenPostResponse", properties=[
    ComponentProperty("name", "Name", "string", required=True),
    ComponentProperty("id", "ID", "integer", required=True),
    ComponentProperty("token", "Token", "string", required=True)
])

Bookmark = _Component("Bookmark", properties=[
    ComponentProperty("id", "Paste ID", "string", required=True),
    ComponentProperty("created_at", "Created At", "date-time", required=True),
    ComponentProperty("expires", "Paste Expires", "date-time", required=False),
    ComponentProperty("views", "View Count", "integer", required=True)
])
BookmarkResponse = _Component("Bookmarks", properties=[
    ComponentArrayProperty("bookmarks", "Bookmarks", True, items=Bookmark)
])

Style = _Component("Style", properties=[
    ComponentProperty("primary_bg", "Primary Background", "string", "hex", True),
    ComponentProperty("secondary_bg", "Secondary Background", "string", "hex", True),
    ComponentProperty("primary_font", "Primary Font", "string", required=True),
    ComponentProperty("secondary_font", "Secondary Font", "string", required=True),
    ComponentProperty("accent", "Accent", "string", "hex", True),
    ComponentProperty("prism_theme", "Prism Theme", "string", required=True),
])