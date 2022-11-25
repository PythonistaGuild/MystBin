from datetime import datetime

import aiohttp
from yarl import URL


class WebhookAdapter:
    def __init__(self) -> None:
        self.session: aiohttp.ClientSession | None = None

    async def _ensure_session(self) -> None:
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def send_request(self, payload: dict[str, str | int | dict]) -> int:
        ...

    async def assemble_payload(self, event: str, url: URL, data: dict) -> dict:
        ...

    async def event_new_paste(
        self, paste_id: str, paste_owner: str | None, paste_filecount: int, paste_expiry: datetime | None
    ) -> None:
        ...

    async def event_delete_paste(self, paste_id: str, paste_owner: str | None) -> None:
        ...

    async def event_edit_paste(self, paste_id: str, paste_owner: str | None) -> None:
        ...

    async def event_newuser_authorized(self, user_id: int, service: str) -> None:
        ...
