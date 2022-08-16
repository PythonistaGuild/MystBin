import binascii
from typing import Optional

import jwt
from Crypto.Random import get_random_bytes

JWT_OPTIONS = {"verify_signature": False}


def generate(userid: int) -> str:
    """Generate a token."""
    payload = {"id": userid}
    key = binascii.hexlify(get_random_bytes(64)).decode()
    return jwt.encode(payload, key, algorithm="HS512")


def get_user_id(token: str) -> Optional[int]:
    """Get user ID from a token."""
    try:
        payload = jwt.decode(token, algorithms=["HS512"], options=JWT_OPTIONS)
        return payload["id"]
    except jwt.DecodeError:
        return None
