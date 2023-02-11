import binascii
import uuid
import os

import jwt
from Crypto.Random import get_random_bytes


JWT_OPTIONS = {"verify_signature": False}

if os.path.exists(".signing-key"):
    with open(".signing-key") as f:
        signing_key = f.read().strip()

else:
    signing_key = binascii.hexlify(get_random_bytes(64)).decode()
    with open(".signing-key", "w") as f:
        f.write(signing_key)

def generate(userid: int, token_key: uuid.UUID, token_id: int) -> str:
    """Generate a token."""
    payload = {"uid": userid, "tkey": token_key.int, "safe": token_key.is_safe.value, "tid": token_id}
    print(payload)
    return jwt.encode(payload, signing_key, algorithm="HS512")


def get_user_id(token: str) -> tuple[int, int, uuid.UUID] | None:
    """Get user ID from a token."""
    try:
        payload = jwt.decode(token, key=signing_key, algorithms=["HS512"], options=JWT_OPTIONS)
        return payload["uid"], payload["tid"], uuid.UUID(int=payload["tkey"], is_safe=uuid.SafeUUID(payload["safe"]))
    except (jwt.DecodeError, jwt.ExpiredSignatureError):
        return None
