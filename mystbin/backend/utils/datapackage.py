import tempfile
import shutil
import logging
import os
from typing import Any

import asyncpg
from msgspec import json

logger = logging.getLogger()

async def create_datapackage(userid: int, db: asyncpg.Connection) -> str:
    core_directory = tempfile.mkdtemp()
    directory = os.path.join(core_directory, str(userid))
    zippath = os.path.join(tempfile.gettempdir(), str(userid))
    userfile = os.path.join(directory, "account.json")
    bookmarksfile = os.path.join(directory, "bookmarks.json")
    tokenfile = os.path.join(directory, "tokens.json")
    pastesdir = os.path.join(directory, "pastes")

    os.mkdir(directory)

    # step 1: account data

    with open(userfile, mode="wb") as file:
        query = """
        SELECT id, emails, discord_id, github_id, google_id, handle, gravatar_hash FROM users WHERE id = $1
        """
        data = await db.fetchrow(query, userid)
        entry: dict[str, Any] = dict(data) # type: ignore
        output = json.encode(entry)
        file.write(output)
    
    # step 2: bookmarks

    with open(bookmarksfile, mode="wb") as file:
        query = """
        SELECT paste AS paste_id, created_at FROM bookmarks WHERE userid = $1
        """
        data = await db.fetch(query, userid)

        entry_l = [{"paste_id": b["paste_id"], "created_at": b["created_at"].isoformat()} for b in data]

        output = json.encode(entry_l)
        file.write(output)
    
    # step 3: tokens
    
    with open(tokenfile, mode="wb") as file:
        query = """
        SELECT id AS token_id, token_name, token_description, uses, is_main AS is_web_token FROM tokens WHERE user_id = $1
        """
        data = await db.fetch(query, userid)

        entry_l = [dict(d) for d in data]

        output = json.encode(entry_l)
        file.write(output)
    
    # step 4: pastes

    query = """
    SELECT id AS paste_id, created_at, expires AS expires_at, last_edited AS last_edited_at, views, origin_ip, public, source
    FROM pastes WHERE author_id = $1
    """
    data = await db.fetch(query, userid)

    query = """
    SELECT content, filename FROM files WHERE parent_id = $1
    """

    for paste in data:
        paste = dict(paste)
        current_paste_dir = os.path.join(pastesdir, paste["paste_id"])
        current_paste_files_dir = os.path.join(current_paste_dir, "files")
        os.makedirs(current_paste_files_dir, exist_ok=True)

        with open(os.path.join(current_paste_dir, "paste.json"), mode="wb") as file:
            output = json.encode(paste)
            file.write(output)
        
        files = await db.fetch(query, paste["paste_id"])

        for paste_file in files:
            with open(os.path.join(current_paste_files_dir, os.path.basename(paste_file["filename"])), mode="w") as file: # the basename guards against directory traversal
                file.write(paste_file["content"])
    
    # step 5: zip the directory & remove it

    shutil.make_archive(zippath, "zip", core_directory)
    shutil.rmtree(core_directory)

    return zippath + ".zip"
        

