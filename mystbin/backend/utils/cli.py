from __future__ import annotations

import asyncio
import argparse
import shlex
from typing import TYPE_CHECKING, Any, Optional

import aioconsole

if TYPE_CHECKING:
    from main import MystbinApp
    from utils.db import Database


def find_disallowed_args(ns: argparse.Namespace, args: list[str], allowed_values: tuple = (None, False)) -> list[str]:
    return [arg for arg in args if getattr(ns, arg) not in allowed_values]


class CLIHandler:
    def __init__(self, app: MystbinApp) -> None:
        self.app = app
        self.db: Database = app.state.db
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
        self.subparsers.add_parser("exit", help="shuts down the mystbin backend server")

        self.subparser_paste = self.subparsers.add_parser(
            "paste", help="subcommand to manage pastes. use 'paste -h' to see more info"
        )
        # self.subparser_paste.add_argument("paste", help="the ID of the paste to manage", metavar="PASTE_ID", required=False)
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
            help="list all pastes in the order they were created (most recent first)",
            action="store_true",
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
        self.subparser_users.add_argument("--list", "-l", help="list all users", action="store_true")
        self.subparser_users.add_argument(
            "--remove",
            "-r",
            help="remove the target user's account. this will delete all pastes linked to the account.",
            metavar="USERID",
        )

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
                await cb(ns)

    # subcommands

    async def command_help(self, namespace: argparse.Namespace) -> None:
        self.parser.print_help()

    async def command_paste(self, namespace: argparse.Namespace) -> None:
        if namespace.list:
            ...

        elif namespace.delete:
            if bad_args := find_disallowed_args(namespace, ["remove_password", "list", "set_password"]):
                print(
                    f"Paste: The following args cannot be used with the `delete` argument: {','.join(bad_args).replace('_', '-')}"
                )
                return

            resp = await self.db.delete_paste(namespace.delete, admin=True)
            if resp:
                author = f"by user {resp['author_id']} " if resp["author_id"] else ""
                password = f"and password '{resp['password']}'" if resp["password"] else ""
                print(f"Deleted paste '{namespace.delete}' {author}with {resp['views']} views {password}")
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
                print(f"paste '{pid}' not found")

        elif namespace.remove_password:
            if bad_args := find_disallowed_args(namespace, ["set_password", "list", "delete"]):
                print(
                    f"Paste: The following args cannot be used with the `remove-password` argument: {','.join(bad_args)}"
                )
                return

            resp = await self.db.set_paste_password(namespace.remove_password, None)
            if resp:
                print(f"Updated password for paste '{namespace.remove_password}'")
            else:
                print(f"paste '{namespace.remove_password}' not found")

        else:
            print("Paste: one argument must be passed")
            self.subparser_paste.print_help()

    async def command_admin(self, namespace: argparse.Namespace) -> None:
        ...

    async def command_users(self, namespace: argparse.Namespace) -> None:
        ...

    async def command_exit(self, _) -> None:
        self.app.should_close = True
        raise KeyboardInterrupt


if __name__ == "__main__":
    import asyncio
    import sys, os

    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    os.chdir(os.path.dirname(os.path.dirname(__file__)))

    async def main():
        from main import MystbinApp

        app = MystbinApp()
        c = CLIHandler(app)
        await c.parse_cli()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
