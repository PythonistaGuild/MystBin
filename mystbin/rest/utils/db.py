"""Copyright(C) 2020 PythonistaGuild

This file is part of MystBin.

MystBin is free software: you can redistribute it and / or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

MystBin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY
without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with MystBin.  If not, see <https://www.gnu.org/licenses/>.
"""
import asyncio
import datetime
import pathlib
import functools
from typing import Any, Dict, List, Optional, Union

import asyncpg

from . import tokens

EPOCH = 1587304800000  # 2020-04-20T00:00:00.0 * 1000 (Milliseconds)


def _recursive_hook(d: dict):
    for a, b in d.items():
        if isinstance(b, dict):
            d[a] = _recursive_hook(b)
        elif isinstance(b, datetime.datetime):
            d[a] = b.isoformat()

    return d


def wrapped_hook_callback(func):
    @functools.wraps(func)
    async def wraps(*args, **kwargs):
        resp = await func(*args, **kwargs)
        if isinstance(resp, dict):
            return _recursive_hook(resp)
        elif isinstance(resp, list):
            r = []
            for i in resp:
                if isinstance(i, dict):
                    r.append(_recursive_hook(i))
                else:
                    r.append(i)
            resp = r

        return resp

    return wraps


class Database:
    """Small Database style object for MystBin usage.
    This will be passed across the backend for database usage.
    """

    timeout = 30

    def __init__(self, app):
        self._pool: asyncpg.pool.Pool = None
        self.env = "staging" if app.config["debug"]["db"] == "True" else "production"
        self._config = app.config[f"{self.env}-database"]
        self._db_schema = pathlib.Path(self._config["schema_path"])

    @property
    def pool(self) -> Optional[asyncpg.pool.Pool]:
        """Property for easier access to attr."""
        return self._pool or None

    async def __ainit__(self):
        await asyncio.sleep(5)
        print(self._config["dsn"])
        self._pool = await asyncpg.create_pool(
            self._config["dsn"], max_inactive_connection_lifetime=0
        )
        with open(self._db_schema) as schema:
            await self._pool.execute(schema.read())
        return self

    async def _do_query(
        self, query, *args, conn: asyncpg.Connection = None
    ) -> Optional[List[asyncpg.Record]]:
        if self._pool is None:
            await self.__ainit__()

        _conn = conn or await self._pool.acquire()
        try:
            response = await _conn.fetch(query, *args, timeout=self.timeout)
        except asyncio.TimeoutError:
            return None
        else:
            if not conn:
                await self._pool.release(_conn)

            return response

    @wrapped_hook_callback
    async def get_paste(
        self, paste_id: str, password: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get the specified paste.
        Parameters
        ------------
        paste_id: :class:`str`
            The paste ID we are attempting to get.
        password: Optional[:class:`str`]
            The passed password we'll attempt to use to decrypt the paste.

        Returns
        ---------
        Optional[:class:`asyncpg.Record`]
            The paste that was retrieved.
        """
        async with self._pool.acquire() as conn:
            query = """
                    UPDATE pastes SET views = views + 1 WHERE id = $1
                    RETURNING *,
                    CASE WHEN password IS NOT NULL THEN true
                    ELSE false END AS has_password,
                    CASE WHEN password = CRYPT($2, password) THEN true
                    ELSE false END AS password_ok
                    """

            resp = await self._do_query(query, paste_id, password or "", conn=conn)

            if resp:
                query = """
                SELECT * FROM files WHERE parent_id = $1
                """
                contents = await self._do_query(query, paste_id, conn=conn)
                resp = dict(resp[0])
                resp["pastes"] = [{a: str(b) for a, b in x.items()} for x in contents]

                return resp
            else:
                return None

    @wrapped_hook_callback
    async def get_paste_compat(self, paste_id: str) -> Optional[Dict[str, str]]:
        async with self._pool.acquire() as conn:
            query = """
                    UPDATE pastes SET views = views + 1 WHERE id = $1
                    RETURNING *,
                    CASE WHEN password IS NOT NULL THEN true
                    ELSE false END AS has_password
                    """

            resp = await self._do_query(query, paste_id, conn=conn)

            if resp:
                query = """
                SELECT content, syntax FROM files WHERE parent_id = $1 LIMIT 1
                """
                contents = await self._do_query(query, paste_id, conn=conn)
                ret = {
                    "key": paste_id,
                    "data": contents[0]["content"],
                    "has_password": resp[0]["has_password"],
                    "syntax": contents[0]["syntax"],
                }

                return ret
            else:
                return None

    @wrapped_hook_callback
    async def put_paste(
        self,
        *,
        paste_id: str,
        content: str,
        filename: str = "file.txt",
        author: Optional[int] = None,
        syntax: str = "",
        expires: datetime.datetime = None,
        password: Optional[str] = None,
    ) -> Dict[str, Union[str, int, None, List[Dict[str, Union[Union[str, int]]]]]]:
        """Puts the specified paste.
        Parameters
        -----------
        paste_id: :class:`str:
            The paste ID we are storing.
        content: :class:`str`
            The paste content.
        filename: :class:`str`
            The name of the file.
        author: Optional[:class:`int`]
            The ID of the author, if present.
        syntax: Optional[:class:`str`]
            The paste syntax, if present.
        expires: Optional[:class:`datetime.datetime`]
            The expiry time of this paste, if present.
        password: Optioanl[:class:`str`]
            The password used to encrypt the paste, if present.

        Returns
        ---------
        :class:`asyncpg.Record`
            The paste record that was created.
        """
        query = """
                WITH file AS (
                    INSERT INTO pastes (id, author_id, created_at, expires, password)
                    VALUES ($1, $2, $3, $4, (SELECT crypt($6, gen_salt('bf')) WHERE $6 is not null))
                    RETURNING id
                )
                INSERT INTO files (parent_id, content, filename, syntax, loc)
                VALUES ((select id from file), $5, $7, $8, $9)
                RETURNING index;
                """

        loc = content.count("\n") + 1
        chars = len(content)
        now = datetime.datetime.utcnow()

        await self._do_query(
            query,
            paste_id,
            author,
            now,
            expires,
            content,
            password,
            filename,
            syntax,
            loc,
        )

        # we need to generate our own response here, as we cant get the full response from the single query
        resp = {
            "id": paste_id,
            "author_id": author,
            "created_at": now,
            "expires": expires,
            "files": [
                {
                    "filename": filename,
                    "syntax": syntax,
                    "loc": loc,
                    "charcount": chars,
                }
            ],
        }
        return resp

    @wrapped_hook_callback
    async def put_pastes(
        self,
        *,
        paste_id: str,
        workspace_name: str,
        pages: List[Dict[str, str]],
        expires: Optional[datetime.datetime] = None,
        author: Optional[int] = None,
        password: Optional[str] = None,
    ) -> Dict[str, Union[str, int, None, List[Dict[str, Union[Union[str, int]]]]]]:
        """Puts the specified paste.
        Parameters
        -----------
        paste_id: :class:`str:
            The paste ID we are storing.
        workspace_name: :class:`str`
            The workspace name of this Paste.
        pages: List[Dict[:class:`str`, :class:`str`]]
            The paste content. A list of dictionaries containing `content`, `filename, and `syntax` (optional) keys.
        expires: Optional[:class:`datetime.datetime`]
            The expiry time of this paste, if present.
        author: Optional[:class:`int`]
            The ID of the author, if present.
        password: Optioanl[:class:`str`]
            The password used to encrypt the paste, if present.

        Returns
        ---------
        Dict[str, Optional[Union[str, int, datetime.datetime]]]
        """
        async with self._pool.acquire() as conn:
            query = """
                    INSERT INTO pastes (id, author_id, workspace_name, expires, password)
                    VALUES ($1, $2, $3, $4, (SELECT crypt($5, gen_salt('bf')) WHERE $5 is not null))
                    RETURNING id, author_id, created_at, expires
                    """

            resp = await self._do_query(
                query, paste_id, author, workspace_name, expires, password, conn=conn
            )

            resp = resp[0]
            print(resp)
            to_insert = []
            for page in pages:
                to_insert.append(
                    (
                        resp["id"],
                        page.content,
                        page.filename,
                        page.syntax,
                        page.content.count("\n"),
                    )
                )

            files_query = """
                          INSERT INTO files (parent_id, content, filename, syntax, loc)
                          VALUES ($1, $2, $3, $4, $5)
                          RETURNING index, filename, loc, charcount, syntax
                          """
            inserted = []
            async with conn.transaction():
                for insert in to_insert:
                    row = await conn.fetchrow(files_query, *insert)
                    inserted.append(row)

            resp = dict(resp)
            resp["files"] = [dict(file) for file in inserted]

            return resp

    @wrapped_hook_callback
    async def edit_paste(
        self,
        paste_id: str,
        author_id: int,
        new_content: str,
        new_nick: Optional[str] = None,
    ) -> Optional[asyncpg.Record]:
        """Edits a live paste
        Parameters
        ------------
        paste_id: :class:`str`
            The paste ID we intend to edit.
        author_id: :class:`int`
            The paste author.
        new_content: Optional[:class:`str`]
            The new paste content we are inserting.
        new_nick: Optional[:class:`str`]
            The new nickname of the paste.

        Returns
        ---------
        :class:`asyncpg.Record`
            The paste record which was edited.
        """
        query = """
                UPDATE files SET
                    content = $1, loc = $2, nick = COALESCE($3, nick)
                WHERE parent_id = $4 AND (
                    SELECT author_id
                    FROM pastes
                    WHERE paste_id = $4
                ) = $5
                RETURNING *
                """

        response = await self._do_query(
            query, new_content, new_content.count("\n"), new_nick, paste_id, author_id
        )

        return response[0] if response else None

    @wrapped_hook_callback
    async def edit_pastes(
        self,
        paste_id: str,
        pages: List[Dict[str, str]],
        author: int,
        password: Optional[str] = None,
    ) -> Optional[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """Puts the specified paste.
        Parameters
        -----------
        paste_id: :class:`str:
            The paste ID we are storing.
        pages: List[Dict[:class:`str`, :class:`str`]
            The paste content.
        author: Optional[:class:`int`]
            The ID of the author, if present.
        password: Optioanl[:class:`str`]
            The password used to encrypt the paste, if present.

        Returns
        ---------
        :class:`asyncpg.Record`
            The paste record that was created.
        """
        async with self._pool.acquire() as conn:
            query = """
                    UPDATE pastes
                    SET last_edited = NOW() AT TIME ZONE 'UTC'
                    WHERE id = $1 AND author_id = $2
                    AND password = (SELECT crypt($3, gen_salt('bf')) WHERE $3 is not null)
                    RETURNING *
                    """

            resp = await self._do_query(query, paste_id, author, password, conn=conn)
            if not resp:
                return None

            resp = resp[0]
            qs = []
            for page in pages:
                qs.append(
                    (
                        page["content"],
                        page["content"].count("\n"),
                        len(page["content"]),
                        paste_id,
                        page["index"],
                    )
                )

            query = """
                    UPDATE paste_content
                    SET content = $1, loc = $2, charcount = $3
                    WHERE parent_id = $4
                    AND index = $5
                    RETURNING content, loc, charcount, index
                    """
            data = await conn.executemany(query, qs)

            resp = dict(resp)
            resp["pages"] = [{a: str(b) for a, b in x.items()} for x in data]

            return resp

    @wrapped_hook_callback
    async def get_all_pastes(
        self, author_id: Optional[int], limit: Optional[int] = None
    ) -> List[asyncpg.Record]:
        """Get all pastes for an author and/or with a limit.
        Parameters
        ------------
        author_id: Optional[:class:`int`]
            The paste author id to query against.
        limit: Optional[:class:`int`]
            The limit to the amount of pastes to return. Defaults to ALL.

        Returns
        ---------
        Optional[List[:class:`asyncpg.Record`]]
            The potential list of pastes.
        """
        query = """
                SELECT id, author_id, nick, syntax, created_at,
                CASE WHEN password IS NOT NULL THEN true ELSE false END AS has_password
                FROM pastes
                WHERE author_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """

        response = await self._do_query(query, author_id, limit)

        return response

    @wrapped_hook_callback
    async def delete_paste(
        self, paste_id: str, author_id: Optional[int] = None, *, admin: bool = False
    ) -> Optional[asyncpg.Record]:
        """Delete a paste, with an admin override.

        Parameters
        ------------
        paste_id: :class:`str`
            The paste ID to delete.
        author_id: Optional[:class:`int`]
            The author ID the paste belongs to.
        admin: :class:`bool`
            Admin override. Defaults to False.

        Returns
        ---------
        :class:`asyncpg.Record`
            The paste that was deleted.
        """
        query = """
                DELETE FROM pastes CASCADE
                WHERE (id = $1 AND author_id = $2)
                OR (id = $1 AND $3)
                RETURNING id;
                """

        response = await self._do_query(query, paste_id, author_id, admin)

        return response[0] if response else None

    @wrapped_hook_callback
    async def get_user(
        self, *, user_id: int = None, token: str = None
    ) -> Optional[Union[asyncpg.Record, int]]:
        """Returns a User on successful query.

        Parameters
        ------------
        user_id: :class:`int`
            The user id to query against.
        token: :class:`str`
            The authorization token to query against once decoded.

        Returns
        ---------
        Optional[Union[:class:`asyncpg.Record`, :class:`int`]]
            Will return a record of the User on success, or a 40x status code depending on failure.
        """

        if not user_id and not token:
            raise ValueError("Expected either id or token")

        if user_id and token:
            raise ValueError("Expected id or token, not both")

        if token:
            user_id = tokens.get_user_id(token)
            if not user_id:
                return 400

        query = """
                SELECT * FROM users WHERE id = $1
                """

        data = await self._do_query(query, user_id)
        if not data:
            return None

        data = data[0]
        if token and data["token"] != token:
            return 401

        return data

    @wrapped_hook_callback
    async def new_user(
        self,
        emails: List[str],
        discord_id: int = None,
        github_id: int = None,
        google_id: int = None,
    ) -> asyncpg.Record:
        """Creates a new User record.

        Parameters
        ------------
        emails: List[:class:`str`]
            The email addresses the user has registered with.
        discord_id: Optional[:class:`int`]
            The Discord ID of the registering user.
        github_id: Optional[:class:`int`]
            The GitHub ID of the registering user.
        google_id: Optional[:class:`int`]
            The Google ID of the registering user.

        Returns
        ---------
        :class:`asyncpg.Record`
            The record created for the registering User.
        """

        userid = int((datetime.datetime.utcnow().timestamp() * 1000) - EPOCH)
        token = tokens.generate(userid)

        query = """
                INSERT INTO users
                VALUES ($1, $2, $3, $4, $5, $6, $7, false, DEFAULT, false, false)
                RETURNING *;
                """

        data = await self._do_query(
            query, userid, token, emails, [], discord_id, github_id, google_id
        )
        return data[0]

    @wrapped_hook_callback
    async def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        bookmarks: Optional[List[str]] = None,
        discord_id: Optional[int] = None,
        github_id: Optional[int] = None,
        google_id: Optional[str] = None,
    ) -> Optional[str]:
        """Updates an existing user account.

        Parameters
        ------------
        user_id: :class:`int`
            The ID of the user to edit.
        email: Optional[:class:`str`]
            The email to add to the User's list of emails.
        bookmarks: Optional[List[:class:`str`]]
            The bookmarks to update existing bookmarks.
        discord_id: Optional[:class:`int`]
            The user's Discord ID.
        github_id: Optional[:class:`int`]
            The user's GitHub ID.
        google_id: Optional[:class:`int`]
            The user's Google ID.

        Returns
        ---------
        Optional[:class:`str`]
            Returns the updated user's token.
        """

        query = """
                UPDATE users SET
                bookmarks = COALESCE($1, bookmarks),
                discord_id = COALESCE($2, discord_id),
                github_id = COALESCE($3, github_id),
                google_id = COALESCE($4, google_id)
                WHERE id = $4
                RETURNING token, emails;
                """

        data = await self._do_query(
            query, bookmarks, discord_id, github_id, google_id, user_id
        )
        if not data:
            return None

        token, emails = data[0]

        if not email or email in emails:
            return token

        query = """
                UPDATE users SET emails = array_append(emails, $1) WHERE id = $2
                """

        await self._do_query(query, email, user_id)
        return token

    @wrapped_hook_callback
    async def check_email(self, emails: Union[str, List[str]]) -> Optional[int]:
        """Quick check to query an email."""
        query = """
                SELECT id FROM users WHERE $1 && emails
                """
        if isinstance(emails, str):
            emails = [emails]

        data = await self._do_query(query, emails)
        if data:
            return data[0]["id"]

    @wrapped_hook_callback
    async def toggle_admin(self, userid: int, admin: bool) -> None:
        """Quick query to toggle admin privileges."""
        query = """
                UPDATE users SET admin = $1 WHERE id = $2
                """

        await self._do_query(query, admin, userid)

    @wrapped_hook_callback
    async def switch_theme(self, userid: int, theme: str) -> None:
        """Quick query to set theme choices."""
        query = """
                UPDATE users SET theme = $1 WHERE id = $2
                """

        await self._do_query(query, theme, userid)

    @wrapped_hook_callback
    async def regen_token(
        self, *, userid: int = None, token: str = None
    ) -> Optional[str]:
        """Generates a new token for the given user id or token. Returns the new token, or None if the user does not exist."""
        if not self._pool:
            await self.__ainit__()

        if not userid and not token:
            raise ValueError("Expected either userid or token argument")

        async with self._pool.acquire() as conn:
            if token:
                query = """
                        SELECT id from users WHERE token = $1
                        """
                data = await self._do_query(query, token, conn=conn)
                if not data:
                    return None

                userid = data[0]["id"]

            new_token = tokens.generate(userid)
            query = """
                    UPDATE users SET token = $1 WHERE id = $2 RETURNING id
                    """
            data = await self._do_query(query, new_token, userid, conn=conn)
            if not data:
                return None

            return token

    @wrapped_hook_callback
    async def ensure_authorization(self, token: str) -> bool:
        """Quick query against a passed token."""
        if not token:
            return False

        query = """
                SELECT id FROM users WHERE token = $1
                """

        data = await self._do_query(query, token)
        if not data:
            return False

        return data[0]["id"]

    @wrapped_hook_callback
    async def ensure_admin(self, token: str) -> bool:
        """Quick query against a token to return if admin or not."""
        if not token:
            return False

        query = """
                SELECT admin FROM users WHERE token = $1
                """

        data = await self._do_query(query, token)
        if not data:
            return False

        return data[0]["admin"]

    @wrapped_hook_callback
    async def ensure_author(self, paste_id: str, author_id: int) -> bool:
        """Quick query to ensure a paste is owned by the passed author ID."""

        query = """
                SELECT id
                FROM pastes
                WHERE id = $1
                AND author_id = $2;
                """

        response = await self._do_query(query, paste_id, author_id)
        if response:
            return True
        return False
