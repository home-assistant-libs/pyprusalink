from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import hashlib

from aiohttp import ClientResponse, ClientSession
from pyprusalink.types import Conflict, InvalidAuth


class ApiClient:
    def __init__(
        self, session: ClientSession, host: str, username: str, password: str
    ) -> None:
        self._session = session
        self.host = host
        self._username = username
        self._password = password
        self._lock = asyncio.Lock()

        self._realm = ""
        self._nonce = ""
        self._qop = ""

    def _generate_headers(self, method: str, path: str) -> dict:
        """Generates new Authorization with the current _nonce, method and path."""
        ha1 = hashlib.md5(
            f"{self._username}:{self._realm}:{self._password}".encode()
        ).hexdigest()
        ha2 = hashlib.md5(f"{method}:{path}".encode()).hexdigest()
        response_value = hashlib.md5(f"{ha1}:{self._nonce}:{ha2}".encode()).hexdigest()

        headers = {
            "Authorization": f'Digest username="{self._username}", realm="{self._realm}", '
            f'nonce="{self._nonce}", uri="{path}", response="{response_value}"'
        }

        return headers

    def _extract_digest_params(self, headers: dict[str]) -> None:
        """Extract realm, nonce key from Digest Auth header"""
        header_value = headers.get("WWW-Authenticate", "")
        if not header_value.startswith("Digest"):
            return

        header_value = header_value[len("Digest ") :]

        params = {}
        parts = header_value.split(",")
        for part in parts:
            key, value = part.strip().split("=", 1)
            params[key.strip()] = value.strip(' "')

        self._realm = params["realm"]
        self._nonce = params["nonce"]
        self._qop = params.get("qop", "auth")

    @asynccontextmanager
    async def request(
        self,
        method: str,
        path: str,
        json_data: dict | None = None,
        try_auth: bool = True,
    ) -> AsyncGenerator[ClientResponse, None]:
        """Make a request to the PrusaLink API."""
        url = f"{self.host}{path}"
        headers = self._generate_headers(method=method, path=path)
        async with self._session.request(
            method, url, json=json_data, headers=headers
        ) as response:
            if response.status == 401:
                if try_auth:
                    self._extract_digest_params(response.headers)
                    async with self.request(method, path, json_data, False) as response:
                        yield response
                        return
                else:
                    raise InvalidAuth()

            if response.status == 409:
                raise Conflict()

            response.raise_for_status()
            yield response
