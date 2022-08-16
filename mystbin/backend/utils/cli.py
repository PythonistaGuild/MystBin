from __future__ import annotations

import asyncio
import argparse
import shlex
from typing import TYPE_CHECKING

import aioconsole
import tabulate

if TYPE_CHECKING:
    from utils.db import Database


def find_disallowed_args(ns: argparse.Namespace, args: list[str], allowed_values: tuple = (None, False)) -> list[str]:
    return [arg for arg in args if getattr(ns, arg) not in allowed_values]


class Interrupt(Exception):
    pass


class CLIHandler:
    def __init__(self, db: Database) -> None:
        self.db: Database = db
        self.parser = argparse.ArgumentParser(
            prog="Mystbin",
            description="the Mystbin backend command-line tool",
            exit_on_error=False,
            usage="",
            add_help=False,
        )
        self.parser.add_argument("--version", "-v", action="version", version="%(prog)s V3")

        self.subparsers = self.parser.add_subparsers(dest="command")
        self.subparsers.add_parser("help", help="send this menu")

        self.subparser_paste = self.subparsers.add_parser(
            "paste", help="subcommand to manage pastes. use 'paste -h' to see more info"
        )
        self.subparser_paste.add_argument("--delete", "-d", help="delete the paste", metavar="PASTE_ID")
        self.subparser_paste.add_argument(
            "--set-password", "-sp", help="set the password for this paste", metavar=("PASTE_ID", "PASSWORD"), nargs=2
        )
        self.subparser_paste.add_argument(
            "--remove-password", "-rp", help="remove the password for this paste", metavar="PASTE_ID"
        )
        self.subparser_paste.add_argument(
            "--list",
            "-l",
            help="list all pastes in the order they were created (most recent first). 50 per page",
            metavar="PAGE",
        )

        self.subparser_admin = self.subparsers.add_parser(
            "admin", help="subcommand to manage administrator accounts. use 'admin -h' to see more info"
        )
        self.subparser_admin.add_argument("--add", "-a", help="give the target user admin privileges", metavar="USERID")
        self.subparser_admin.add_argument(
            "--remove", "-r", help="remove admin privileges from the target user", metavar="USERID"
        )
        self.subparser_admin.add_argument(
            "--list", "-l", help="list the users with admin privileges", action="store_true"
        )

        self.subparser_users = self.subparsers.add_parser(
            "users", help="subcommand to manage user accounts. use 'users -h' to see more info"
        )
        self.subparser_users.add_argument("--list", "-l", help="list all users. 50 per page", metavar="PAGE")

    async def parse_cli(self) -> None:
        await asyncio.sleep(1)  # wait until app startup and until the prints are done
        print("Entering the command line tool. Type 'help' for more information")
        try:
            while True:
                data = await aioconsole.ainput(prompt="> ")
                await self.parse_once(data)
                print("\n")
        except KeyboardInterrupt:
            return

    async def parse_once(self, inp: str) -> None:
        args = shlex.split(inp)
        try:
            ns: argparse.Namespace = self.parser.parse_args(args)
        except SystemExit:
            return
        except argparse.ArgumentError as e:
            print(e.message)
        else:
            print(ns)
            if not ns.command:
                return

            cb = getattr(self, f"command_{ns.command}", None)
            if cb:
                try:
                    await cb(ns)
                except Interrupt:
                    pass

    # subcommands

    async def command_help(self, namespace: argparse.Namespace) -> None:
        self.parser.print_help()

    async def command_paste(self, namespace: argparse.Namespace) -> None:
        if namespace.list:
            try:
                page = max(int(namespace.list) - 1, 0)
            except:
                print(f"Paste: Expected a page number, got '{namespace.list}'")
                return

            paste_info = await self.db.get_all_pastes(page, 50)
            if not paste_info:
                print(f"Paste: Page {page} not found")
                return

            tabled = tabulate.tabulate(
                [list(x.values()) for x in paste_info],
                headers=["id", "author id", "created at", "views", "expires", "origin ip", "has password"],
                tablefmt="psql",
            )
            await aioconsole.aprint(tabled)

            print(f"Paste: Showing {len(paste_info)} pastes (page {page+1})")

        elif namespace.delete:
            if bad_args := find_disallowed_args(namespace, ["remove_password", "list", "set_password"]):
                print(
                    f"Paste: The following args cannot be used with the `delete` argument: {','.join(bad_args).replace('_', '-')}"
                )
                return

            resp = await self.db.delete_paste(namespace.delete, admin=True)
            if resp:
                print(f"Deleted paste '{namespace.delete}'")
            else:
                print("Failed to delete paste (paste not found)")

        elif namespace.set_password:
            if bad_args := find_disallowed_args(namespace, ["remove_password", "list", "delete"]):
                print(
                    f"Paste: The following args cannot be used with the `set-password` argument: {','.join(bad_args)}"
                )
                return

            pid = namespace.set_password[0]
            password = namespace.set_password[1]

            resp = await self.db.set_paste_password(pid, password)
            if resp:
                print(f"Updated password for paste '{pid}'")
            else:
                print(f"Paste '{pid}' not found")

        elif namespace.remove_password:
            if bad_args := find_disallowed_args(namespace, ["set_password", "list", "delete"]):
                print(
                    f"Paste: The following args cannot be used with the `remove-password` argument: {','.join(bad_args)}"
                )
                return

            resp = await self.db.set_paste_password(namespace.remove_password, None)
            if resp:
                print(f"Removed password for paste '{namespace.remove_password}'")
            else:
                print(f"Paste '{namespace.remove_password}' not found")

        else:
            print("Paste: One argument must be passed")
            self.subparser_paste.print_help()

    async def command_admin(self, namespace: argparse.Namespace) -> None:
        def _try_userid(uid: str) -> int:
            try:
                return int(uid)
            except:
                print(f"Admin: Expected a user id, got '{uid}'")
                raise Interrupt

        if namespace.add:
            if bad_args := find_disallowed_args(namespace, ["remove", "list"]):
                print(f"Admin: The following args cannot be used with the `add` argument: {','.join(bad_args)}")
                return

            if await self.db.toggle_admin(_try_userid(namespace.add), True):
                print(f"{namespace.add} is now an admin")
            else:
                print("Admin: User not found")

        elif namespace.remove:
            if bad_args := find_disallowed_args(namespace, ["add", "list"]):
                print(f"Admin: The following args cannot be used with the `remove` argument: {','.join(bad_args)}")
                return

            if await self.db.toggle_admin(_try_userid(namespace.add), False):
                print(f"{namespace.add} is now not an admin")
            else:
                print("Admin: User not found")

        elif namespace.list:
            users = await self.db.list_admin()
            resp = tabulate.tabulate(
                [list(x.values()) for x in users],
                headers=["User ID", "Username", "Discord ID", "Github ID", "Google ID"],
                tablefmt="psql",
            )
            await aioconsole.aprint(resp)

    async def command_users(self, namespace: argparse.Namespace) -> None:
        if namespace.list:
            try:
                page = int(namespace.list)
            except:
                print(f"Users: expected an int, got {namespace.list!r}")
                return

            users: dict = (await self.db.get_admin_userlist(page))["users"]  # type: ignore
            if not users:
                print("Users: No users found")
                return

            for user in users:
                user["authorizations"] = ", ".join(user["authorizations"])

            fmt = tabulate.tabulate([list(x.values()) for x in users], headers=list(users[0].keys()), tablefmt="psql")
            await aioconsole.aprint(fmt)


if __name__ == "__main__":
    import asyncio
    import sys, os

    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    os.chdir(os.path.dirname(os.path.dirname(__file__)))

    async def main():
        from app import MystbinApp

        app = MystbinApp()
        c = CLIHandler(app.state.db)
        await c.parse_cli()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
