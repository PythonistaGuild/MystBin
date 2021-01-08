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
from random import sample
from typing import Dict, List, Optional, Union

from asyncpg import Record
from fastapi import APIRouter, Request, Security
from fastapi.responses import UJSONResponse
from fastapi.security import HTTPBearer
from models import errors, payloads, responses
from utils.ratelimits import limit

WORDS_LIST = open(pathlib.Path("utils/words.txt")).readlines()


router = APIRouter()
auth_model = HTTPBearer()
optional_auth_model = HTTPBearer(auto_error=False)


def generate_paste_id():
    """Generate three random words."""
    word_list = [word.title() for word in WORDS_LIST if len(word) > 3]
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
        return UJSONResponse(
            {"error": "files.length: you have not provided any files"}, status_code=400
        )
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


@router.post(
    "/paste",
    tags=["pastes"],
    response_model=responses.PastePostResponse,
    responses={
        201: {"model": responses.PastePostResponse},
        400: {
            "content": {
                "application/json": {
                    "example": {"error": "files.length: You have provided a bad paste"}
                }
            }
        },
    },
    status_code=201,
    name="Create a paste with a single file.",
)
@limit("postpastes", "zones.pastes.post")
async def post_paste(
    request: Request,
    payload: payloads.PastePost,
    authorization: Optional[str] = Security(optional_auth_model),
) -> Union[Dict[str, Optional[Union[str, int, datetime.datetime]]], UJSONResponse]:
    """Post a paste to MystBin.
    This endpoint accepts a single file."""
    author = None

    if authorization and authorization.credentials:
        author = await request.app.state.db.get_user(token=authorization.credentials)
        if not author or author == 400:
            return UJSONResponse(
                {"error": "Token provided but no valid user found"}, status_code=403
            )
        elif author == 401:
            return UJSONResponse(
                {"error": "Token provided was not valid"}, status_code=403
            )
        elif not isinstance(author, Record):
            raise ValueError("the database returned a bad response")

    author: Optional[int] = author.get("id", None) if author else None

    if err := enforce_paste_limit(request.app, payload):
        return err

    paste: Record = await request.app.state.db.put_paste(
        paste_id=generate_paste_id(),
        content=payload.content,
        filename=payload.filename,
        author=author,
        syntax=payload.syntax,
        expires=payload.expires,
        password=payload.password,
    )

    return UJSONResponse(dict(paste))


@router.put(
    "/paste",
    tags=["pastes"],
    response_model=responses.PastePostResponse,
    responses={
        201: {"model": responses.PastePostResponse},
        400: {
            "content": {
                "application/json": {
                    "example": {"error": "files.length: You have provided a bad paste"}
                }
            }
        },
    },
    status_code=201,
    name="Create a paste with multiple files.",
)
@limit("postpastes", "zones.pastes.post")
async def put_pastes(
    request: Request,
    payload: payloads.ListedPastePut,
    authorization: Optional[str] = Security(optional_auth_model),
) -> Union[Dict[str, Optional[Union[str, int, datetime.datetime]]], UJSONResponse]:
    """Post a paste to MystBin.
    This endpoint accepts a single or many files."""

    author = None

    if authorization and authorization.credentials:
        author = await request.app.state.db.get_user(token=authorization.credentials)
        if not author:
            return UJSONResponse(
                {"error": "Token provided but no valid user found."}, status_code=403
            )

    if err := enforce_multipaste_limit(request.app, payload):
        return err

    author: Optional[int] = author.get("id", None) if author else None

    pastes = await request.app.state.db.put_pastes(
        paste_id=generate_paste_id(),
        workspace_name=payload.workspace_name,
        pages=payload.files,
        expires=payload.expires,
        author=author,
        password=payload.password,
    )

    return UJSONResponse(pastes)


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
async def get_paste(
    request: Request, paste_id: str, password: Optional[str] = None
) -> Union[UJSONResponse, Dict[str, Optional[Union[str, int, datetime.datetime]]]]:
    """Get a paste from MystBin."""
    pastes = await request.app.state.db.get_paste(paste_id, password)
    if pastes is None:
        return UJSONResponse({"error": "Not Found"}, status_code=404)

    return UJSONResponse(pastes)


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
    authorization: str = Security(auth_model),
) -> Union[UJSONResponse, Dict[str, List[Dict[str, str]]]]:
    """Get all pastes for a specified author.
    * Requires authentication.
    """
    if not authorization:
        return UJSONResponse({"error": "Forbidden"}, status_code=403)

    author: Record = await request.app.state.db.get_user(
        token=authorization.credentials
    )

    pastes = await request.app.state.db.get_all_pastes(author["id"], limit)
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
    authorization: str = Security(auth_model),
) -> Union[UJSONResponse, Dict[str, Optional[Union[str, int, datetime.datetime]]]]:
    """Edit a paste on MystBin.
    * Requires authentication.
    """
    if not authorization:
        return UJSONResponse({"error": "Forbidden"}, status_code=403)

    author: Record = await request.app.state.db.get_user(
        token=authorization.credentials
    )
    if not author or isinstance(author, int):
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

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
async def delete_paste(
    request: Request, paste_id: str = None, authorization: str = Security(auth_model)
) -> Union[UJSONResponse, Dict[str, str]]:
    """Deletes pastes on MystBin.
    * Requires authentication.
    """
    if not authorization:
        return UJSONResponse({"error": "Forbidden"}, status_code=403)

    author: Union[Record, int] = await request.app.state.db.get_user(
        token=authorization.credentials
    )
    if not author or author in [400, 401]:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    is_owner: bool = await request.app.state.db.ensure_author(paste_id, author["id"])
    if not is_owner:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    deleted: Record = await request.app.state.db.delete_paste(
        paste_id, author["id"], admin=False
    )

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
    authorization: str = Security(auth_model),
) -> Union[UJSONResponse, Dict[str, List[str]]]:
    """Deletes pastes on MystBin.
    * Requires authentication.
    """
    # We will filter out the pastes that are authorized and unauthorized, and return a clear response
    response = {"succeeded": [], "failed": []}

    author: Union[Record, int] = await request.app.state.db.get_user(
        token=authorization.credentials
    )
    if not author or isinstance(author, int):
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    for paste in payload.pastes:
        if await request.app.state.db.ensure_author(paste, author["id"]):
            response["succeeded"].append(paste)
        else:
            response["failed"].append(paste)

    for paste in response["succeeded"]:
        await request.app.state.db.delete_paste(paste, author["id"], admin=False)

    return UJSONResponse(response, status_code=200)
