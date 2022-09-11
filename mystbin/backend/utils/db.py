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
from __future__ import annotations

import asyncio
import datetime
import difflib
import functools
import os
import pathlib
from typing import Any, Dict, List, Literal, Optional, Union, cast

import asyncpg
from asyncpg import Record
from fastapi import Request, Response
from models import payloads

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

    def __init__(self, config: dict[str, dict[str, str | int]]):
        self._pool: Optional[asyncpg.Pool] = None
        self._config = config["database"]
        if "ISDOCKER" in os.environ:
            self._db_schema = pathlib.Path("/etc/schema.sql")
        else:
            self._db_schema = pathlib.Path("../database/schema.sql")

        self.ban_cache = None

    @property
    def pool(self) -> asyncpg.Pool:
        """Property for easier access to attr."""
        assert self._pool is not None

        return self._pool

    async def __ainit__(self):
        await asyncio.sleep(5)
        self._pool = await asyncpg.create_pool(
            self._config["dsn"], max_inactive_connection_lifetime=0, max_size=3, min_size=0
        )
        # with open(self._db_schema) as schema:
        #    await self._pool.execute(schema.read())
        return self

    async def _do_query(
        self, query: str, *args, conn: Optional[asyncpg.Connection] = None
    ) -> Optional[List[asyncpg.Record]]:
        if self._pool is None:
            await self.__ainit__()

        _conn = conn or await cast(asyncpg.Pool, self._pool).acquire()
        try:
            response = await _conn.fetch(query, *args, timeout=self.timeout)
        except asyncio.TimeoutError:
            return None
        else:
            if not conn:
                await self.pool.release(_conn)

            return response

    @wrapped_hook_callback
    async def get_all_pastes(self, page: int, count: int, reverse=False) -> List[Dict[str, Any]]:
        """
        Gets the most recent pastes (20) of them, or oldest if reverse is True

        Parameters
        -----------
        page: :class:`int`
            The offset of pastes
        count: :class:`int`
            The amount of pastes to return
        reverse: :class:`bool`
            whether to search for oldest pastes first
        """
        query = f"""
                SELECT id, author_id, created_at, views, expires, origin_ip, (password is not null) as has_password
                FROM pastes
                ORDER BY created_at {'ASC' if reverse else 'DESC'}
                LIMIT $1
                OFFSET $2
                """
        return [dict(x) for x in await self._do_query(query, count, page * count)]

    # for anyone who wonders why this doesnt have a wrapped hook on it, it's because the endpoints for this particular
    # db call have to validate the data themselves, and then manually call the hook, so theres no point repeating the
    # process twice
    async def get_paste(self, paste_id: str, password: Optional[str] = None) -> Optional[Dict[str, Any]]:
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
        async with self.pool.acquire() as conn:
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
                contents = cast(List[asyncpg.Record], await self._do_query(query, paste_id, conn=conn))
                resp = dict(resp[0])
                resp["files"] = [{a: str(b) for a, b in x.items()} for x in contents]
                return resp
            else:
                return None

    @wrapped_hook_callback
    async def get_paste_compat(self, paste_id: str) -> Optional[Dict[str, str]]:
        if not self._pool:
            await self.__ainit__()

        async with self.pool.acquire() as conn:
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
                contents = cast(List[asyncpg.Record], await self._do_query(query, paste_id, conn=conn))
                ret = {
                    "key": paste_id,
                    "data": contents[0]["content"],
                    "has_password": resp[0]["has_password"],
                }

                return ret
            else:
                return None

    @wrapped_hook_callback
    async def put_paste(
        self,
        *,
        paste_id: str,
        origin_ip: Optional[str],
        pages: List[payloads.RichPasteFile] | List[payloads.PasteFile],
        expires: Optional[datetime.datetime] = None,
        author: Optional[int] = None,
        password: Optional[str] = None,
    ) -> Dict[str, Union[str, int, None, List[Dict[str, Union[str, int]]]]]:
        """Puts the specified paste.
        Parameters
        -----------
        paste_id: :class:`str:
            The paste ID we are storing.
        origin_ip: :class:`str`
            The ip the paste came from
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
        if not self._pool:
            await self.__ainit__()

        async with self.pool.acquire() as conn:
            query = """
                    INSERT INTO pastes (id, author_id, expires, password, origin_ip)
                    VALUES ($1, $2, $3, (SELECT crypt($4, gen_salt('bf')) WHERE $4 is not null), $5)
                    RETURNING id, author_id, created_at, expires, origin_ip
                    """

            resp = cast(
                List[asyncpg.Record],
                await self._do_query(query, paste_id, author, expires, password, origin_ip, conn=conn),
            )

            resp = resp[0]
            to_insert = []
            for page in pages:
                to_insert.append(
                    (
                        resp["id"],
                        page.content,
                        page.filename,
                        page.content.count("\n") + 1,  # add an extra for line 1
                        getattr(page, "attachment", None)
                    )
                )

            files_query = """
                          INSERT INTO files (parent_id, content, filename, loc, attachment)
                          VALUES ($1, $2, $3, $4, $5)
                          RETURNING index, filename, loc, charcount, content, attachment
                          """
            inserted = []
            async with conn.transaction():
                for insert in to_insert:
                    row = await conn.fetchrow(files_query, *insert)
                    inserted.append(row)

            resp = dict(resp)
            del resp["origin_ip"]
            resp["files"] = [dict(file) for file in inserted]

            return resp

    @wrapped_hook_callback
    async def edit_paste(
        self,
        paste_id: str,
        *,
        author: int,
        new_expires: Optional[datetime.datetime] = None,
        new_password: Optional[str] = None,
        files: Optional[list[payloads.PasteFile]] = None,
    ) -> Optional[Literal[404]]:
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
        if not self._pool:
            await self.__ainit__()

        async with self.pool.acquire() as conn:
            conn: asyncpg.Connection

            query = """
                    UPDATE pastes
                    SET last_edited = NOW() AT TIME ZONE 'UTC',
                    password = (SELECT crypt($3, gen_salt('bf')) WHERE $3 is not null),
                    expires = $4
                    WHERE id = $1 AND author_id = $2
                    RETURNING *
                    """

            resp = await self._do_query(query, paste_id, author, new_password, new_expires, conn=conn)
            if not resp:
                return 404

            if files:
                qs = []
                for file in files:
                    qs.append(
                        (
                            file.content,
                            file.content.count("\n"),
                            len(file.content),
                            paste_id,
                        )
                    )

                query = """
                        UPDATE files
                        SET content = $1, loc = $2, charcount = $3
                        WHERE parent_id = $4
                        RETURNING content, loc, charcount
                        """
                await conn.executemany(query, qs)

    @wrapped_hook_callback
    async def set_paste_password(self, paste_id: str, password: str | None) -> Optional[asyncpg.Record]:
        """Sets a password for the specified paste.
        This is for use by the cli module.

        Parameters
        ------------
        paste_id: :class:`str`
            The id of the paste to update the password for
        password: :class:`str`
            The password to use

        Returns
        ---------
        Optional[:class:`asyncpg.Record`]
            The updated paste
        """
        query = """
        UPDATE pastes
        SET password = $2
        WHERE id = $1
        RETURNING *
        """
        resp = await self._do_query(query, paste_id, password)
        if resp:
            return resp[0]

        return None

    @wrapped_hook_callback
    async def get_all_user_pastes(self, author_id: Optional[int], limit: Optional[int] = None) -> List[asyncpg.Record]:
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
                SELECT id, author_id, created_at,
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

        return (await self._do_query(query))[0]["count"]

    @wrapped_hook_callback
    async def delete_paste(self, paste_id: str, author_id: Optional[int] = None, *, admin: bool = False) -> Optional[str]:
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
    async def get_user(self, *, user_id: int = None, token: str = None) -> Optional[Union[asyncpg.Record, int]]:
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
        username: str,
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
                VALUES ($1, $2, $3, $4, $5, $6, false, DEFAULT, false, $7)
                RETURNING *;
                """

        data = await self._do_query(
            query,
            userid,
            token,
            emails,
            discord_id and str(discord_id),
            github_id and str(github_id),
            google_id and str(google_id) or None,
            username,
        )
        return data[0]

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
            query,
            discord_id and str(discord_id),
            github_id and str(github_id),
            google_id and str(google_id),
            user_id,
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

    async def unlink_account(self, user_id: int, account: str) -> bool:
        """Unlinks an account. Doesnt do sanity checks."""
        if account == "google":
            query = "UPDATE users SET google_id = null WHERE id = $1 AND google_id is not null RETURNING id"
        elif account == "github":
            query = "UPDATE users SET github_id = null WHERE id = $1 AND users.github_id is not null RETURNING id"
        elif account == "discord":
            query = "UPDATE users SET discord_id = null WHERE id = $1 AND discord_id is not null RETURNING id"
        else:
            raise ValueError(f"Expected account to be one of google, github, or discord. Not '{account}'")

        return bool(await self._do_query(query, user_id))

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

    async def toggle_admin(self, userid: int, admin: bool) -> bool:
        """Quick query to toggle admin privileges."""
        query = """
                UPDATE users SET admin = $1 WHERE id = $2 RETURNING id
                """

        return bool(await self._do_query(query, admin, userid))

    async def list_admin(self) -> List[asyncpg.Record]:
        query = """
        SELECT id, username, discord_id, github_id, google_id FROM users WHERE admin = true
        """
        resp = await self._do_query(query)
        return resp or []

    @wrapped_hook_callback
    async def ban_user(self, userid: Optional[int] = None, ip: Optional[str] = None, reason: Optional[str] = None):
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

    async def unban_user(self, userid: Optional[int] = None, ip: Optional[str] = None) -> bool:
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
    async def regen_token(self, *, userid: int = None, token: str = None) -> Optional[str]:
        """Generates a new token for the given user id or token.
        Returns the new token, or None if the user does not exist.
        """
        if not self._pool:
            await self.__ainit__()

        if not userid and not token:
            raise ValueError("Expected either userid or token argument")

        async with self.pool.acquire() as conn:
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

            return new_token

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

    async def create_bookmark(self, userid: int, paste_id: str):  # doesnt return anything, no need for a hook
        """creates a bookmark for a user"""
        query = """
                INSERT INTO bookmarks (userid, paste) VALUES ($1, $2)
                """

        try:
            await self._do_query(query, userid, paste_id)
        except asyncpg.UniqueViolationError:
            raise ValueError("This paste is already bookmarked")
        except asyncpg.ForeignKeyViolationError:
            raise ValueError("This paste does not exist")  # its an auth'ed endpoint, so the user has to exist

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
    async def get_admin_userlist(self, page: int) -> Dict[str, Union[int, Dict[str, Union[int, bool, None]]]]:
        query = """
                SELECT
                    id,
                    username,
                    github_id,
                    discord_id,
                    google_id,
                    admin,
                    theme,
                    subscriber,
                    (SELECT COUNT(*) FROM pastes WHERE author_id = users.id) AS paste_count
                FROM users LIMIT 20 OFFSET $1 * 20;
        """
        if not self._pool:
            await self.__ainit__()

        async with self.pool.acquire() as conn:
            users = await self._do_query(query, page - 1, conn=conn)
            records: List[Record] = await self._do_query("SELECT COUNT(*) AS count FROM users", conn=conn)
            pageinfo: int = records[0]["count"]

        users = [
            {
                "id": x["id"],
                "username": x["username"],
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
        return {"users": users, "user_count": pageinfo, "page": page}

    async def get_admin_usercount(self) -> int:
        query = "SELECT COUNT(id) AS count FROM users"
        data = await self._do_query(query)
        return data[0]["count"]

    @wrapped_hook_callback
    async def search_bans(self, *, ip=None, userid=None, search=None) -> Union[Optional[str], List[Dict[str, Any]]]:
        assert any((ip, userid, search))
        if not self.ban_cache:
            if ip and userid:
                r = await self._do_query("SELECT reason FROM bans WHERE ip = $1 OR userid = $2", ip, userid)
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

        if "." in search:  # a really stupid way to detect a possible ip, but hey, it works
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

    async def put_log(self, request: Request, response: Response) -> None:
        query = """
        INSERT INTO logs VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        try:
            body = request._body
        except:
            body = None

        try:
            resp = str(response.body)
        except AttributeError:
            resp = None
        await self._do_query(
            query,
            request.headers.get("X-Forwarded-For", request.client.host),
            request.state.user and request.state.user["id"],
            datetime.datetime.utcnow(),
            request.headers.get("CF-RAY"),
            request.headers.get("CF-IPCOUNTRY"),
            f"{request.method.upper()} {request.url.include_query_params()}",
            body,
            response.status_code,
            resp,
        )

        async def put_paste_images(self, parent_id, tab_id) -> None:
            query = """INSERT INTO images VALUES($1, $2)"""

            await self._do_query(query, parent_id, tab_id)
