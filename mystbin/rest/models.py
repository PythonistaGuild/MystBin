from typing import List, Optional

from pydantic import BaseModel

__all__ = ("PasteCreate", "PasteEdit", "PasteDelete")


class PasteCreate(BaseModel):
    content: str
    syntax: Optional[str] = None
    nick: Optional[str] = None


class PasteEdit(BaseModel):
    new_content: str
    nick: Optional[str] = None


class PasteDelete(BaseModel):
    pastes: List[str]
