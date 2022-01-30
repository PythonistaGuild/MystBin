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
import datetime
import pathlib
import re
from random import sample
from typing import Dict, List, Optional, Union

from asyncpg import Record
from fastapi import APIRouter, Request, Security
from fastapi.responses import UJSONResponse
from models import errors, payloads, responses
from utils.db import _recursive_hook as recursive_hook
from utils.ratelimits import limit

_WORDS_LIST = open(pathlib.Path("utils/words.txt")).readlines()
word_list = [word.title() for word in _WORDS_LIST if len(word) > 3]
del _WORDS_LIST

TOKEN_RE = re.compile(r"[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27}")

router = APIRouter()


def generate_paste_id():
    """Generate three random words."""
    word_samples = sample(word_list, 3)
    return "".join(word_samples).replace("\n", "")


def enforce_paste_limit(app, paste: payloads.PastePost, n=1):
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


def enforce_multipaste_limit(app, pastes: payloads.ListedPastePut):
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


async def upload_to_gist(request: Request, tokens: str):
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


async def find_discord_tokens(request: Request, pastes: Union[payloads.ListedPastePut, payloads.PastePost]):
    if not request.app.config["apps"].get("github_bot_token", None):
        return None

    tokens = []

    try:
        for file in pastes.files:
            v = TOKEN_RE.findall(file.content)
            if v:
                tokens += v
    except AttributeError:
        return TOKEN_RE.findall(pastes.content)

    return tokens or None


@router.post(
    "/paste",
    tags=["pastes"],
    response_model=responses.PastePostResponse,
    responses={
        201: {"model": responses.PastePostResponse},
        400: {"content": {"application/json": {"example": {"error": "files.length: You have provided a bad paste"}}}},
    },
    status_code=201,
    name="Create a paste with a single file.",
)
@limit("postpastes", "zones.pastes.post")
async def post_paste(
    request: Request,
    payload: payloads.PastePost,
) -> Union[Dict[str, Optional[Union[str, int, datetime.datetime]]], UJSONResponse]:
    """Post a paste to MystBin.
    This endpoint accepts a single file."""
    author: Record = request.state.user

    author: Optional[int] = author["id"] if author else None

    if err := enforce_paste_limit(request.app, payload):
        return err

    notice = None

    if tokens := await find_discord_tokens(request, payload):
        data = await upload_to_gist(request, "\n".join(tokens))
        notice = f"Discord tokens have been found and uploaded to {data['html_url']}"

    paste = await request.app.state.db.put_paste(
        paste_id=generate_paste_id(),
        content=payload.content,
        filename=payload.filename,
        author=author,
        syntax=payload.syntax,
        expires=payload.expires,
        password=payload.password,
        origin_ip=request.headers.get("x-forwarded-for", request.client.host)
        if request.app.config["paste"]["log_ip"]
        else None,
    )
    paste["notice"] = notice

    return UJSONResponse(paste)


@router.put(
    "/paste",
    tags=["pastes"],
    response_model=responses.PastePostResponse,
    responses={
        201: {"model": responses.PastePostResponse},
        400: {"content": {"application/json": {"example": {"error": "files.length: You have provided a bad paste"}}}},
    },
    status_code=201,
    name="Create a paste with multiple files.",
)
@limit("postpastes", "zones.pastes.post")
async def put_pastes(
    request: Request,
    payload: payloads.ListedPastePut,
) -> Union[Dict[str, Optional[Union[str, int, datetime.datetime]]], UJSONResponse]:
    """Post a paste to MystBin.
    This endpoint accepts a single or many files."""

    author: Record = request.state.user

    if err := enforce_multipaste_limit(request.app, payload):
        return err

    notice = None

    if tokens := await find_discord_tokens(request, payload):
        data = await upload_to_gist(request, "\n".join(tokens))
        notice = f"Discord tokens have been found and uploaded to {data['html_url']}"

    author: Optional[int] = author["id"] if author else None

    paste = await request.app.state.db.put_pastes(
        paste_id=generate_paste_id(),
        pages=payload.files,
        expires=payload.expires,
        author=author,
        password=payload.password,
        origin_ip=request.headers.get("x-forwarded-for", request.client.host)
        if request.app.config["paste"]["log_ip"]
        else None,
    )

    paste["notice"] = notice
    paste = responses.PastePostResponse(**paste)
    paste = recursive_hook(paste.dict())
    return UJSONResponse(paste)


@router.get(
    "/paste/{paste_id}",
    tags=["pastes"],
    response_model=responses.PasteGetResponse,
    responses={
        200: {"model": responses.PasteGetResponse},
        401: {"model": errors.Unauthorized},
        404: {"model": errors.NotFound},
    },
    name="Retrieve paste file(s)",
)
@limit("getpaste", "zones.pastes.get")
async def get_paste(request: Request, paste_id: str, password: Optional[str] = None) -> UJSONResponse:
    """Get a paste from MystBin."""
    paste = await request.app.state.db.get_paste(paste_id, password)
    if paste is None:
        return UJSONResponse({"error": "Not Found"}, status_code=404)

    if paste["has_password"] and not paste["password_ok"]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    resp = responses.PasteGetResponse(**paste)
    return UJSONResponse(recursive_hook(resp.dict()))


@router.get(
    "/pastes",
    tags=["pastes"],
    response_model=List[responses.PasteGetAllResponse],
    responses={
        200: {"model": Optional[List[responses.PasteGetAllResponse]]},
        403: {"model": errors.Forbidden},
    },
    name="Get multiple pastes",
)
@limit("getpaste", "zones.pastes.get")
async def get_all_pastes(
    request: Request,
    limit: Optional[int] = None,
) -> Union[UJSONResponse, Dict[str, List[Dict[str, str]]]]:
    """Get all pastes for a specified author.
    * Requires authentication.
    """
    user = request.state.user
    if not user:
        return UJSONResponse({"error": "Forbidden"}, status_code=403)

    pastes = await request.app.state.db.get_all_user_pastes(user["id"], limit)
    pastes = [dict(entry) for entry in pastes]

    return UJSONResponse({"pastes": pastes})


@router.put(
    "/paste/{paste_id}",
    tags=["pastes"],
    response_model=responses.PastePatchResponse,
    responses={
        200: {"model": responses.PastePatchResponse},
        401: {"model": errors.Unauthorized},
        403: {"model": errors.Forbidden},
        404: {"model": errors.NotFound},
    },
    name="Edit paste",
)
@router.patch(
    "/paste/{paste_id}",
    tags=["pastes"],
    response_model=responses.PastePatchResponse,
    responses={
        200: {"model": responses.PastePatchResponse},
        401: {"model": errors.Unauthorized},
        403: {"model": errors.Forbidden},
        404: {"model": errors.NotFound},
    },
    name="Edit paste",
)
@limit("postpastes", "zones.pastes.post")
async def edit_paste(
    request: Request,
    paste_id: str,
    payload: payloads.PastePatch,
) -> Union[UJSONResponse, Dict[str, Optional[Union[str, int, datetime.datetime]]]]:
    """Edit a paste on MystBin.
    * Requires authentication.
    """
    author = request.state.user
    if not author:
        return UJSONResponse({"error": "Forbidden"}, status_code=403)

    paste: Union[Record, int] = await request.app.state.db.edit_paste(
        paste_id,
        author["id"],
        payload.new_content,
        payload.new_expires,
        payload.new_nick,
    )
    if not paste or paste == 404:
        return UJSONResponse(
            {"error": "Paste was not found or you are not it's author."},
            status_code=404,
        )

    return UJSONResponse(dict(paste[0]))


@router.delete(
    "/paste/{paste_id}",
    tags=["pastes"],
    responses={
        200: {"content": {"application/json": {"example": {"deleted": "SomePasteID"}}}},
        401: {"model": errors.Unauthorized},
        403: {"model": errors.Forbidden},
    },
    status_code=200,
    name="Delete paste",
)
@limit("deletepaste", "zones.pastes.delete")
async def delete_paste(request: Request, paste_id: str = None) -> Union[UJSONResponse, Dict[str, str]]:
    """Deletes pastes on MystBin.
    * Requires authentication.
    """
    user = request.state.user
    if not user:
        return UJSONResponse({"error": "Forbidden"}, status_code=403)

    if not user["admin"]:
        is_owner: bool = await request.app.state.db.ensure_author(paste_id, user["id"])
        if not is_owner:
            return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    deleted: Record = await request.app.state.db.delete_paste(paste_id, user["id"], admin=False)

    return UJSONResponse({"deleted": deleted["id"]}, status_code=200)


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
    name="Delete pastes",
)
@limit("deletepaste", "zones.pastes.delete")
async def delete_pastes(
    request: Request,
    payload: payloads.PasteDelete,
) -> Union[UJSONResponse, Dict[str, List[str]]]:
    """Deletes pastes on MystBin.
    * Requires authentication.
    """
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


@router.post(
    "/documents",
    tags=["pastes"],
    deprecated=True,
    response_description='{"key": "string"}',
)
@limit("postpastes", "zones.pastes.post")
async def compat_create_paste(request: Request):
    """
    A compatibility endpoint to maintain hastbin compat. Depreciated in favour of /paste
    This endpoint does not allow for syntax highlighting, multi-file, password protection, expiry, etc. Use the /paste endpoint for these features
    """
    content = await request.body()
    paste: Record = await request.app.state.db.put_paste(
        paste_id=generate_paste_id(),
        content=content,
        origin_ip=request.headers.get("x-forwarded-for", request.client.host)
        if request.app.config["paste"]["log_ip"]
        else None,
    )
    return UJSONResponse({"key": paste["id"]})
