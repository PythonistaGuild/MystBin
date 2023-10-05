import asyncio
import hashlib

import aiohttp
import yarl


def hash_email_gravatar(email: str) -> str:
    return hashlib.md5(email.lower().encode()).hexdigest()


async def _gravatar_get(session: aiohttp.ClientSession, email: str) -> tuple[bool, str]:
    avy_hash = hash_email_gravatar(email)

    url = yarl.URL("https://www.gravatar.com/avatar/" + avy_hash).with_query({"d": "404"})

    async with session.get(url) as resp:
        return resp.status == 200, avy_hash


async def find_available_gravatar(emails: list[str], force_response: bool) -> str | None:
    session = aiohttp.ClientSession()

    tasks: tuple[asyncio.Task[tuple[bool, str]]] = tuple(
        asyncio.create_task(_gravatar_get(session, email)) for email in emails
    )
    results: list[tuple[bool, str]] = await asyncio.gather(*tasks)

    for resp in results:
        if resp[0]:
            return resp[1]

    return None if not force_response else results[0][1]
