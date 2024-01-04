from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import hashlib

from httpx import AsyncClient, DigestAuth, Response, Request
from httpx._auth import _DigestAuthChallenge
from pyprusalink.types import Conflict, InvalidAuth, NotFound

# TODO remove after the following issues are fixed (in all supported firmwares for the latter one):
# https://github.com/encode/httpx/pull/3045
# https://github.com/prusa3d/Prusa-Firmware-Buddy/pull/3665
class DigestAuthWorkaround(DigestAuth):
    # Taken from httpx.DigestAuth and modified
    # https://github.com/encode/httpx/blob/c6907c22034e2739c4c1af89908e3c9f90602788/httpx/_auth.py#L258
    def _build_auth_header(
        self, request: Request, challenge: "_DigestAuthChallenge"
    ) -> str:
        if challenge.qop is not None:
            return super()._build_auth_header(request, challenge)

        def digest(data: bytes) -> bytes:
            return hashlib.md5(data).hexdigest().encode()

        A1 = b":".join((self._username, challenge.realm, self._password))
        HA1 = digest(A1)

        path = request.url.raw_path
        A2 = b":".join((request.method.encode(), path))
        HA2 = digest(A2)

        digest_data = [HA1, challenge.nonce, HA2]

        format_args = {
            "username": self._username,
            "realm": challenge.realm,
            "nonce": challenge.nonce,
            "uri": path,
            "response": digest(b":".join(digest_data)),
            # Omitting algorithm as a work around for https://github.com/prusa3d/Prusa-Firmware-Buddy/pull/3665
        }

        return "Digest " + self._get_header_value(format_args)

class ApiClient:
    def __init__(
        self, async_client: AsyncClient, host: str, username: str, password: str
    ) -> None:
        self._async_client = async_client
        self.host = host
        self._auth = DigestAuthWorkaround(username=username, password=password)

    @asynccontextmanager
    async def request(
        self,
        method: str,
        path: str,
        json_data: dict | None = None,
        try_auth: bool = True,
    ) -> AsyncGenerator[Response, None]:
        """Make a request to the PrusaLink API."""
        url = f"{self.host}{path}"

        response = await self._async_client.request(
            method, url, json=json_data, auth=self._auth
        )

        if response.status_code == 401:
            raise InvalidAuth()

        if response.status_code == 409:
            raise Conflict()

        if response.status_code == 404:
            raise NotFound()

        response.raise_for_status()
        yield response
