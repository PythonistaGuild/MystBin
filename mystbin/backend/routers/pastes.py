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

import asyncio
import json
import pathlib
import re
import uuid
from random import sample
from typing import Coroutine

import msgspec
import yarl
from asyncpg import Record
from models import payloads, responses
from sse_starlette import EventSourceResponse
from starlette import status as HTTPStatus
from starlette.datastructures import UploadFile
from starlette.requests import Request

from mystbin_models import MystbinRequest, MystbinWebsocket
from utils import openapi
from utils.ratelimits import limit
from utils.responses import Response, VariableResponse
from utils.router import Router


_WORDS_LIST = open(pathlib.Path("utils/words.txt")).readlines()
word_list = [word.title() for word in _WORDS_LIST if len(word) > 3]
del _WORDS_LIST

TOKEN_RE = re.compile(r"[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27}")

router = Router()

__p = pathlib.Path("./config.json")
if not __p.exists():
    __p = pathlib.Path("../../config.json")

with __p.open() as __f:
    __config = json.load(__f)

del __p, __f  # micro-opt, don't keep unneeded variables in-ram
HAS_BUNNYCDN = True
if not __config.get("bunny_cdn"):
    HAS_BUNNYCDN = False
elif not __config["bunny_cdn"].get("token"):
    HAS_BUNNYCDN = False


def generate_paste_id(n: int = 3):
    """Generate three random words."""
    word_samples = sample(word_list, n)
    return "".join(word_samples).replace("\n", "")


def enforce_paste_limit(app, paste: payloads.PasteFile | payloads.RichPasteFile, request: Request, n=1):
    charlim = app.config["paste"]["character_limit"]
    if len(paste.content) > charlim:
        return VariableResponse(
            {
                "error": f"files.{n}.content ({paste.filename}): maximum length per file is {charlim} characters. "
                f"You are {len(paste.content)-charlim} characters over the limit"
            },
            request,
            status_code=400,
        )

    return None


def enforce_multipaste_limit(app, pastes: payloads.PastePost | payloads.RichPastePost, request: Request):
    filelim = app.config["paste"]["character_limit"]
    if len(pastes.files) < 1:
        return VariableResponse({"error": "files.length: you have not provided any files"}, request, status_code=400)
    if len(pastes.files) > filelim:
        return VariableResponse(
            {
                "error": f"files.length: maximum file count is {filelim} files. You are "
                f"{len(pastes.files) - filelim} files over the limit"
            },
            request,
            status_code=400,
        )

    for n, file in enumerate(pastes.files):
        if err := enforce_paste_limit(app, file, request, n):
            return err

    return None


async def upload_to_gist(request: MystbinRequest, tokens: str) -> dict:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {request.app.config['apps']['github_bot_token']}",
    }

    filename = "output.txt"
    data = {"public": True, "files": {filename: {"content": tokens}}}

    async with request.app.state.client.post("https://api.github.com/gists", headers=headers, data=data) as resp:
        if 300 > resp.status >= 200:
            return await resp.json()
        resp.raise_for_status()
        raise RuntimeError


async def find_discord_tokens(request: MystbinRequest, pastes: payloads.PastePost | payloads.RichPastePost):
    if not request.app.config["apps"].get("github_bot_token", None):
        return None

    tokens = []

    for file in pastes.files:
        v = TOKEN_RE.findall(file.content)
        if v:
            tokens += v

    return tokens or None


def respect_dnt(request: MystbinRequest):
    if request.headers.get("DNT", None) == "1":
        return "DNT"

    if request.app.config["paste"]["log_ip"]:
        return request.headers.get("X-Forwarded-For", request.client.host)  # type: ignore

    return None


async def handle_paste_requests(
    request: MystbinRequest, payload: payloads.RichPastePost | payloads.PastePost, new_paste_id: str
) -> str | None:
    if payload.requester_id is not None and payload.requester_slug is not None:
        if await request.app.state.db.get_paste_request(payload.requester_slug, payload.requester_id) is not None:
            await request.app.state.db.fulfill_paste_request(payload.requester_slug, payload.requester_id, new_paste_id)
        else:
            return "\nInvalid requester ID/Slug, ignored."


desc = f"""Post a paste.

This endpoint falls under the `postpastes` ratelimit bucket.
The `postpastes` bucket has a default ratelimit of {__config['ratelimits']['postpastes']}, and a ratelimit of {__config['ratelimits']['authed_postpastes']} when signed in
"""


@router.post("/paste")
@openapi.instance.route(
    openapi.Route(
        "/paste",
        "POST",
        "Create Paste",
        ["pastes"],
        openapi.PastePost,
        [],
        {
            201: openapi.Response("Success", openapi.PastePostResponse),
            400: openapi.BadRequestResponse,
            422: openapi.ValidationErrorResponse,
        },
        description=desc,
    )
)
@limit("postpastes")
async def put_pastes(request: MystbinRequest) -> Response:
    author_: Record | None = request.state.user

    try:
        _data = await request.body()
    except:
        return VariableResponse({"error": "Bad body"}, request, status_code=400)

    payload = payloads.create_struct_from_payload(_data, payloads.PastePost)

    if err := enforce_multipaste_limit(request.app, payload, request):
        return err

    notice = None

    if tokens := await find_discord_tokens(request, payload):
        data = await upload_to_gist(request, "\n".join(tokens))
        notice = f"Discord tokens have been found and uploaded to {data['html_url']}"

    author: int | None = author_["id"] if author_ else None
    paste_id: str = generate_paste_id()

    paste = await request.app.state.db.put_paste(
        paste_id=paste_id,
        pages=payload.files,
        expires=payload.expires,
        author=author,
        password=payload.password,
        origin_ip=respect_dnt(request),
        token_id=request.state.token_id,
        private=payload.private,
    )

    _request_notice = await handle_paste_requests(request, payload, paste_id)
    if _request_notice is not None:
        if notice is not None:
            notice += "\n" + _request_notice
        else:
            notice = _request_notice

    paste["notice"] = notice and notice.strip()
    response = responses.PastePostResponse(**paste)  # type: ignore
    return VariableResponse(response, request)


@router.post("/rich-paste")
@limit("postpastes")
async def post_rich_paste(request: MystbinRequest) -> Response:
    form = await request.form()

    reads: str | None = form.get("data")  # type: ignore
    images: list[UploadFile] | None = form.getlist("images")  # type: ignore
    if not reads:
        return VariableResponse({"error": "multipart.data: `data` field not given"}, request, status_code=400)

    payload = payloads.create_struct_from_payload(reads, payloads.RichPastePost)

    paste_id = generate_paste_id()

    if images and HAS_BUNNYCDN:

        async def _partial(target, spool: UploadFile):
            data = await spool.read()
            await request.app.state.client.put(
                target, data=data, headers=headers
            )  # TODO figure out how to pass spooled object instead of load into memory

        image_idx = {}
        headers = {"Content-Type": "application/octet-stream", "AccessKey": f"{__config['bunny_cdn']['token']}"}
        partials: list[Coroutine] = []

        for index, image in enumerate(images):  # TODO honour config filesize limit
            if not isinstance(image, UploadFile):
                return VariableResponse({"error", f"multipart.images.{index}: Expected an image"}, request)

            origin = image.filename.split(".")[-1]
            new_name = f"{('%032x' % uuid.uuid4().int)[:8]}-{paste_id}.{origin}"
            url = f"https://{__config['bunny_cdn']['hostname']}.b-cdn.net/images/{new_name}"
            image_idx[image.filename] = url
            target = f"https://storage.bunnycdn.com/{__config['bunny_cdn']['hostname']}/images/{new_name}"
            partials.append(_partial(target, image))

        for n, file in enumerate(payload.files):
            if file.attachment is not None:
                if file.attachment not in image_idx:
                    return VariableResponse(
                        {"error": f"files.{n}.attachment: Unkown attachment '{file.attachment}'"}, request
                    )

                file.attachment = image_idx[file.attachment]

        await asyncio.wait(partials, return_when=asyncio.ALL_COMPLETED)

    if err := enforce_multipaste_limit(request.app, payload, request):
        return err

    notice = None

    if tokens := await find_discord_tokens(request, payload):
        gist = await upload_to_gist(request, "\n".join(tokens))
        notice = f"Discord tokens have been found and uploaded to {gist['html_url']}"

    author: int | None = request.state.user["id"] if request.state.user else None

    paste = await request.app.state.db.put_paste(
        paste_id=paste_id,
        pages=payload.files,
        expires=payload.expires,
        author=author,
        password=payload.password,
        origin_ip=respect_dnt(request),
        token_id=request.state.token_id,
    )

    _request_notice = await handle_paste_requests(request, payload, paste_id)
    if _request_notice is not None:
        if notice is not None:
            notice += "\n" + _request_notice
        else:
            notice = _request_notice

    paste["notice"] = notice
    resp = responses.PastePostResponse(**paste)  # type: ignore
    return Response(msgspec.json.encode(resp), status_code=201)


desc = f"""Get a paste by ID.

This endpoint falls under the `getpaste` ratelimit bucket.
The `getpaste` bucket has a default ratelimit of {__config['ratelimits']['getpaste']}, and a ratelimit of {__config['ratelimits']['authed_getpaste']} when signed in
"""


@router.get("/paste/{paste_id}")
@openapi.instance.route(
    openapi.Route(
        "/paste/{paste_id}",
        "GET",
        "Get Paste",
        ["pastes"],
        None,
        [
            openapi.RouteParameter("Password", "string", "password", False, "query"),
            openapi.RouteParameter("Paste ID", "string", "paste_id", False, "path"),
        ],
        {
            201: openapi.Response("Success", openapi.PasteGetResponse),
            400: openapi.BadRequestResponse,
            401: openapi.UnauthorizedResponse,
            404: openapi.NotFoundResponse,
        },
        description=desc,
    )
)
@limit("getpaste")
async def get_paste(request: MystbinRequest) -> VariableResponse:
    paste_id: str = request.path_params["paste_id"]
    password: str | None = request.query_params.get("password")

    paste = await request.app.state.db.get_paste(paste_id, password)
    if paste is None:
        return VariableResponse({"error": "Not Found"}, request, status_code=404)

    if paste["has_password"] and not paste["password_ok"]:
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)

    resp = responses.create_struct(paste, responses.PasteGetResponse)
    return VariableResponse(resp, request)


desc = f"""Get metadata for all pastes for the user you are signed in as via the Authorization header.
* Requires authentication.

This endpoint falls under the `getpaste` ratelimit bucket.
The `getpaste` bucket has a default ratelimit of {__config['ratelimits']['getpaste']}, and a ratelimit of {__config['ratelimits']['authed_getpaste']} when signed in
"""


@router.get("/pastes/@me")
@openapi.instance.route(
    openapi.Route(
        "/pastes/@me",
        "GET",
        "Get User Pastes",
        ["pastes"],
        None,
        [
            openapi.RouteParameter("Limit Per Page (default: 50)", "integer", "limit", False, "query"),
            openapi.RouteParameter("Page", "integer", "page", False, "query"),
        ],
        {
            201: openapi.Response("Success", openapi.PasteGetAllResponse),
            400: openapi.BadRequestResponse,
            401: openapi.UnauthorizedResponse,
        },
        description=desc,
    )
)
@limit("getpaste")
async def get_all_pastes(request: MystbinRequest) -> VariableResponse:
    user = request.state.user
    if not user:
        return VariableResponse(
            {"error": "Unathorized", "notice": "You must be signed in to use this route"}, request, status_code=401
        )

    try:
        limit = int(request.query_params.get("limit", 50))
        page = int(request.query_params.get("page", 1))
    except:
        return VariableResponse({"error": "Bad query parameter passed"}, request, status_code=400)

    if limit < 1 or page < 1:
        return VariableResponse({"error": "limit and page must be greater than 1"}, request, status_code=400)

    pastes = await request.app.state.db.get_all_user_pastes(user["id"], limit, page)
    pastes = [dict(entry) for entry in pastes]

    return VariableResponse({"pastes": pastes}, request)


desc = f"""Edit a paste.
You must be the author of the paste (IE, the paste must be created under your account).

* Requires authentication

This endpoint falls under the `postpastes` ratelimit bucket.
The `postpastes` bucket has a default ratelimit of {__config['ratelimits']['postpastes']}, and a ratelimit of {__config['ratelimits']['authed_postpastes']} when signed in
"""


@router.patch("/paste/{paste_id}")
@openapi.instance.route(
    openapi.Route(
        "/paste/{paste_id}",
        "PATCH",
        "Edit Paste",
        ["pastes"],
        openapi.PastePatch,
        [openapi.RouteParameter("Paste ID", "string", "paste_id", True, "path")],
        {
            204: openapi.Response("Success", None),
            400: openapi.BadRequestResponse,
            401: openapi.UnauthorizedResponse,
            404: openapi.NotFoundResponse,
            422: openapi.ValidationErrorResponse,
        },
        description=desc,
    )
)
@limit("postpastes")
async def edit_paste(request: MystbinRequest) -> VariableResponse | Response:
    author = request.state.user
    if not author:
        return VariableResponse(
            {"error": "Unathorized", "notice": "You must be signed in to use this route"}, request, status_code=401
        )

    paste_id: str = request.path_params["paste_id"]

    try:
        _body = await request.body()
    except:
        return VariableResponse({"error": "Bad body given"}, request, status_code=400)

    payload = payloads.create_struct_from_payload(_body, payloads.PastePatch)

    paste = await request.app.state.db.edit_paste(
        paste_id,
        author=author["id"],
        new_expires=payload.new_expires,
        new_password=payload.new_password,
        files=payload.new_files,
        private=payload.private,
    )
    if paste == 404:
        return VariableResponse(
            {"error": "Paste was not found or you are not it's author"},
            request,
            status_code=404,
        )

    return Response(status_code=204)


desc = f"""Deletes a paste.
You must be the author of the paste (IE, the paste must be created under your account).

* Requires authentication.

This endpoint falls under the `deletepaste` ratelimit bucket.
The `deletepaste` bucket has a default ratelimit of {__config['ratelimits']['deletepaste']}, and a ratelimit of {__config['ratelimits']['authed_deletepaste']} when signed in
"""


@router.delete("/paste/{paste_id}")
@openapi.instance.route(
    openapi.Route(
        "/paste/{paste_id}",
        "DELETE",
        "Delete Paste",
        ["pastes"],
        None,
        [openapi.RouteParameter("Paste ID", "string", "paste_id", True, "path")],
        {204: openapi.Response("Success", None), 400: openapi.BadRequestResponse, 401: openapi.UnauthorizedResponse},
        description=desc,
    )
)
@limit("deletepaste")
async def delete_paste(request: MystbinRequest) -> Response | VariableResponse:
    user = request.state.user
    if not user:
        return VariableResponse(
            {"error": "Unathorized", "notice": "You must be signed in to use this route"}, request, status_code=401
        )

    paste_id: str = request.path_params["paste_id"]

    if not user["admin"]:
        is_owner: bool = await request.app.state.db.ensure_author(paste_id, user["id"])
        if not is_owner:
            return VariableResponse(
                {"error": "Unauthorized", "notice": f"You do not own paste '{paste_id}'"}, request, status_code=401
            )

    deleted: Record = await request.app.state.db.delete_paste(paste_id, user["id"], admin=user["admin"])

    if deleted:
        return Response(status_code=204)
    else:
        return VariableResponse({"error": "Something went wrong"}, request, status_code=500)


desc = f"""Deletes pastes.
You must be the author of the pastes (IE, the pastes must be created under your account).

* Requires authentication.

This endpoint falls under the `deletepaste` ratelimit bucket.
The `deletepaste` bucket has a default ratelimit of {__config['ratelimits']['deletepaste']}, and a ratelimit of {__config['ratelimits']['authed_deletepaste']} when signed in
"""


@router.delete("/paste")
@openapi.instance.route(
    openapi.Route(
        "/paste",
        "DELETE",
        "Delete Many Pastes",
        ["pastes"],
        openapi.PasteDelete,
        [],
        {
            200: openapi.PasteDeleteResponse,
            400: openapi.BadRequestResponse,
            401: openapi.UnauthorizedResponse,
            422: openapi.ValidationErrorResponse,
        },
        description=desc,
    )
)
@limit("deletepaste")
async def delete_pastes(request: MystbinRequest) -> VariableResponse:
    # We will filter out the pastes that are authorized and unauthorized, and return a clear response
    response = {"succeeded": [], "failed": []}

    author: Record = request.state.user
    if not author:
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)

    try:
        _body = await request.body()
    except:
        return VariableResponse({"error": "Bad body given"}, request, status_code=400)

    payload = payloads.create_struct_from_payload(_body, payloads.PasteDelete)

    for paste in payload.pastes:
        if await request.app.state.db.ensure_author(paste, author["id"]):
            response["succeeded"].append(paste)
        else:
            response["failed"].append(paste)

    for paste in response["succeeded"]:
        await request.app.state.db.delete_paste(paste, author["id"], admin=False)

    return VariableResponse(response, request, status_code=200)


desc = f"""
Fetches a raw paste overview.

This endpoint falls under the `getpaste` ratelimit bucket.
The `getpaste` bucket has a default ratelimit of {__config['ratelimits']['getpaste']}, and a ratelimit of {__config['ratelimits']['authed_getpaste']} when signed in
"""


@router.get("/raw/{paste_id}")
@openapi.instance.route(
    openapi.Route(
        "/raw/{paste_id}",
        "GET",
        "Get raw overview",
        ["pastes"],
        None,
        [
            openapi.RouteParameter("Paste ID", "string", "paste_id", True, "path"),
            openapi.RouteParameter("Password", "string", "password", False, "query"),
        ],
        {200: openapi.Response("Success", None, "text/plain"), 401: openapi.Response("Unauthorized", None, "text/plain")},
        description=desc,
    )
)
@limit("getpaste")
async def get_raw_paste_overview(request: MystbinRequest) -> Response:
    paste_id = request.path_params["paste_id"]
    password: str | None = request.query_params.get("password")

    paste = await request.app.state.db.get_raw_paste_info(paste_id, password)
    if paste is None:
        return Response("Not Found", status_code=404)

    if paste["has_password"] and not paste["password_ok"]:
        return Response("Password: failed", status_code=401)

    files = [f"File-Index: {f['n']}\nFile-Name: {f['filename']}\nFile-Chars: {f['charcount']}\n\n" for f in paste["files"]]

    response = f"""Password: {'OK' if paste['has_password'] else 'NA'}
Paste-Id: {paste_id}
Paste-Author: {paste['author_id']}
Paste-Created-At: {paste['created_at']}
Paste-Views: {paste['views']}

{''.join(files)}"""

    return Response(response)


desc = f"""
Fetches raw paste text.

This endpoint falls under the `getpaste` ratelimit bucket.
The `getpaste` bucket has a default ratelimit of {__config['ratelimits']['getpaste']}, and a ratelimit of {__config['ratelimits']['authed_getpaste']} when signed in
"""


@router.get("/raw/{paste_id}/{file_index:int}")
@openapi.instance.route(
    openapi.Route(
        "/raw/{paste_id}/{file_index}",
        "GET",
        "Get raw content",
        ["pastes"],
        None,
        [
            openapi.RouteParameter("Paste ID", "string", "paste_id", True, "path"),
            openapi.RouteParameter("File Index (0-indexed)", "integer", "file_index", True, "path"),
            openapi.RouteParameter("Password", "string", "password", False, "query"),
        ],
        {200: openapi.Response("Success", None, "text/plain"), 401: openapi.Response("Unauthorized", None, "text/plain")},
        description=desc,
    )
)
@limit("getpaste")
async def get_raw_paste_file(request: MystbinRequest) -> Response:
    paste_id = request.path_params["paste_id"]
    file_index = int(request.path_params["file_index"])

    password: str | None = request.query_params.get("password")

    paste = await request.app.state.db.get_raw_paste_info(paste_id, password)
    if paste is None:
        return Response("Not Found", status_code=404)

    if paste["has_password"] and not paste["password_ok"]:
        return Response("Password: failed", status_code=401)

    try:
        return Response(paste["files"][file_index]["content"])
    except IndexError:
        return Response("File index not found", status_code=404)


desc = f"""
A compatibility endpoint to maintain hastbin compatibility. Simply pass the paste body as the request body.
Depreciated in favour of /paste.
This endpoint does not allow for syntax highlighting, multi-file, password protection, expiry, etc. Use the /paste endpoint for these features

This endpoint falls under the `postpastes` ratelimit bucket.
The `postpastes` bucket has a default ratelimit of {__config['ratelimits']['postpastes']}, and a ratelimit of {__config['ratelimits']['authed_postpastes']} when signed in
"""


@router.post("/documents")
@openapi.instance.route(
    openapi.Route(
        "/documents",
        "POST",
        "Hastebin Create Paste",
        ["pastes"],
        None,
        [],
        {
            200: openapi.Response(
                "Success",
                openapi._Component(
                    "HasteCompatComponent",
                    [openapi.ComponentProperty("key", "Key", "string", "Paste ID", True)],
                    example={"key": "FooBar"},
                ),
            ),
            400: openapi.BadRequestResponse,
        },
        description=desc,
        deprecated=True,
    )
)
@limit("postpastes")
async def compat_create_paste(request: MystbinRequest) -> VariableResponse:
    content = await request.body()
    limit = request.app.config["paste"]["character_limit"]
    if len(content) > limit:
        return VariableResponse({"error": f"body: file size exceeds character limit of {limit}"}, request, status_code=400)

    paste: Record = await request.app.state.db.put_paste(
        paste_id=generate_paste_id(),
        pages=[payloads.PasteFile(filename="file.txt", content=content.decode("utf8"))],
        origin_ip=respect_dnt(request),
        token_id=None,
    )
    return VariableResponse({"key": paste["id"]}, request)


### The following handles paste requests

desc = f"""
Create a paste request.
This will create a url that can be passed to an end user.
Additionally, you will receive a websocket URL that will wait for the user to complete the paste, and then will provide you with a paste slug for the created paste.

The generated link expires after 15 minutes.

* Requires authorization

This endpoint falls under the `postpastes` ratelimit bucket.
The `postpastes` bucket has a ratelimit of {__config['ratelimits']['authed_postpastes']} when signed in
"""


@router.post("/paste/request")
@openapi.instance.route(
    openapi.Route(
        "/pastes/request",
        "POST",
        "Create Request",
        ["pastes"],
        None,
        [],
        {
            200: openapi.Response(
                "Success",
                openapi._Component(
                    "PasteRequestSuccessComponent",
                    [
                        openapi.ComponentProperty("edit_url", "Edit URL", "string", required=True),
                        openapi.ComponentProperty("websocket_url", "Websocket URL", "string", required=True),
                    ],
                ),
            ),
            401: openapi.UnauthorizedResponse,
        },
        desc,
        is_body_required=False,
    )
)
@limit("postpastes")
async def request_paste(request: MystbinRequest) -> Response:
    author = request.state.user
    if not author:
        return VariableResponse({"error": "Unauthorized"}, request, status_code=401)

    slug = generate_paste_id(n=4)
    success = False

    for _ in range(3):
        try:
            await request.app.state.db.put_paste_request(slug, author["id"])
            success = True
            break
        except ValueError:
            continue

    if not success:
        return VariableResponse({"error": "Unable to assign a slug. What have you done?"}, request, status_code=500)

    edit_url = yarl.URL(request.app.config["site"]["frontend_site"]).with_path(f"/request/{author['id']}/{slug}")
    websocket_url = yarl.URL(request.app.config["site"]["backend_site"]).with_path(f"/request/{author['id']}/{slug}")

    return VariableResponse({"edit_url": str(edit_url), "websocket_url": str(websocket_url)}, request)


desc = f"""
Open a websocket that sends an event once the paste request has been fulfilled.
This websocket will send a HELLO message: `{{"event": "HELLO"}}`, and then will remain silent until the paste has been fulfilled or expired.

If the paste has been fulfilled, you will receive the following payload: `{{"event": "FULFILLED", "url": "{__config['site']['frontend_site']}/SomeRandomPaste"}}`.
If the paste has timed out, you will receive the following payload: `{{"event": "TIMEOUT"}}`.
If the user/slug you pass is invalid, you will receive `{{"event": "INVALID"}}` directly after HELLO.

This endpoint falls under the `postpastes` ratelimit bucket.
The `postpastes` bucket has a default ratelimit of {__config['ratelimits']['getpaste']}, and a ratelimit of {__config['ratelimits']['authed_getpaste']} when signed in
"""


@router.ws("/request/{user_id:int}/{slug:str}")
@openapi.instance.route(
    openapi.Route(
        "/request/@{user_id}/{slug}",
        "GET",
        "Request WS",
        ["pastes"],
        None,
        [
            openapi.RouteParameter("User ID", "integer", "user_id", True, "path"),
            openapi.RouteParameter("Slug", "string", "slug", True, "path"),
        ],
        {101: openapi.Response("SWITCHING PROTOCOLS", None, "TODO")},
        desc,
        is_body_required=False,
    )
)
@limit("getpaste")
async def request_ws(websocket: MystbinWebsocket):
    slug = websocket.path_params["slug"]
    user_id = int(websocket.path_params["user_id"])
    fulfilled: str | None = await websocket.app.state.db.get_paste_request(slug, user_id)

    await websocket.accept()
    await websocket.send_json({"event": "HELLO"})

    if fulfilled or fulfilled is None:
        payload = {"event": "INVALID", "fulfilled": fulfilled}
        await websocket.send_json(payload)
        await websocket.close(code=HTTPStatus.WS_1000_NORMAL_CLOSURE, reason="Invalid")
        return

    event = asyncio.Future[str]()

    async def wait_for_event(_, __, ___, payload: str) -> None:
        decoded = msgspec.json.decode(payload)
        if decoded["slug"] == slug and decoded["user_id"] == user_id:
            event.set_result(decoded["paste_slug"])

    conn = await websocket.app.state.db.create_listener(wait_for_event)

    while True:
        if websocket.client_state is websocket.client_state.DISCONNECTED:  # client disconnected, clean up and exit
            await websocket.app.state.db.release_listener(conn, wait_for_event)
            event.cancel()
            return

        elif event.done():
            await websocket.app.state.db.release_listener(conn, wait_for_event)
            result = event.result()
            break

        else:
            await asyncio.sleep(1)

    url = yarl.URL(websocket.app.config["site"]["frontend_site"]).with_path(result)
    response = {"event": "FULFILLED", "url": str(url)}

    try:
        await websocket.send(response)
        await websocket.close(
            code=HTTPStatus.WS_1000_NORMAL_CLOSURE,
            reason="https://media.discordapp.net/attachments/336642776609456130/816774571772477500/1006_socket_disconnected-s.png",
        )  # we'll see how long until someone notices this
    except:
        pass


@router.get("/request/{user_id:int}/{slug:str}/sse")  # this needs some debugging, seems like uvicorn doesnt like it
@limit("getpaste")
async def request_sse(request: MystbinRequest) -> Response | EventSourceResponse:
    slug = request.path_params["slug"]
    user_id = int(request.path_params["user_id"])
    fulfilled = await request.app.state.db.get_paste_request(slug, user_id)

    if fulfilled is None:
        return Response(status_code=404)
    elif fulfilled:
        return Response(f"FULFILLED:{fulfilled}", status_code=400)

    event = asyncio.Future[str]()

    async def wait_for_event(_, __, ___, payload: str) -> None:
        decoded = msgspec.json.decode(payload)
        if decoded["slug"] == slug and decoded["user_id"] == user_id:
            event.set_result(decoded["paste_slug"])

    async def generate_send_event():
        try:
            slug = await asyncio.wait_for(event, None)
        except asyncio.CancelledError:
            await request.app.state.db.release_listener(conn, wait_for_event)
            return
        except:
            resp = "ERROR"
        else:
            url = yarl.URL(request.app.config["site"]["frontend_site"]).with_path(slug)
            resp = "FULFILLED:" + str(url)

        try:
            yield resp
        finally:
            await request.app.state.db.release_listener(conn, wait_for_event)

    conn = await request.app.state.db.create_listener(wait_for_event)
    return EventSourceResponse(generate_send_event())


request_sse.SSE = (
    True  # SSE endpoints cant have logging applied (response unfurling), so this tells the ratelimiter not to log at all
)
