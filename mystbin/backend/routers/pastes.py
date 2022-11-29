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
import datetime
import json
import pathlib
import re
import uuid
from random import sample
from typing import Coroutine

import pydantic
from asyncpg import Record
from fastapi import APIRouter, File, Response, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import UJSONResponse
from models import errors, payloads, responses

from mystbin_models import MystbinRequest
from utils.db import _recursive_hook as recursive_hook
from utils.ratelimits import limit


try:
    import ujson

    _loads = ujson.loads
except ModuleNotFoundError:
    import json

    _loads = json.loads


_WORDS_LIST = open(pathlib.Path("utils/words.txt")).readlines()
word_list = [word.title() for word in _WORDS_LIST if len(word) > 3]
del _WORDS_LIST

TOKEN_RE = re.compile(r"[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27}")

router = APIRouter()

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


def enforce_paste_limit(app, paste: payloads.PasteFile, n=1):
    charlim = app.config["paste"]["character_limit"]
    if len(paste.content) > charlim:
        return UJSONResponse(
            {
                "error": f"files.{n}.content ({paste.filename}): maximum length per file is {charlim} characters. "
                f"You are {len(paste.content)-charlim} characters over the limit"
            },
            status_code=400,
        )

    return None


def enforce_multipaste_limit(app, pastes: payloads.PastePut):
    filelim = app.config["paste"]["character_limit"]
    if len(pastes.files) < 1:
        return UJSONResponse({"error": "files.length: you have not provided any files"}, status_code=400)
    if len(pastes.files) > filelim:
        return UJSONResponse(
            {
                "error": f"files.length: maximum file count is {filelim} files. You are "
                f"{len(pastes.files) - filelim} files over the limit"
            },
            status_code=400,
        )

    for n, file in enumerate(pastes.files):
        if err := enforce_paste_limit(app, file, n):
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


async def find_discord_tokens(request: MystbinRequest, pastes: payloads.PastePut):
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
        return request.headers.get("X-Forwarded-For", request.client.host)

    return None


desc = f"""Post a paste.

This endpoint falls under the `postpastes` ratelimit bucket.
The `postpastes` bucket has a default ratelimit of {__config['ratelimits']['postpastes']}, and a ratelimit of {__config['ratelimits']['authed_postpastes']} when signed in
"""


@router.put(
    "/paste",
    tags=["pastes"],
    response_model=responses.PastePostResponse,
    responses={
        201: {"model": responses.PastePostResponse},
        400: {"content": {"application/json": {"example": {"error": "files.length: You have provided too many files"}}}},
    },
    status_code=201,
    name="Create paste",
    description=desc,
)
@limit("postpastes")
async def put_pastes(
    request: MystbinRequest,
    payload: payloads.PastePut,
) -> dict[str, str | int | datetime.datetime | None] | UJSONResponse:
    author_: Record | None = request.state.user

    if err := enforce_multipaste_limit(request.app, payload):
        return err

    notice = None

    if tokens := await find_discord_tokens(request, payload):
        data = await upload_to_gist(request, "\n".join(tokens))
        notice = f"Discord tokens have been found and uploaded to {data['html_url']}"

    author: int | None = author_["id"] if author_ else None

    paste = await request.app.state.db.put_paste(
        paste_id=generate_paste_id(),
        pages=payload.files,
        expires=payload.expires,
        author=author,
        password=payload.password,
        origin_ip=respect_dnt(request),
    )

    paste["notice"] = notice
    paste = responses.PastePostResponse(**paste)  # type: ignore # this is a problem for future me #TODO
    paste = recursive_hook(paste.dict())
    return UJSONResponse(paste, status_code=201)


@router.post(
    "/rich-paste",
    tags=["pastes"],
    response_model=responses.PastePostResponse,
    responses={
        201: {"model": responses.PastePostResponse},
        400: {"content": {"application/json": {"example": {"error": "files.length: You have provided too many files"}}}},
    },
    status_code=201,
    name="Create Rich Paste",
)
@limit("postpastes")
async def post_rich_paste(
    request: MystbinRequest,
    data: bytes = File(None, max_length=(__config["paste"]["character_limit"] * __config["paste"]["file_limit"]) + 500),
    images: list[UploadFile] = File(None),
) -> UJSONResponse:

    reads = data
    try:
        payload = payloads.RichPastePost.parse_raw(reads, content_type="application/json")
    except pydantic.ValidationError as e:
        return UJSONResponse({"detail": e.errors()}, status_code=422)
    except:
        return UJSONResponse({"error": f"multipart.section.data: Invalid JSON"})

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

        for image in images:  # TODO honour config filesize limit
            origin = image.filename.split(".")[-1]
            new_name = f"{('%032x' % uuid.uuid4().int)[:8]}-{paste_id}.{origin}"
            url = f"https://{__config['bunny_cdn']['hostname']}.b-cdn.net/images/{new_name}"
            image_idx[image.filename] = url
            target = f"https://storage.bunnycdn.com/{__config['bunny_cdn']['hostname']}/images/{new_name}"
            partials.append(_partial(target, image))

        for n, file in enumerate(payload.files):
            if file.attachment is not None:
                if file.attachment not in image_idx:
                    return UJSONResponse({"error": f"files.{n}.attachment: Unkown attachment '{file.attachment}'"})

                file.__dict__["attachment"] = image_idx[file.attachment]

        await asyncio.wait(partials, return_when=asyncio.ALL_COMPLETED)

    if err := enforce_multipaste_limit(request.app, payload):
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
    )

    paste["notice"] = notice
    paste = responses.PastePostResponse(**paste)  # type: ignore # this is a problem for future me #TODO
    paste = recursive_hook(paste.dict())
    return UJSONResponse(paste, status_code=201)


desc = f"""Get a paste by ID.

This endpoint falls under the `getpaste` ratelimit bucket.
The `getpaste` bucket has a default ratelimit of {__config['ratelimits']['getpaste']}, and a ratelimit of {__config['ratelimits']['authed_getpaste']} when signed in
"""


@router.get(
    "/paste/{paste_id}",
    tags=["pastes"],
    response_model=responses.PasteGetResponse,
    responses={
        200: {"model": responses.PasteGetResponse},
        401: {"model": errors.Unauthorized},
        404: {"model": errors.NotFound},
    },
    name="Get paste",
    description=desc,
)
@limit("getpaste")
async def get_paste(request: MystbinRequest, paste_id: str, password: str | None = None) -> UJSONResponse:
    paste = await request.app.state.db.get_paste(paste_id, password)
    if paste is None:
        return UJSONResponse({"error": "Not Found"}, status_code=404)

    if paste["has_password"] and not paste["password_ok"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    resp = responses.PasteGetResponse(**paste)
    return UJSONResponse(recursive_hook(resp.dict()))


desc = f"""Get all pastes for the user you are signed in as via the Authorization header.
* Requires authentication.

This endpoint falls under the `getpaste` ratelimit bucket.
The `getpaste` bucket has a default ratelimit of {__config['ratelimits']['getpaste']}, and a ratelimit of {__config['ratelimits']['authed_getpaste']} when signed in
"""


@router.get(
    "/pastes/@me",
    tags=["pastes"],
    response_model=list[responses.PasteGetAllResponse],
    responses={
        200: {"model": list[responses.PasteGetAllResponse] | None},
        400: {"content": {"application/json": {"example": {"error": "You have provided an invalid query argument"}}}},
        401: {"model": errors.Unauthorized},
    },
    name="Get user pastes",
    description=desc,
)
@limit("getpaste")
async def get_all_pastes(
    request: MystbinRequest, limit: int = 50, page: int = 1
) -> UJSONResponse | dict[str, list[dict[str, str]]]:
    user = request.state.user
    if not user:
        return UJSONResponse({"error": "Unathorized", "notice": "You must be signed in to use this route"}, status_code=401)

    if limit < 1 or page < 1:
        return UJSONResponse({"error": "limit and page must be greater than 1"}, status_code=400)

    pastes = await request.app.state.db.get_all_user_pastes(user["id"], limit, page)
    pastes = [dict(entry) for entry in pastes]

    return UJSONResponse({"pastes": jsonable_encoder(pastes)})


desc = f"""Edit a paste.
You must be the author of the paste (IE, the paste must be created under your account).

* Requires authentication

This endpoint falls under the `postpastes` ratelimit bucket.
The `postpastes` bucket has a default ratelimit of {__config['ratelimits']['postpastes']}, and a ratelimit of {__config['ratelimits']['authed_postpastes']} when signed in
"""


@router.patch(
    "/paste/{paste_id}",
    tags=["pastes"],
    responses={
        204: {},
        401: {"model": errors.Unauthorized},
        403: {"model": errors.Forbidden},
        404: {"model": errors.NotFound},
    },
    name="Edit paste",
    description=desc,
)
@limit("postpastes")
async def edit_paste(
    request: MystbinRequest,
    paste_id: str,
    payload: payloads.PastePatch,
) -> UJSONResponse | Response:
    author = request.state.user
    if not author:
        return UJSONResponse({"error": "Unathorized", "notice": "You must be signed in to use this route"}, status_code=401)

    paste = await request.app.state.db.edit_paste(
        paste_id,
        author=author["id"],
        new_expires=payload.new_expires,
        new_password=payload.new_password,
        files=payload.new_files,
    )
    if paste == 404:
        return UJSONResponse(
            {"error": "Paste was not found or you are not it's author."},
            status_code=404,
        )

    return Response(status_code=204)


desc = f"""Deletes a paste.
You must be the author of the paste (IE, the paste must be created under your account).

* Requires authentication.

This endpoint falls under the `deletepaste` ratelimit bucket.
The `deletepaste` bucket has a default ratelimit of {__config['ratelimits']['deletepaste']}, and a ratelimit of {__config['ratelimits']['authed_deletepaste']} when signed in
"""


@router.delete(
    "/paste/{paste_id}",
    tags=["pastes"],
    responses={
        200: {"content": {"application/json": {"example": {"deleted": "SomePasteID"}}}},
        401: {"model": errors.Unauthorized},
    },
    status_code=200,
    name="Delete paste",
    description=desc,
)
@limit("deletepaste")
async def delete_paste(request: MystbinRequest, paste_id: str) -> UJSONResponse | dict[str, str]:
    user = request.state.user
    if not user:
        return UJSONResponse({"error": "Unathorized", "notice": "You must be signed in to use this route"}, status_code=401)

    if not user["admin"]:
        is_owner: bool = await request.app.state.db.ensure_author(paste_id, user["id"])
        if not is_owner:
            return UJSONResponse({"error": "Unauthorized", "notice": f"You do not own paste '{paste_id}'"}, status_code=401)

    deleted: Record = await request.app.state.db.delete_paste(paste_id, user["id"], admin=False)

    return UJSONResponse({"deleted": deleted["id"]}, status_code=200)


desc = f"""Deletes pastes.
You must be the author of the pastes (IE, the pastes must be created under your account).

* Requires authentication.

This endpoint falls under the `deletepaste` ratelimit bucket.
The `deletepaste` bucket has a default ratelimit of {__config['ratelimits']['deletepaste']}, and a ratelimit of {__config['ratelimits']['authed_deletepaste']} when signed in
"""


@router.delete(
    "/paste",
    tags=["pastes"],
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "succeeded": ["SomePasteID"],
                        "failed": ["OtherPasteID"],
                    }
                }
            }
        },
        401: {"model": errors.Unauthorized},
        403: {"model": errors.Forbidden},
    },
    status_code=200,
    name="Bulk delete pastes",
    description=desc,
)
@limit("deletepaste")
async def delete_pastes(
    request: MystbinRequest,
    payload: payloads.PasteDelete,
) -> UJSONResponse | dict[str, list[str]]:
    # We will filter out the pastes that are authorized and unauthorized, and return a clear response
    response = {"succeeded": [], "failed": []}

    author: Record = request.state.user
    if not author:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    for paste in payload.pastes:
        if await request.app.state.db.ensure_author(paste, author["id"]):
            response["succeeded"].append(paste)
        else:
            response["failed"].append(paste)

    for paste in response["succeeded"]:
        await request.app.state.db.delete_paste(paste, author["id"], admin=False)

    return UJSONResponse(response, status_code=200)


desc = f"""
A compatibility endpoint to maintain hastbin compatibility. Depreciated in favour of /paste
This endpoint does not allow for syntax highlighting, multi-file, password protection, expiry, etc. Use the /paste endpoint for these features

This endpoint falls under the `postpastes` ratelimit bucket.
The `postpastes` bucket has a default ratelimit of {__config['ratelimits']['postpastes']}, and a ratelimit of {__config['ratelimits']['authed_postpastes']} when signed in
"""


@router.post(
    "/documents",
    tags=["pastes"],
    deprecated=True,
    responses={
        200: {"application/json": {"example": {"key": "string"}, "description": "A key containing the slug for your paste"}},
        400: {"application/json": {"example": {"error": "You have provided an invalid paste body"}}},
    },
    name="Hastebin create paste",
    description=desc,
)
@limit("postpastes")
async def compat_create_paste(request: MystbinRequest):
    content = await request.body()
    limit = request.app.config["paste"]["character_limit"]
    if len(content) > limit:
        return UJSONResponse({"error": f"body: file size exceeds character limit of {limit}"}, status_code=400)

    paste: Record = await request.app.state.db.put_paste(
        paste_id=generate_paste_id(),
        pages=[payloads.PasteFile(filename="file.txt", content=content.decode("utf8"))],
        origin_ip=respect_dnt(request),
    )
    return UJSONResponse({"key": paste["id"]})
