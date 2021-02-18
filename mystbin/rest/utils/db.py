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
import difflib
import functools
import math
import pathlib
from typing import Any, Dict, List, Optional, Union

import asyncpg

from . import tokens

EPOCH = 1587304800000  # 2020-04-20T00:00:00.0 * 1000 (Milliseconds)


def _recursive_hook(d: dict):
    for a, b in d.items():
        if isinstance(b, asyncpg.Record):
            b = dict(b)

        if isinstance(b, dict):
            d[a] = _recursive_hook(b)
        elif isinstance(b, datetime.datetime):
            d[a] = b.isoformat()

    return d


def wrapped_hook_callback(func):
    @functools.wraps(func)
    async def wraps(*args, **kwargs):
        resp = await func(*args, **kwargs)
        if isinstance(resp, asyncpg.Record):
            resp = dict(resp)

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
        self._config = app.config["database"]
        self._db_schema = pathlib.Path(self._config["schema_path"])
        self.ban_cache = None

    @property
    def pool(self) -> Optional[asyncpg.pool.Pool]:
        """Property for easier access to attr."""
        return self._pool or None

    async def __ainit__(self):
        await asyncio.sleep(5)
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
    async def get_recent_pastes(
        self, offset: int, reverse=False
    ) -> List[Dict[str, Any]]:
        """
        Gets the most recent pastes (20) of them, or oldest if reverse is True

        Parameters
        -----------
        offset: :class:`int`
            The offset of pastes
        reverse: :class:`bool`
            whether to search for oldest pastes first
        """
        query = f"""
                SELECT id, author_id, (SELECT names FROM users WHERE id=pastes.author_id) AS author_names, created_at,
                views, expires, origin_ip FROM pastes
                ORDER BY created_at {'ASC' if reverse else 'DESC'}
                LIMIT 20
                OFFSET $1
                """
        return [dict(x) for x in await self._do_query(query, offset)]

    # for anyone who wonders why this doesnt have a wrapped hook on it, it's because the endpoints for this particular
    # db call have to validate the data themselves, and then manually call the hook, so theres no point repeating the
    # process twice
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
                WITH upd AS (
                    UPDATE pastes
                    SET last_edit_time = (now() at time zone 'utc')
                    WHERE id = $4 AND author_id IS NOT NULL
                    RETURNING author_id
                )
                UPDATE files SET
                    content = $1, loc = $2, nick = COALESCE($3, nick)
                WHERE parent_id = $4 AND (select * from upd) = $5
                RETURNING *;
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
    async def get_paste_count(self) -> asyncpg.Record:
        """Get total paste count from Database.

        Returns
        ---------
        :class:`asyncpg.Record`
            The record containing total paste count.
        """
        query = """SELECT count(*) FROM pastes"""

        return await self._do_query(query)

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
        discord_id: str = None,
        github_id: str = None,
        google_id: str = None,
    ) -> asyncpg.Record:
        """Creates a new User record.

        Parameters
        ------------
        emails: List[:class:`str`]
            The email addresses the user has registered with.
        discord_id: Optional[:class:`str`]
            The Discord ID of the registering user.
        github_id: Optional[:class:`str`]
            The GitHub ID of the registering user.
        google_id: Optional[:class:`str`]
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
                VALUES ($1, $2, $3, $4, $5, $6, false, DEFAULT, false)
                RETURNING *;
                """

        data = await self._do_query(
            query, userid, token, emails, str(discord_id) or None, str(github_id) or None, str(google_id) or None
        )
        return data[0]

    @wrapped_hook_callback
    async def update_user(
        self,
        user_id: int,
        emails: Optional[List[str]] = None,
        discord_id: Optional[str] = None,
        github_id: Optional[str] = None,
        google_id: Optional[str] = None,
    ) -> Optional[str]:
        """Updates an existing user account.

        Parameters
        ------------
        user_id: :class:`int`
            The ID of the user to edit.
        emails: Optional[List[:class:`str`]]
            The email to add to the User's list of emails.
        discord_id: Optional[:class:`str`]
            The user's Discord ID.
        github_id: Optional[:class:`str`]
            The user's GitHub ID.
        google_id: Optional[:class:`str`]
            The user's Google ID.

        Returns
        ---------
        Optional[:class:`str`]
            Returns the updated user's token.
        """

        query = """
                UPDATE users SET
                discord_id = COALESCE($1, discord_id),
                github_id = COALESCE($2, github_id),
                google_id = COALESCE($3, google_id)
                WHERE id = $4
                RETURNING token, emails;
                """

        data = await self._do_query(
            query, str(discord_id), str(github_id), str(google_id), user_id
        )
        if not data:
            return None

        token, _emails = data[0]

        if not emails:
            return token

        new_emails = set(_emails)
        new_emails.update(emails)
        new_emails = list(new_emails)
        if new_emails == emails:
            return token


        query = """
                UPDATE users SET emails = $1 WHERE id = $2
                """

        await self._do_query(query, new_emails, user_id)
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
    async def ban_user(self, userid: int = None, ip: str = None, reason: str = None):
        """
        Bans a user.
        Returns False if the user/ip doesnt exist, or is already banned, otherwise returns True
        """
        try:
            query = """
                    INSERT INTO bans VALUES ($1, $2, $3)
                    """
            assert userid or ip
            await self._do_query(query, ip, userid, reason)
        except asyncpg.UniqueViolationError:
            return False
        else:
            return True

    @wrapped_hook_callback
    async def unban_user(self, userid: int = None, ip: str = None):
        """
        Unbans a user.
        Returns True if the user/ip was successfully unbanned, otherwise False
        """
        assert userid or ip

        if userid and ip:
            query = "DELETE FROM bans WHERE userid = $1 OR ip = $2 RETURNING *;"
            return len(await self._do_query(query, userid, ip)) > 0
        elif userid:
            query = "DELETE FROM bans WHERE userid = $1 RETURNING *;"
            return len(await self._do_query(query, userid)) > 0
        else:
            query = "DELETE FROM bans WHERE ip = $1 RETURNING *;"
            return len(await self._do_query(query, ip)) > 0

    @wrapped_hook_callback
    async def get_bans(self, page: int = 1):
        """
        Lists the bans. Pages by 40
        """
        query = """
                SELECT * FROM bans LIMIT 40 OFFSET $1 * 20
                """
        data = await self._do_query(query, page - 1)
        return data

    @wrapped_hook_callback
    async def switch_theme(self, userid: int, theme: str) -> None:
        """Quick query to set theme choices."""
        query = """
                UPDATE users SET theme = $1 WHERE id = $2
                """

        await self._do_query(query, theme, userid)

    @wrapped_hook_callback
    async def toggle_subscription(self, userid: int, state: bool):
        query = "UPDATE users SET subscriber = $1 WHERE id = $2 AND subscriber != $1 RETURNING id;"
        val = await self._do_query(query, state, userid)
        return len(val) > 0

    @wrapped_hook_callback
    async def regen_token(
        self, *, userid: int = None, token: str = None
    ) -> Optional[str]:
        """Generates a new token for the given user id or token.
        Returns the new token, or None if the user does not exist.
        """
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
    async def get_bookmarks(self, userid: int) -> List[Dict[str, Any]]:
        """
        Gets a list of bookmarks from the db
        """
        query = """
                SELECT paste as id, pastes.created_at, pastes.expires, pastes.views
                FROM bookmarks
                INNER JOIN pastes
                    ON pastes.id = bookmarks.paste
                WHERE userid = $1
                ORDER BY created_at
                """

        data = await self._do_query(query, userid)
        return [dict(x) for x in data]

    async def create_bookmark(self, userid: int, paste_id: str): # doesnt return anything, no need for a hook
        """creates a bookmark for a user"""
        query = """
                INSERT INTO bookmarks (userid, paste) VALUES ($1, $2)
                """

        try:
            await self._do_query(query, userid, paste_id)
        except asyncpg.UniqueViolationError:
            raise ValueError("This paste is already bookmarked")
        except asyncpg.ForeignKeyViolationError:
            raise ValueError("This paste does not exist") # its an auth'ed endpoint, so the user has to exist

    async def delete_bookmark(self, userid: int, paste_id: str) -> bool:
        """deletes a users bookmark"""
        query = """
                DELETE FROM bookmarks WHERE userid = $1 AND paste = $2 RETURNING paste
                """
        data = await self._do_query(query, userid, paste_id)
        return bool(data)

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

    @wrapped_hook_callback
    async def get_admin_userlist(
        self, page: int
    ) -> Dict[str, Union[List[Dict[str, Union[int, bool, None]]], int]]:
        query = """
                SELECT
                    id,
                    github_id,
                    discord_id,
                    google_id,
                    admin,
                    theme,
                    subscriber,
                    (SELECT COUNT(*) FROM pastes WHERE author_id = users.id) AS paste_count
                FROM users LIMIT 20 OFFSET $1 * 20;
        """
        async with self._pool.acquire() as conn:
            users = await self._do_query(query, page - 1, conn=conn)
            pageinfo = math.ceil(
                (
                    await self._do_query(
                        "SELECT COUNT(*) AS count FROM users", conn=conn
                    )
                )[0]["count"]
            )

        users = [
            {
                "id": x["id"],
                "admin": x["admin"],
                "theme": x["theme"],
                "subscriber": x["subscriber"],
                "paste_count": x["paste_count"],
                "last_seen": None,  # TODO need something to track last seen timestamps
                "authorizations": [
                    x
                    for x in (
                        "github" if x["github_id"] else None,
                        "discord" if x["discord_id"] else None,
                        "google" if x["google_id"] else None,
                    )
                    if x is not None
                ],
            }
            for x in users
        ]
        return {"users": users, "page_count": pageinfo, "page": page}

    @wrapped_hook_callback
    async def search_bans(
        self, *, ip=None, userid=None, search=None
    ) -> Union[Optional[str], List[Dict[str, Any]]]:
        assert any((ip, userid, search))
        if not self.ban_cache:
            if ip and userid:
                r = await self._do_query(
                    "SELECT reason FROM bans WHERE ip = $1 OR userid = $2", ip, userid
                )
                return r[0]["reason"] if r else None

            if ip:  # quick path: select directly from the db
                r = await self._do_query("SELECT reason FROM bans WHERE ip = $1", ip)
                return r[0]["reason"] if r else None

            elif userid:  # quick path: select directly from the db
                r = await self._do_query("SELECT reason FROM bans WHERE id = $1", ip)
                return r[0]["reason"] if r else None

            # long path, sequence search
            self.ban_cache = await self._do_query("SELECT * FROM bans")

        if ip and userid:
            v = [x for x in self.ban_cache if x["ip"] == ip or x["userid"] == userid]
            return v[0]["reason"] if v else None

        if ip:
            v = [x for x in self.ban_cache if x["ip"] == ip]
            return v[0]["reason"] if v else None

        elif userid:
            v = [x for x in self.ban_cache if x["ip"] == ip]
            return v[0]["reason"] if v else None

        # long path
        # in reality this should only ever be called by the admin ban search endpoint
        matcher = difflib.SequenceMatcher()
        matcher.set_seq1(search)
        close = []

        if (
            "." in search
        ):  # a really stupid way to detect a possible ip, but hey, it works
            for ban in self.ban_cache:
                if not ban["ip"]:
                    continue

                if ban["ip"] == search:
                    return ban["reason"]

                matcher.set_seq2(ban["ip"])
                if matcher.quick_ratio() > 0.7:
                    close.append(dict(ban))

        for ban in self.ban_cache:
            if not ban["id"]:
                continue

            if ban["id"] == search:
                return ban["reason"]

            matcher.set_seq2(ban["id"])
            if matcher.quick_ratio() > 0.7:
                close.append(dict(ban))
                continue


        return close
