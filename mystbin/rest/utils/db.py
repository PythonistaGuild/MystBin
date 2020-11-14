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
from typing import List, Optional, Union

import asyncpg

from . import tokens


EPOCH = 1587304800000  # 2020-04-20T00:00:00.0 * 1000 (Milliseconds)


class Database:
    """Small Database style object for MystBin usage.
    This will be passed across the backend for database usage.

    # TODO: Document methods and attrs.
    """
    timeout = 30

    def __init__(self, app):
        self._pool: asyncpg.pool.Pool = None
        self._config = app.config['database']
        self._db_schema = pathlib.Path(self._config['schema_path'])

    @property
    def pool(self) -> Optional[asyncpg.pool.Pool]:
        """ Property for easier access to attr. """
        return self._pool or None

    async def __ainit__(self):
        self._pool = await asyncpg.create_pool(self._config['dsn'], max_inactive_connection_lifetime=0)
        with open(self._db_schema) as schema:
            await self._pool.execute(schema.read())
        return self

    async def _do_query(self, query, *args, conn: asyncpg.Connection = None) -> Optional[List[asyncpg.Record]]:
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

    async def get_paste(self, paste_id: str, password: Optional[str] = None) -> Optional[asyncpg.Record]:
        """ Get the specified paste.
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
        query = """
                SELECT *,
                CASE WHEN password IS NOT NULL THEN true
                ELSE false END AS has_password,
                CASE WHEN password = CRYPT($2, password) THEN true
                ELSE false END AS password_ok

                FROM pastes WHERE id = $1
                """

        resp = await self._do_query(query, paste_id, password or "")

        if resp:
            return resp[0]
        return None

    async def put_paste(self,
                        paste_id: str,
                        content: str,
                        author: Optional[int] = None,
                        nick: str = "",
                        syntax: str = "",
                        password: Optional[str] = None
                        ) -> asyncpg.Record:
        """Puts the specified paste.
        Parameters
        -----------
        paste_id: :class:`str:
            The paste ID we are storing.
        content: :class:`str`
            The paste content.
        author: Optional[:class:`int`]
            The ID of the author, if present.
        nick: Optional[:class:`str`]
            The nickname of the paste, if present.
        syntax: Optional[:class:`str`]
            The paste syntax, if present.
        password: Optioanl[:class:`str`]
            The password used to encrypt the paste, if present.

        Returns
        ---------
        :class:`asyncpg.Record`
            The paste record that was created.
        """
        query = """
                INSERT INTO pastes (id, author, nick, syntax, password, loc, charcount, content)
                VALUES ($1, $2, $3, $4, (SELECT crypt($5, gen_salt('bf')) WHERE $5 is not null), $6, $7, $8)
                RETURNING *
                """

        loc = content.count("\n") + 1
        chars = len(content)

        resp = await self._do_query(query, paste_id, author, nick, syntax, password, loc, chars, content)

        return resp[0]

    async def edit_paste(self,
                         paste_id: str,
                         author_id: int,
                         new_content: Optional[str] = None,
                         new_expires: Optional[datetime.datetime] = None,
                         new_nick: Optional[str] = None) -> asyncpg.Record:
        """ Edits a live paste
        Parameters
        ------------
        paste_id: :class:`str`
            The paste ID we intend to edit.
        author: :class:`int`
            The paste author.
        new_content: Optional[:class:`str`]
            The new paste content we are inserting.
        new_expires: Optional[:class:`datetime.datetime`]
            The new expiration time.
        new_nick: Optional[:class:`str`]
            The new nickname of the paste.

        Returns
        ---------
        :class:`asyncpg.Record`
            The paste record which was edited.
        """
        query = """
                UPDATE pastes
                SET content = COALESCE($3, content),
                expires = COALESCE($4, expires),
                nick = COALESCE($5, nick)
                WHERE id = $1
                AND author = $2
                RETURNING *;
                """

        response = await self._do_query(query, paste_id, author_id, new_content, new_expires, new_nick)

        print(response)

        return response or 404

    async def get_all_pastes(self, author_id: Optional[int], limit: Optional[int] = None) -> Optional[List[asyncpg.Record]]:
        """ Get all pastes for an author and/or with a limit.
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
                SELECT id, author, nick, syntax, loc, charcount, created_at,
                CASE WHEN password IS NOT NULL THEN true ELSE false END AS has_password
                FROM pastes
                WHERE author = $1
                ORDER BY created_at DESC
                LIMIT $2
                """

        response = await self._do_query(query, author_id, limit)

        return response

    async def delete_paste(self,
                           paste_id: str,
                           author_id: Optional[int] = None,
                           *,
                           admin: bool = False) -> asyncpg.Record:
        """
        Delete a paste, with an admin override.

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
                DELETE FROM pastes
                WHERE (id = $1 AND author = $2)
                OR (id = $1 AND $3)
                RETURNING id;
                """

        response = await self._do_query(query, paste_id, author_id, admin)

        return response[0]

    async def get_user(self, *,
                       user_id: int = None,
                       token: str = None) -> Optional[Union[asyncpg.Record, int]]:
        """
        Returns a User on successful query.

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
        if token and data['token'] != token:
            return 401

        return data

    async def new_user(self,
                       email: str,
                       discord_id: int = None,
                       github_id: int = None,
                       google_id: int = None
                       ) -> asyncpg.Record:
        """ Creates a new User record.

        Parameters
        ------------
        email: :class:`str`
            The email address the user has registered with.
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
                VALUES ($1, $2, $3, $4, $5, $6, false, DEFAULT, false, false)
                RETURNING *;
                """

        data = await self._do_query(query, userid, token, [email], discord_id, github_id, google_id)
        return data[0]

    async def update_user(self,
                          user_id: int,
                          email: Optional[str] = None,
                          discord_id: Optional[int] = None,
                          github_id: Optional[int] = None,
                          google_id: Optional[str] = None
                          ) -> Optional[str]:
        """ Updates an existing user account.

        Parameters
        ------------
        user_id: :class:`int`
            The ID of the user to edit.
        email: Optional[:class:`str`]
            The email to add to the User's list of emails.
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
                discord_id = COALESCE($1, discord_id),
                github_id = COALESCE($2, github_id),
                google_id = COALESCE($3, google_id)
                WHERE id = $4
                RETURNING token, emails;
                """

        data = await self._do_query(query, discord_id, github_id, google_id, user_id)
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

    async def check_email(self, email: str) -> Optional[int]:
        """ Quick check to query an email. """
        query = """
                SELECT id FROM users WHERE $1 = ANY(emails)
                """

        data = await self._do_query(query, email)
        if data:
            return data[0]['id']

    async def toggle_admin(self, userid: int, admin: bool) -> None:
        """ Quick query to toggle admin privileges. """
        query = """
                UPDATE users SET admin = $1 WHERE id = $2
                """

        await self._do_query(query, admin, userid)

    async def switch_theme(self, userid: int, theme: str) -> None:
        """ Quick query to set theme choices. """
        query = """
                UPDATE users SET theme = $1 WHERE id = $2
                """

        await self._do_query(query, theme, userid)

    async def regen_token(self, *, userid: int=None, token: str=None) -> Optional[str]:
        """
        Generates a new token for the given user id or token. Returns the new token, or None if the user does not exist
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

                userid = data[0]['id']

            new_token = tokens.generate(userid)
            query = """
                    UPDATE users SET token = $1 WHERE id = $2 RETURNING id
                    """
            data = await self._do_query(query, new_token, userid, conn=conn)
            if not data:
                return None

            return token

    async def ensure_authorization(self, token: str) -> bool:
        """ Quick query against a passed token. """
        if not token:
            return False

        query = """
                SELECT id FROM users WHERE token = $1
                """

        data = await self._do_query(query, token)
        if not data:
            return False

        return data[0]['id']

    async def ensure_admin(self, token: str) -> bool:
        """ Quick query against a token to return if admin or not. """
        if not token:
            return False

        query = """
                SELECT admin FROM users WHERE token = $1
                """

        data = await self._do_query(query, token)
        if not data:
            return False

        return data[0]['admin']

    async def ensure_author(self, paste_id: str, author_id: int) -> bool:
        """ Quick query to ensure a paste is owned by the passed author ID. """

        query = """
                SELECT id
                FROM pastes
                WHERE id = $1
                AND author = $2;
                """

        response = await self._do_query(query, paste_id, author_id)
        if response:
            return True
        return False
