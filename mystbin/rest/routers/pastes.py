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
from fastapi import APIRouter, Depends, Request
from fastapi.responses import UJSONResponse
from fastapi.security import HTTPBearer

from ..models import errors, payloads, responses

WORDS_LIST = open(pathlib.Path("mystbin/rest/utils/words.txt")).readlines()


router = APIRouter()
auth_model = HTTPBearer()
optional_auth_model = HTTPBearer(auto_error=False)


def generate_paste_id():
    """Generate three random words."""
    word_list = [word.title() for word in WORDS_LIST if len(word) > 3]
    word_samples = sample(word_list, 3)
    return "".join(word_samples).replace("\n", "")


@router.post("/paste", tags=["pastes"], response_model=responses.PastePostResponse, responses={
    201: {"model": responses.PastePostResponse}},
    status_code=201,
    name="Create a paste with a single file."
)
async def post_paste(request: Request, payload: payloads.PastePost, authorization: Optional[str] = Depends(optional_auth_model)) -> Dict[str, Optional[Union[str, int, datetime.datetime]]]:
    """Post a paste to MystBin.
    This endpoint accepts a single file."""
    author = None

    if authorization and authorization.credentials:
        author: Record = await request.app.state.db.get_user(token=authorization.credentials)
        if not author:
            return UJSONResponse({"error": "Token provided but no valid user found."}, status_code=403)

    author: Optional[int] = author.get("id", None) if isinstance(
        author, Record) else None

    paste: Record = await request.app.state.db.put_paste(paste_id=generate_paste_id(),
                                                         content=payload.content,
                                                         filename=payload.filename,
                                                         author=author,
                                                         syntax=payload.syntax,
                                                         expires=payload.expires,
                                                         password=payload.password)

    return dict(paste)


@router.put("/paste", tags=["pastes"], response_model=responses.PastePostResponse, responses={
    201: {"model": responses.PastePostResponse},
    400: {"content": {"application/json": {"example": {"error": "You have not supplied any files to insert into a paste."}}}},
},
    status_code=201,
    name="Create a paste with multiple files.")
async def post_pastes(request: Request, payload: payloads.ListedPastePut, authorization: Optional[str] = Depends(optional_auth_model)) -> Dict[str, Optional[Union[str, int, datetime.datetime]]]:
    """Post a paste to MystBin.
    This endpoint accepts a single or many files."""
    ...
    if authorization and authorization.credentials:
        author: Record = await request.app.state.db.get_user(token=authorization.credentials)
        if not author:
            return UJSONResponse({"error": "Token provided but no valid user found."}, status_code=403)

    if not payload.data or len(payload.data) < 1:
        return UJSONResponse({"error": "You have not supplied any files to insert into a paste."}, status_code=400)

    author: Optional[int] = author.get("id", None) if isinstance(
        author, Record) else None

    pastes: List[Record] = await request.app.state.db.put_pastes(paste_id=generate_paste_id(),
                                                                 workspace_name=payload.workspace_name,
                                                                 pages=payload.files,
                                                                 expires=payload.expires,
                                                                 author=author,
                                                                 password=payload.password)

    return dict(pastes)


@router.get("/paste/{paste_id}", tags=["pastes"], response_model=List[responses.PasteGetResponse], responses={
    200: {"model": List[responses.PasteGetResponse]},
    401: {"model": errors.Unauthorized},
    404: {"model": errors.NotFound}},
    name="Retrieve paste file(s)"
)
async def get_paste(request: Request, paste_id: str, password: Optional[str] = None) -> Union[UJSONResponse, Dict[str, Optional[Union[str, int, datetime.datetime]]]]:
    """Get a paste from MystBin."""
    pastes: List[Record] = await request.app.state.db.get_paste(paste_id, password)
    if pastes is None:
        return UJSONResponse({"error": "Not Found"}, status_code=404)

    return_pastes = []
    for paste in pastes:
        # TODO: New paste authentication logic AND transformation logic if needed?
        # if paste['has_password'] and not paste['password_ok']:
        #     return UJSONResponse({"error": "Unauthorized"}, status_code=401)
        return_pastes.append(dict(paste))

    # TODO so far we still need `content` returned
    return return_pastes


@router.get("/pastes", tags=["pastes"], response_model=List[responses.PasteGetAllResponse], responses={
    200: {"model": Optional[List[responses.PasteGetAllResponse]]},
    403: {"model": errors.Forbidden}},
    name="Get multiple pastes"
)
async def get_all_pastes(request: Request, limit: Optional[int] = None, authorization: str = Depends(auth_model)) -> Union[UJSONResponse, Dict[str, List[Dict[str, str]]]]:
    """Get all pastes for a specified author.
    * Requires authentication.
    """
    if not authorization:
        return UJSONResponse({"error": "Forbidden"}, status_code=403)

    author: Record = await request.app.state.db.get_user(token=authorization.credentials)

    pastes: Record = await request.app.state.db.get_all_pastes(author['id'], limit)
    pastes = [dict(entry) for entry in pastes]

    return {"pastes": pastes}


@router.put("/paste/{paste_id}", tags=["pastes"], response_model=responses.PastePatchResponse, responses={
    200: {"model": responses.PastePatchResponse},
    401: {"model": errors.Unauthorized},
    403: {"model": errors.Forbidden},
    404: {"model": errors.NotFound}},
    name="Edit paste"
)
@router.patch("/paste/{paste_id}", tags=["pastes"], response_model=responses.PastePatchResponse, responses={
    200: {"model": responses.PastePatchResponse},
    401: {"model": errors.Unauthorized},
    403: {"model": errors.Forbidden},
    404: {"model": errors.NotFound}},
    name="Edit paste"
)
async def edit_paste(request: Request, paste_id: str, payload: payloads.PastePatch, authorization: str = Depends(auth_model)) -> Union[UJSONResponse, Dict[str, Optional[Union[str, int, datetime.datetime]]]]:
    """Edit a paste on MystBin.
    * Requires authentication.
    """
    if not authorization:
        return UJSONResponse({"error": "Forbidden"}, status_code=403)

    author: Record = await request.app.state.db.get_user(token=authorization.credentials)
    if not author or author in {400, 401}:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    paste: Union[Record, int] = await request.app.state.db.edit_paste(paste_id, author['id'], payload.new_content, payload.new_expires, payload.new_nick)
    if not paste or paste == 404:
        return UJSONResponse({"error": "Paste was not found or you are not it's author."}, status_code=404)

    return dict(paste[0])


@router.delete("/paste/{paste_id}", tags=["pastes"], responses={
    200: {"content": {"application/json": {"example": {"deleted": "SomePasteID"}}}},
    401: {"model": errors.Unauthorized},
    403: {"model": errors.Forbidden}},
    status_code=200,
    name="Delete paste"
)
async def delete_paste(request: Request, paste_id: str = None, authorization: str = Depends(auth_model)) -> Union[UJSONResponse, Dict[str, str]]:
    """Deletes pastes on MystBin.
    * Requires authentication.
    """
    if not authorization:
        return UJSONResponse({"error": "Forbidden"}, status_code=403)

    author: Union[Record, int] = await request.app.state.db.get_user(token=authorization.credentials)
    if not author or author in {400, 401}:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    is_owner: bool = await request.app.state.db.ensure_author(paste_id, author['id'])
    if not is_owner:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    deleted: Record = await request.app.state.db.delete_paste(paste_id, author['id'], admin=False)

    return UJSONResponse({"deleted": deleted['id']}, status_code=200)

@router.delete("/paste", tags=["pastes"], responses={
    200: {"content": {"application/json": {"example": {"succeeded": ["SomePasteID"], "failed": ["OtherPasteID"]}}}},
    401: {"model": errors.Unauthorized},
    403: {"model": errors.Forbidden}},
    status_code=200,
    name="Delete pastes"
)
async def delete_pastes(request: Request, payload: payloads.PasteDelete, authorization: str = Depends(auth_model)) -> Union[UJSONResponse, Dict[str, List[str]]]:
    """Deletes pastes on MystBin.
    * Requires authentication.
    """
    # We will filter out the pastes that are authorized and unauthorized, and return a clear response
    response = {"succeeded": [], "failed": []}

    author: Union[Record, int] = await request.app.state.db.get_user(token=authorization.credentials)
    if not author or author in {400, 401}:
        return UJSONResponse({"error": "Unauthorized"}, status_code=401)

    for paste in payload.pastes:
        if await request.app.state.db.ensure_author(paste, author['id']):
            response['succeeded'].append(paste)
        else:
            response['failed'].append(paste)

    for paste in response['succeeded']:
        await request.app.state.db.delete_paste(paste, author['id'], admin=False)

    return UJSONResponse(response, status_code=200)
