import asyncio
import os
import pathlib
import sys

import toml
from httpx import AsyncClient
from main import app


with open("tests/config.toml") as f:
    app.config = toml.load(f)

loop = asyncio.get_event_loop()
loop.run_until_complete(app.router.startup())


client = AsyncClient(app=app, base_url="http://127.0.0.1:8888/")
