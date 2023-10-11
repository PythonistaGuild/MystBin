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
import uuid
from typing import Any, Awaitable, Callable, Literal, cast

import asyncpg
import msgspec
from asyncpg import Record
from models import payloads, responses
from starlette.requests import Request
from starlette.responses import Response

from . import gravatar, tokens


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
        self._pool: asyncpg.Pool | None = None
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
        self._pool = await asyncpg.create_pool(
            self._config["dsn"], max_inactive_connection_lifetime=3, max_size=3, min_size=0
        )
        self._listener_pool = cast(
            asyncpg.Pool,
            await asyncpg.create_pool(self._config["dsn"], max_inactive_connection_lifetime=0, max_size=9999, min_size=0),
        )
        # with open(self._db_schema) as schema:
        #    await self._pool.execute(schema.read())
        return self

    async def _do_query(self, query: str, *args, conn: asyncpg.Connection | None = None) -> list[asyncpg.Record]:
        if self._pool is None:
            await self.__ainit__()

        _conn = conn or await cast(asyncpg.Pool, self._pool).acquire()
        try:
            response = await _conn.fetch(query, *args, timeout=self.timeout)
        except asyncio.TimeoutError:
            return []
        else:
            return response
        finally:
            if not conn:
                await self.pool.release(_conn)

    async def create_listener(self, fn: Callable[[str, str, str, str], Awaitable[None]]) -> asyncpg.Connection:
        conn: asyncpg.Connection = await self._listener_pool.acquire()
        await conn.add_listener("paste_requests", fn)
        return conn

    async def release_listener(self, conn: asyncpg.Connection, fn: Callable[[str, str, str, str], Awaitable[None]]) -> None:
        await conn.remove_listener("paste_requests", fn)
        await self._listener_pool.release(conn)

    @wrapped_hook_callback
    async def get_all_pastes(self, page: int, count: int, reverse=False) -> list[dict[str, Any]]:
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
        results = await self._do_query(query, count, page * count)
        if not results:
            return []
        return [dict(x) for x in results]

    # for anyone who wonders why this doesnt have a wrapped hook on it, it's because the endpoints for this particular
    # db call have to validate the data themselves, and then manually call the hook, so theres no point repeating the
    # process twice
    async def get_paste(self, paste_id: str, password: str | None = None) -> dict[str, Any] | None:
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
                contents: list[asyncpg.Record] = await self._do_query(query, paste_id, conn=conn)
                resp = dict(resp[0])
                resp["files"] = [responses.create_struct(x, responses.File) for x in contents]
                return resp
            else:
                return None

    @wrapped_hook_callback
    async def get_paste_compat(self, paste_id: str) -> dict[str, str] | None:
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
                SELECT content FROM files WHERE parent_id = $1 LIMIT 1
                """
                contents: list[asyncpg.Record] = await self._do_query(query, paste_id, conn=conn)
                ret = {
                    "key": paste_id,
                    "data": contents[0]["content"],
                    "has_password": resp[0]["has_password"],
                }

                return ret
            else:
                return None

    @wrapped_hook_callback
    async def get_token_pastes(
        self, user_id: int | None, token_id: int, verify_user: bool = True
    ) -> list[responses.PasteGetAll] | None:
        """Fetches all pastes that are generated with a specific token.
        If verify_user is True, the user_id must match the user that generated the token.

        Parameters
        -----------
        user_id: class:`int` | None
            The user that is making the request
        token_id: :class:`int`
            The token to fetch pastes for
        verify_user: :class:`bool` = True
            Whether to verify if the user_id matches that of the token_id

        Returns
        --------
        list[PasteGetAll] | None
        """
        if not self._pool:
            await self.__ainit__()

        async with self.pool.acquire() as conn:
            if verify_user:
                query = "SELECT 1 FROM tokens WHERE id = $1 AND user_id = $2"
                if not await conn.fetchval(query, token_id, user_id):
                    return None

            query = """
                    SELECT
                        id,
                        author_id,
                        created_at,
                        last_edited AS edited_at,
                        (SELECT password IS NOT NULL) AS has_password,
                        expires,
                        views
                    FROM pastes
                    WHERE
                        token_id = $1
                    """

            resp = await self._do_query(query, token_id, conn=conn)
            return [responses.PasteGetAll(**record) for record in resp]

    @wrapped_hook_callback
    async def get_raw_paste_info(self, paste_id: str, password: str | None) -> dict[str, Any] | None:
        query = """
                SELECT
                    filename,
                    charcount,
                    content,
                    pastes.author_id,
                    pastes.created_at,
                    pastes.views,
                    CASE WHEN pastes.password IS NOT NULL THEN true
                    ELSE false END AS has_password,
                    CASE WHEN pastes.password = CRYPT($2, password) THEN true
                    ELSE false END AS password_ok
                FROM files
                INNER JOIN pastes
                ON pastes.id = files.parent_id
                WHERE
                    parent_id = $1
                ORDER BY
                    index
        """
        resp = await self._do_query(query, paste_id, password)
        if not resp:
            return None

        r0 = resp[0]
        return {
            "views": r0["views"],
            "created_at": r0["created_at"],
            "author_id": r0["author_id"],
            "has_password": r0["has_password"],
            "password_ok": r0["password_ok"],
            "files": [
                {"filename": x["filename"], "content": x["content"], "charcount": x["charcount"], "n": i}
                for i, x in enumerate(resp)
            ],
        }

    @wrapped_hook_callback
    async def put_paste(
        self,
        *,
        paste_id: str,
        origin_ip: str | None,
        pages: list[payloads.RichPasteFile] | list[payloads.PasteFile],
        token_id: int | None,
        expires: datetime.datetime | None = None,
        author: int | None = None,
        password: str | None = None,
        public: bool = True,
    ) -> dict[str, str | int | None | list[dict[str, str | int]]]:
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
        token_id: Optional[:class:`uuid.UUID`]
            The token that created this paste. Used for token analytics.
        public: :class:`bool`
            Is this paste private? defaults to True.

        Returns
        ---------
        Dict[str, Optional[Union[str, int, datetime.datetime]]]
        """
        if not self._pool:
            await self.__ainit__()

        async with self.pool.acquire() as conn:
            query = """
                    INSERT INTO pastes (id, author_id, expires, password, origin_ip, token_id, public)
                    VALUES ($1, $2, $3, (SELECT crypt($4, gen_salt('bf')) WHERE $4 is not null), $5, $6, $7)
                    RETURNING id, author_id, created_at, expires, origin_ip
                    """

            resp: list[asyncpg.Record] = await self._do_query(
                query, paste_id, author, expires, password, origin_ip, token_id, public, conn=conn
            )

            resp = resp[0]
            to_insert = []
            for page in pages:
                to_insert.append(
                    (
                        resp["id"],  # type: ignore # TODO??
                        page.content,
                        page.filename,
                        page.content.count("\n") + 1,  # add an extra for line 1
                        getattr(page, "attachment", None),
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

            formatted_resp = dict(resp)
            del formatted_resp["origin_ip"]
            formatted_resp["files"] = [responses.create_struct(file, responses.File) for file in inserted]

            return formatted_resp

    @wrapped_hook_callback
    async def edit_paste(
        self,
        paste_id: str,
        *,
        author: int,
        new_expires: datetime.datetime | None = None,
        new_password: str | None = None,
        files: list[payloads.PasteFile] | None = None,
        private: bool | None = None,
    ) -> Literal[404] | None:
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
                    expires = $4,
                    private = COALESCE($5, private)
                    WHERE id = $1 AND author_id = $2
                    RETURNING *
                    """

            resp = await self._do_query(query, paste_id, author, new_password, new_expires, private, conn=conn)
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
    async def set_paste_password(self, paste_id: str, password: str | None) -> asyncpg.Record | None:
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
    async def get_all_user_pastes(
        self, author_id: int | None, limit: int, page: int, author_handle: str | None = None, public_only: bool = False
    ) -> list[asyncpg.Record]:
        """Get all pastes for an author and/or with a limit.
        Parameters
        ------------
        author_id: :class:`int` | None
            The paste author id to query against.
        limit: :class:`int`
            The limit to the amount of pastes to return.
        page: :class:`int`
            The page number. This is relative to the limit per page (eg changing the limit will change your offset)
        author_handle: :class:`str`
            The paste author handle to query against.
        public_only: :class:`bool`
            Whether to only return public pastes.

        Returns
        ---------
        Optional[List[:class:`asyncpg.Record`]]
            The potential list of pastes.
        """
        query = f"""
                WITH (
                    SELECT COALESCE(CASE
                        WHEN $1 IS NOT NULL THEN $1
                        WHEN $4 IS NOT NULL THEN (
                            SELECT id FROM users WHERE handle = $4
                        )
                        ELSE ''
                        END,
                        0)
                ) AS true_author_id
                SELECT 
                    id,
                    author_id,
                    created_at,
                    views,
                    expires,
                    CASE
                        WHEN password IS NOT NULL
                        THEN true
                        ELSE false
                        END
                    AS has_password
                FROM pastes
                WHERE
                    author_id = (SELECT true_author_id)
                    {'AND public = true' if public_only else ''}
                ORDER BY created_at DESC
                LIMIT $2
                OFFSET $3
                """
        if not author_id and not author_handle:
            raise ValueError("One of author_id or author_handle must be specified.")

        assert page >= 1 and limit >= 1, ValueError("limit and page cannot be smaller than 1")
        response = await self._do_query(query, author_id, limit, page - 1, author_handle)
        if not response:
            return []

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
    async def delete_paste(self, paste_id: str, author_id: int | None = None, *, admin: bool = False) -> str | None:
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

    async def put_paste_request(self, slug: str, author_id: int) -> None:
        """Creates a paste request

        Parameters
        -----------
        slug: :class:`str`
            The request slug. Usually 3 random words.
        author_id: :class:`int`
            The user who made the request for the paste.

        Raises
        -------
        ValueError: The slug is taken.
        """

        query = """
        INSERT INTO
            requested_pastes
        VALUES
            ($1, $2)
        """

        try:
            await self._do_query(query, slug, author_id)
        except asyncpg.IntegrityConstraintViolationError as e:
            raise ValueError("slug is taken") from e

    async def get_paste_request(self, slug: str, user_id: int, conn: asyncpg.Connection | None = None) -> str | None:
        """
        Determines if a paste request exists.

        Parameters
        -----------
        slug: :class:`str`
            The request slug. Usually 3 random words.
        user_id: :class:`int`
            The user who made the request for the paste.

        Returns
        --------
        :class:`str` | None
            Returns the new slug, if the request has been fulfilled. Otherwise, returns an empty string.
            Returns None if the request does not exist.
        """

        query = """
        SELECT
            fulfilled_slug
        FROM requested_pastes
        WHERE
            requester = $1 AND id = $2
        """

        resp = await self._do_query(query, user_id, slug, conn=conn)
        if not resp:
            return None

        return resp[0]["fulfilled_slug"] or ""

    async def fulfill_paste_request(self, slug: str, user_id: int, paste_slug: str) -> None:
        if not self._pool:
            await self.__ainit__()

        async with cast(asyncpg.Pool, self._pool).acquire() as conn:
            conn: asyncpg.Connection
            await conn.execute(
                "SELECT pg_notify('paste_requests', $1);",
                msgspec.json.encode({"slug": slug, "user_id": user_id, "paste_slug": paste_slug}).decode(),
            )
            await conn.execute(
                "UPDATE requested_pastes SET fulfilled_slug = $3 WHERE requester = $1 AND id = $2", user_id, slug, paste_slug
            )

    @wrapped_hook_callback
    async def get_user(self, *, user_id: int | None = None, token: str | None = None) -> asyncpg.Record | int | None:
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
            t = tokens.get_user_id(token)
            if not t:
                return 400

            user_id = t[0]

        query = """
                SELECT * FROM users WHERE id = $1
                """

        data = await self._do_query(query, user_id)
        if not data:
            return None

        return data[0]

    @wrapped_hook_callback
    async def update_user_handle(self, user_id: int, handle: str) -> bool:
        """
        Updates a user's handle.

        Parameters
        ------------
        user_id: :class:`int`
            The user id to update.
        handle: :class:`str`
            The new handle.

        Returns
        --------
        :class:`bool`
            was the update successful? if failed, validation failed or the handle is taken.
        """
        if len(handle) > 32 or handle.strip().replace(" ", "-").lower() != handle:
            return False

        query = """
            UPDATE users SET handle = $1, needs_handle_modal = FALSE WHERE id = $2
        """

        try:
            await self._do_query(query, handle, user_id)
            return True
        except:
            return False

    async def _create_default_token(self, user_id, token_key, conn: asyncpg.Connection | None = None) -> int:
        query = """
                INSERT INTO
                tokens
                (user_id, token_name, token_key, is_main)
                VALUES
                ($1, 'Default Token', $2, true)
                RETURNING id
                """

        resp = await self._do_query(query, user_id, token_key, conn=conn)
        return resp[0]["id"]

    @wrapped_hook_callback
    async def new_user(
        self,
        emails: list[str],
        username: str,
        discord_id: str | None = None,
        github_id: str | None = None,
        google_id: str | None = None,
    ) -> tuple[dict, str]:
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
        :class:`asyncpg.Record`, :class:`str`
            The record created for the registering User, and the token accompanying it, along with the user's current handle.
        """

        userid = int((datetime.datetime.utcnow().timestamp() * 1000) - EPOCH)
        token_key = uuid.uuid4()

        gravatar_hash = await gravatar.find_available_gravatar(emails, force_response=True)

        query = """
                INSERT INTO users
                (id, emails, discord_id, github_id, google_id, handle, gravatar_hash)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *;
                """

        async with self.pool.acquire() as conn:
            try:
                data = await self._do_query(
                    query,
                    userid,
                    emails,
                    discord_id and str(discord_id),
                    github_id and str(github_id),
                    google_id and str(google_id) or None,
                    username.lower().replace(" ", "-")[:32],
                    gravatar_hash,
                    conn=conn,
                )
            except asyncpg.UniqueViolationError:  # the name is taken, so we default to the user id
                data = await self._do_query(
                    query,
                    userid,
                    emails,
                    discord_id and str(discord_id),
                    github_id and str(github_id),
                    google_id and str(google_id) or None,
                    str(userid),
                    gravatar_hash,
                    conn=conn,
                )

            token_id = await self._create_default_token(userid, token_key, conn=conn)

            token = tokens.generate(userid, token_key, token_id)
            return data[0], token

    async def update_user_on_login(
        self,
        user_id: int,
        emails: list[str] | None = None,
        discord_id: str | None = None,
        github_id: str | None = None,
        google_id: str | None = None,
    ) -> tuple[str | None, bool, str]:
        """Updates an existing user account with the login provided.

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
        tuple[:class:`str` | None, bool, str]
            Returns the updated user's token, and whether or not they need to be presented with a handle selection modal, and their current handle.
        """

        if emails:
            new_gravatar_hash = await gravatar.find_available_gravatar(emails, force_response=False)
        else:
            new_gravatar_hash = None

        query = """
                UPDATE users SET
                    discord_id = COALESCE($1, discord_id),
                    github_id = COALESCE($2, github_id),
                    google_id = COALESCE($3, google_id),
                    emails = CASE 
                        WHEN $5::text[] IS NOT NULL THEN
                            (ARRAY( SELECT DISTINCT unnest(emails || $5::text[]) ))
                        ELSE
                            emails
                    END,
                    gravatar_hash = COALESCE($6, gravatar_hash)
                WHERE
                    id = $4
                RETURNING
                    (SELECT tokens.id FROM tokens WHERE tokens.user_id = $4 AND tokens.is_main = true) as token_id,
                    (SELECT tokens.token_key FROM tokens WHERE tokens.user_id = $4 AND tokens.is_main = true) as token_key,
                    NOT user_has_selected_handle,
                    handle;
                """

        data = await self._do_query(
            query,
            discord_id and str(discord_id),
            github_id and str(github_id),
            google_id and str(google_id),
            user_id,
            emails,
            new_gravatar_hash,
        )
        if not data:
            raise RuntimeError("attempted to update user that does not exist")

        token_id, token_key, user_needs_modal, handle = data[0]

        if not token_id:
            token_key = uuid.uuid4()
            token_id = await self._create_default_token(user_id, token_key)

        token = tokens.generate(user_id, token_key, token_id)

        return token, user_needs_modal, handle

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

    async def check_email(self, emails: str | list[str]) -> int | None:
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

    async def list_admin(self) -> list[asyncpg.Record]:
        query = """
        SELECT id, handle, discord_id, github_id, google_id FROM users WHERE admin = true
        """
        resp = await self._do_query(query)
        return resp or []

    @wrapped_hook_callback
    async def ban_user(self, userid: int | None = None, ip: str | None = None, reason: str | None = None) -> bool:
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

    async def unban_user(self, userid: int | None = None, ip: str | None = None) -> bool:
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
    async def toggle_subscription(self, userid: int, state: bool):
        query = "UPDATE users SET subscriber = $1 WHERE id = $2 AND subscriber != $1 RETURNING id;"
        val = await self._do_query(query, state, userid)
        return len(val) > 0

    @wrapped_hook_callback
    async def regen_token(self, *, userid: int, token_id: int) -> str | None:
        """Generates a new token for the given user id and token id.
        Returns the new token, or None if the user/token does not exist.
        """
        if not self._pool:
            await self.__ainit__()

        async with self.pool.acquire() as conn:
            new_token_key = uuid.uuid4()
            new_token = tokens.generate(userid, new_token_key, token_id)

            query = """
                    UPDATE tokens
                    SET
                    token_key = $1
                    WHERE id = $2 AND user_id = $3
                    RETURNING id
                    """

            resp = await conn.fetchval(query, new_token_key, token_id, userid)
            if resp:
                return new_token

            return None

    @wrapped_hook_callback
    async def get_tokens(self, userid: int) -> list[dict]:
        """
        Gets token metadata for a user.
        """

        query = "SELECT id, token_name, token_description, is_main FROM tokens where user_id = $1"

        data = await self._do_query(query, userid)
        return data

    @wrapped_hook_callback
    async def create_token(self, user_id: int, name: str, description: str) -> tuple[str, int] | None:
        query = """
                INSERT INTO
                tokens
                (user_id, token_name, token_description, token_key, is_main)
                VALUES
                ($1, $2, $3, $4, false)
                RETURNING id
                """

        token_key = uuid.uuid4()
        try:
            resp = await self._do_query(query, user_id, name, description, token_key)
        except (asyncpg.CheckViolationError, asyncpg.StringDataRightTruncationError):
            return None

        token = tokens.generate(user_id, token_key, resp[0]["id"])
        return token, resp[0]["id"]

    async def delete_token(self, user_id: int, token_id: int) -> bool:
        query = """
                DELETE FROM
                tokens
                WHERE
                id = $1
                AND
                user_id = $2
                RETURNING id
                """

        resp = await self._do_query(query, token_id, user_id)
        return bool(resp)

    async def get_user_style(self, userid: int) -> responses.Style | None:
        """
        Gets the style the user set, or None if they didn't set any
        """
        query = """
                SELECT
                    primary_bg,
                    secondary_bg,
                    primary_font,
                    secondary_font,
                    accent,
                    prism_theme
                FROM styles
                WHERE userid = $1
                """

        data = await self._do_query(query, userid)
        if data:
            return responses.Style(**data[0])

    async def set_user_style(self, userid: int, style: responses.Style) -> None:
        query = """
                INSERT INTO styles
                    (userid, primary_bg, secondary_bg, primary_font, secondary_font, accent, prism_theme)
                VALUES
                    ($1,$2,$3,$4,$5,$6,$7)
                ON CONFLICT (userid)
                DO UPDATE SET
                    primary_bg = $2,
                    secondary_bg = $3,
                    primary_font = $4,
                    secondary_font = $5,
                    accent = $6,
                    prism_theme = $7
                """

        await self._do_query(
            query,
            userid,
            style.primary_bg,
            style.secondary_bg,
            style.primary_font,
            style.secondary_font,
            style.accent,
            style.prism_theme,
        )

    @wrapped_hook_callback
    async def get_bookmarks(self, userid: int) -> list[dict[str, Any]]:
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

    async def create_bookmark(self, userid: int, paste_id: str) -> None:  # doesnt return anything, no need for a hook
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
    async def ensure_admin(self, token_id: uuid.UUID) -> bool:
        """Quick query against a token to return if admin or not."""
        if not token_id:
            return False

        query = """
                SELECT users.admin
                FROM tokens
                INNER JOIN users
                ON users.id = tokens.user_id
                WHERE token_id = $1
                """

        data = await self._do_query(query, token_id)
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
    async def get_admin_userlist(self, page: int) -> dict[str, int | dict[str, int | bool | None]]:
        query = """
                SELECT
                    id,
                    handle,
                    github_id,
                    discord_id,
                    google_id,
                    admin,
                    gravatar_hash,
                    (SELECT COUNT(*) FROM pastes WHERE author_id = users.id) AS paste_count
                FROM users LIMIT 20 OFFSET $1 * 20;
        """
        if not self._pool:
            await self.__ainit__()

        async with self.pool.acquire() as conn:
            users = await self._do_query(query, page - 1, conn=conn)
            records: list[Record] = await self._do_query("SELECT COUNT(*) AS count FROM users", conn=conn)
            pageinfo: int = records[0]["count"]

        users = [
            {
                "id": x["id"],
                "handle": x["handle"],
                "admin": x["admin"],
                "paste_count": x["paste_count"],
                "gravatar_hash": x["gravatar_hash"],
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
        return {"users": users, "user_count": pageinfo, "page": page}  # type: ignore # that's

    async def get_admin_usercount(self) -> int:
        query = "SELECT COUNT(id) AS count FROM users"
        data = await self._do_query(query)
        return data[0]["count"]

    @wrapped_hook_callback
    async def search_bans(
        self, *, ip: str | None = None, userid: int | None = None, search: str | None = None
    ) -> str | list[dict[str, Any]] | None:
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
        assert search
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

        user_id: int | None = request.state.user and request.state.user["id"]
        route = f"{request.method.upper()} {request.url.path}{'?' + request.url.query if request.url.query else ''}"

        if route == "DELETE /users/@me":
            user_id = None  # fix foreign key violation when the account has been deleted

        await self._do_query(
            query,
            request.headers.get("X-Forwarded-For", request.client.host if request.client else "IP unknown"),
            user_id,
            datetime.datetime.utcnow(),
            request.headers.get("CF-RAY"),
            request.headers.get("CF-IPCOUNTRY"),
            route,
            body,
            response.status_code,
            resp,
        )

    async def delete_user(self, user_id: int, keep_pastes: bool) -> None:
        """
        Deletes a user's account.
        This simply calls the underlying SQL function created in the schema,
        refer to the SQL function for implementation details.
        """
        query = "SELECT public.deleteUserAccount($1::bigint, $2::boolean) AS pain"
        await self._do_query(query, user_id, keep_pastes)
