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
import pathlib
from random import sample
from typing import List, Optional, Union, Dict

from asyncpg import Record
from fastapi import APIRouter, Depends, Request, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from models import (Forbidden, NotFound, PasteDelete, PasteGetAllResponse,
                    PasteGetResponse, PastePatch, PastePatchResponse,
                    PastePost, PastePostResponse, Unauthorized)


WORDS_LIST = open(pathlib.Path("utils/words.txt")).readlines()


router = APIRouter()
auth_model = HTTPBearer()
optional_auth_model = HTTPBearer(auto_error=False)


def generate_paste_id():
    """ Generate three random words. """
    return "".join(sample([word.title() for word in WORDS_LIST if len(word) > 3], 3)).replace("\n", "")


@router.post("/paste", tags=["pastes"], response_model=PastePostResponse, responses={
    201: {"model": PastePostResponse}},
    status_code=201,
    name="Create paste"
)
async def post_paste(request: Request, payload: PastePost, authorization: Optional[str] = Security(optional_auth_model)) -> Dict[str, Optional[Union[str, int, datetime.datetime]]]:
    """ Post a paste to MystBin. """
    author = None

    if authorization and authorization.credentials:
        author: Record = await request.app.state.db.get_user(token=authorization.credentials)

    author: Optional[int] = author.get("id", None) if isinstance(
        author, Record) else None

    paste: Record = await request.app.state.db.put_paste(generate_paste_id(), payload.content, author, payload.nick, payload.syntax, payload.password)

    return dict(paste)


@router.get("/paste/{paste_id}", tags=["pastes"], response_model=PasteGetResponse, responses={
    200: {"model": PasteGetResponse},
    401: {"model": Unauthorized},
    404: {"model": NotFound}},
    name="Retrieve paste"
)
async def raw_paste(request: Request, paste_id: str, password: Optional[str] = None) -> Union[JSONResponse, Dict[str, Optional[Union[str, int, datetime.datetime]]]]:
    """ Get a raw paste from MystBin. """
    paste: Record = await request.app.state.db.get_paste(paste_id, password)
    if paste is None:
        return JSONResponse({"error": "Not Found"}, status_code=404)

    if paste['has_password'] and not paste['password_ok']:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    return dict(paste)


@router.get("/pastes", tags=["pastes"], response_model=List[PasteGetAllResponse], responses={
    200: {"model": Optional[List[PasteGetAllResponse]]},
    403: {"model": Forbidden}},
    name="Get multiple pastes"
)
async def get_all_pastes(request: Request, limit: Optional[int] = None, authorization: str = Depends(auth_model)) -> Union[JSONResponse, Dict[str, List[Dict[str, str]]]]:
    """ Get all pastes for a specified author.
    * Can require authentication.
    """
    if not authorization:
        return JSONResponse({"error": "Forbidden"}, status_code=403)

    author: Record = await request.app.state.db.get_user(token=authorization.credentials)

    pastes: Record = await request.app.state.db.get_all_pastes(author['id'], limit)
    pastes = [dict(entry) for entry in pastes]

    return {"pastes": pastes}


@router.put("/paste/{paste_id}", tags=["pastes"], response_model=PastePatchResponse, responses={
    200: {"model": PastePatchResponse},
    401: {"model": Unauthorized},
    403: {"model": Forbidden},
    404: {"model": NotFound}},
    name="Edit paste"
)
@router.patch("/paste/{paste_id}", tags=["pastes"], response_model=PastePatchResponse, responses={
    200: {"model": PastePatchResponse},
    401: {"model": Unauthorized},
    403: {"model": Forbidden},
    404: {"model": NotFound}},
    name="Edit paste"
)
async def edit_paste(request: Request, paste_id: str, payload: PastePatch, authorization: str = Depends(auth_model)) -> Union[JSONResponse, Dict[str, Optional[Union[str, int, datetime.datetime]]]]:
    """ Edit a paste on MystBin.
    * Requires authentication.
    """
    if not authorization:
        return JSONResponse({"error": "Forbidden"}, status_code=403)

    author: Record = await request.app.state.db.get_user(token=authorization.credentials)
    if not author or author in {400, 401}:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    paste: Union[Record, int] = await request.app.state.db.edit_paste(paste_id, author['id'], payload.new_content, payload.new_expires, payload.new_nick)
    if not paste or paste == 404:
        return JSONResponse({"error": "Paste was not found or you are not it's author."}, status_code=404)

    return dict(paste[0])


@router.delete("/paste/{paste_id}", tags=["pastes"], responses={
    401: {"model": Unauthorized},
    403: {"model": Forbidden}},
    status_code=200,
    name="Delete paste"
)
async def delete_paste(request: Request, paste_id: str = None, authorization: str = Depends(auth_model)) -> Union[JSONResponse, Dict[str, str]]:
    """ Deletes pastes on MystBin.
    * Requires authentication.
    """
    if not authorization:
        return JSONResponse({"error": "Forbidden"}, status_code=403)

    author: Union[Record, int] = await request.app.state.db.get_user(token=authorization.credentials)
    if not author or author in {400, 401}:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    is_owner: bool = await request.app.state.db.ensure_author(paste_id, author['id'])
    if not is_owner:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    deleted: Record = await request.app.state.db.delete_paste(paste_id, author['id'], admin=False)

    return JSONResponse({"deleted": deleted['id']}, status_code=200)

@router.delete("/paste", tags=["pastes"], responses={
    401: {"model": Unauthorized},
    403: {"model": Forbidden}},
    status_code=200,
    name="Delete pastes"
)
async def delete_pastes(request: Request, payload: PasteDelete, authorization: str = Depends(auth_model)) -> Union[JSONResponse, Dict[str, List[str]]]:
    """ Deletes pastes on MystBin.
    * Requires authentication.
    """
    # We will filter out the pastes that are authorized and unauthorized, and return a clear response
    response = {"succeeded": [], "failed": []}

    author: Union[Record, int] = await request.app.state.db.get_user(token=authorization.credentials)
    if not author or author in {400, 401}:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    for paste in payload.pastes:
        if await request.app.state.db.ensure_author(paste, author['id']):
            response['succeeded'].append(paste)
        else:
            response['failed'].append(paste)

    for paste in response['succeeded']:
        await request.app.state.db.delete_paste(paste, author['id'], admin=False)

    return JSONResponse(response, status_code=200)
