from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from httpx import AsyncClient, DigestAuth, Response
from pyprusalink.types import Conflict, InvalidAuth, NotFound


class ApiClient:
    def __init__(
        self, async_client: AsyncClient, host: str, username: str, password: str
    ) -> None:
        self._async_client = async_client
        self.host = host
        self._auth = DigestAuth(username=username, password=password)

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
