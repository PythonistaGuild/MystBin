import asyncio
import datetime
import logging

import asyncpg
from msgspec import json

from utils import datapackage, email

logger = logging.getLogger()

class TaskProcessor:
    def __init__(self, config: dict) -> None:
        self.config: dict[str, dict[str, str | int | bool]] = config
        self.db: asyncpg.Connection = None # type: ignore
        self.pubsub: asyncpg.Connection = None # type: ignore
        self.queue = asyncio.Queue()

    async def start(self) -> None:        
        self.pubsub = await asyncpg.connect(dsn=self.config["database"]["dsn"])
        self.db = await asyncpg.connect(dsn=self.config["database"]["dsn"]) # type: ignore # ??? only this one raises a type error

        await self.pubsub.add_listener("create_task", self.pubsub_receiver)
        asyncio.create_task(self.main_loop(), name="tasks-main-loop")
        asyncio.create_task(self.expiry_insert_loop(), name="tasks-expiry-loop")

    async def pubsub_receiver(self, conn: asyncpg.Connection, pid: str, channel: str, message: str) -> None:
        data = json.decode(message)
        await self.queue.put(data)

    async def expiry_insert_loop(self) -> None:
        while True:
            await self.queue.put({"task": "paste_expiry"})
            await asyncio.sleep(60)

    async def main_loop(self) -> None:
        while True:
            task = await self.queue.get()
            
            logger.debug("processing task %s", task)

            try:
                handler = getattr(self, f"task_{task['task']}")
                await handler(task)
            except Exception as e:
                logger.exception("An exception occurred during a task", exc_info=e)

            self.queue.task_done()

    async def task_datapackage(self, message: dict) -> None:
        # message needs user_id and email
        package = await datapackage.create_datapackage(message["user_id"], self.db)
        await email.send_datapackage(package, message["email"], self.config)

    async def task_delete_user(self, message: dict) -> None:
        # message needs user_id and keep_pastes
        emails = await self.db.fetchval("SELECT emails FROM users WHERE id = $1", message["user_id"])
        await self.db.execute("SELECT deleteUserAccount($1::bigint, $2::boolean)", message["user_id"], message["keep_pastes"])
        
        await email.send_goodbye(emails[0], self.config) # type: ignore

    async def task_paste_expiry(self, _) -> None:
        now = datetime.datetime.utcnow()
        await self.db.execute("DELETE FROM pastes CASCADE WHERE expires IS NOT NULL and expires <= $1", now)
