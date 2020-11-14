import binascii
from typing import Optional

import jwt
from Crypto.Random import get_random_bytes


def generate(userid: int, key=None) -> str:
    payload = {"id": userid}
    key = key or binascii.hexlify(get_random_bytes(64))
    return jwt.encode(payload, key, algorithm='HS512').decode()


def get_user_id(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, verify=False, algorithms=['HS512'])
        return payload['id']
    except jwt.DecodeError:
        return None
