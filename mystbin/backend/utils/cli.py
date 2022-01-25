from __future__ import annotations

import argparse
import shlex
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import MystbinApp

class CLIHandler:
    def __init__(self, app: MystbinApp) -> None:
        self.app = app
        self.parser = argparse.ArgumentParser(
            prog="Mystbin",
            description="the Mystbin backend command-line tool",
            #exit_on_error=False,
            usage="",
            #add_help=False
        )
        self.parser.add_argument("-v", "--version", action="version", version="%(prog)s V3")

        self.subparsers = self.parser.add_subparsers(dest="command")
        sub_help = self.subparsers.add_parser("help", help="send this menu")

        self.subparser_paste = self.subparsers.add_parser("paste", help="subcommand to manage pastes. use 'paste -h' to see more info")
        self.subparser_paste.add_argument("paste", help="the ID of the paste to manage")
        self.subparser_paste.add_argument("--delete", "-d", help="delete the paste", action="store_true")
        self.subparser_paste.add_argument("--set-password", "-sp", help="set the password for this paste", metavar="PASSWORD")
        self.subparser_paste.add_argument("--remove-password", "-rp", help="remove the password for this paste", action="store_true")
        self.subparser_paste.add_argument("--list", "-l", help="list all pastes in the order they were created (most recent first)", action="store_true")

        self.subparser_admin = self.subparsers.add_parser("admin", help="subcommand to manage administrator accounts. use 'admin -h' to see more info")
        self.subparser_admin.add_argument("--add", "-a", help="give the target user admin privileges", metavar="USERID")
        self.subparser_admin.add_argument("--remove", "-r", help="remove admin privileges from the target user", metavar="USERID")
        self.subparser_admin.add_argument("--list", "-l", help="list the users with admin privileges", action="store_true")

        self.subparser_users = self.subparsers.add_parser("users", help="subcommand to manage user accounts. use 'users -h' to see more info")
        self.subparser_users.add_argument("--list", "-l", help="list all users", action="store_true")
        self.subparser_users.add_argument("--remove", "-r", help="remove the target user's account. this will delete all pastes linked to the account.", metavar="USERID")

    async def parse_cli(self) -> None:
        ...

    async def parse_once(self, inp: str) -> None:
        args = shlex.split(inp)
        try:
            ns: argparse.Namespace = self.parser.parse_args(args)
        except SystemExit:
            return
        else:
            print(ns)
            if not ns.command:
                return
            
            cb = getattr(self, f"command_{ns.command}", None)
            if cb:
                await cb(ns)


    # subcommands

    async def command_help(self, namespace: argparse.Namespace) -> None:
        ...

    async def command_paste(self, namespace: argparse.Namespace) -> None:
        ...

    async def command_admin(self, namespace: argparse.Namespace) -> None:
        ...

    async def command_users(self, namespace: argparse.Namespace) -> None:
        ...

if __name__ == "__main__":
    import asyncio
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    os.chdir(os.path.dirname(os.path.dirname(__file__)))
    from main import MystbinApp
    app = MystbinApp()
    c = CLIHandler(app)
    asyncio.run(c.parse_once("paste"))
    