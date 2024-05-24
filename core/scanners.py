"""MystBin. Share code easily.

Copyright (C) 2020-Current PythonistaGuild

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import base64
import binascii
import enum
import logging
import re
from typing import ClassVar

from types_.scanner import ScannerSecret


logger: logging.Logger = logging.getLogger(__name__)


class Services(enum.Enum):
    discord = "Discord"
    pypi = "PyPi"
    github = "GitHub"


class BaseScanner:
    REGEX: ClassVar[re.Pattern[str]]
    SERVICE: Services

    @classmethod
    def match(cls, content: str) -> ScannerSecret:
        payload: ScannerSecret = {
            "service": cls.SERVICE,
            "tokens": set(cls.REGEX.findall(content)),
        }

        return payload


class DiscordScanner(BaseScanner):
    REGEX = re.compile(r"[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27,}")
    SERVICE = Services.discord

    @staticmethod
    def validate_discord_token(token: str) -> bool:
        try:
            # Just check if the first part validates as a user ID
            (user_id, _, _) = token.split(".")
            user_id = int(base64.b64decode(user_id + "==", validate=True))
        except (ValueError, binascii.Error):
            return False
        else:
            return True

    @classmethod
    def match(cls, content: str) -> ScannerSecret:
        payload: ScannerSecret = {
            "service": cls.SERVICE,
            "tokens": {t for t in cls.REGEX.findall(content) if cls.validate_discord_token(t)},
        }

        return payload


class PyPiScanner(BaseScanner):
    REGEX = re.compile(r"pypi-AgEIcHlwaS5vcmc[A-Za-z0-9-_]{70,}")
    SERVICE = Services.pypi


class GitHubScanner(BaseScanner):
    REGEX = re.compile(r"((ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36})")
    SERVICE = Services.github

    @classmethod
    def match(cls, content: str) -> ScannerSecret:
        payload: ScannerSecret = {
            "service": cls.SERVICE,
            "tokens": {t[0] for t in cls.REGEX.findall(content)},
        }

        return payload


class SecurityInfo:
    __SERVICE_MAPPING: ClassVar[dict[Services, type[BaseScanner]]] = {
        Services.discord: DiscordScanner,
        Services.pypi: PyPiScanner,
        Services.github: GitHubScanner,
    }

    @classmethod
    def scan_file(
        cls,
        file: str,
        /,
        *,
        allowed: list[Services] = [],
        disallowed: list[Services] = [],
    ) -> list[ScannerSecret]:
        """Scan for tokens in a given files content.

        You may pass a list of allowed or disallowed Services.
        If both lists are empty (Default) all available services will be scanned.
        """
        allowed = allowed if allowed else list(Services)
        services: list[Services] = [s for s in allowed if s not in disallowed]
        secrets: list[ScannerSecret] = []

        for service in services:
            scanner: type[BaseScanner] | None = cls.__SERVICE_MAPPING.get(service, None)
            if not scanner:
                logging.warning("The provided service %r is not a supported or a valid service.", service)
                continue

            found: ScannerSecret = scanner.match(file)
            if found["tokens"]:
                secrets.append(found)

        return secrets
