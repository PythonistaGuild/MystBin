from secrets import token_urlsafe
from typing import Dict

from fastapi import APIRouter

from models import *

__all__ = ("post_paste", "raw_paste", "edit_paste")

router = APIRouter()

@router.post("/paste", tags=["pastes"])
async def post_paste(payload: PasteCreate) -> Dict[str, str]:
    """ Post a paste to MystBin. """
    return {"pastes": [{"id": token_urlsafe(5), "nick": payload.nick}]}

@router.get("/paste/{paste_id}", tags=["pastes"])
async def raw_paste(paste_id: str) -> Dict[str, str]:
    """ Get a raw paste from MystBin. """
    return {"id": paste_id, "data": "Umbra sucks!"}

@router.put("/paste/{paste_id}", tags=["pastes"])
@router.patch("/paste/{paste_id}", tags=["pastes"])
async def edit_paste(paste_id: str, payload: PasteEdit) -> Dict[str, str]:
    """ Edit a paste on MystBin.
        * Requires authentication.
    """
    ...

@router.delete("/paste/{paste_id}", tags=["pastes"])
async def delete_paste(paste_id: str = None) -> Dict[str, str]:
    """ Deletes pastes on MystBin.
        * Requires authentication.
    """
    return {"paste": paste_id}

@router.delete("/paste", tags=["pastes"])
async def delete_pastes(payload: PasteDelete) -> Dict[str, str]:
    """ Deletes pastes on MystBin.
        * Requires authentication.
    """
    return {"paste": payload}
