import aiohttp
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from .const import API_URL, DEFAULT_HEADERS

_LOGGER = logging.getLogger(__name__)


class Track17Api:
    """Small wrapper around 17TRACK HTTP API used by the coordinator.

    The coordinator expects:
    - async_get_tracking(number) -> dict (may contain an "error" key)
    - fetch_single(number) -> { number: dict }
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            headers = DEFAULT_HEADERS.copy()
            # If an API key is provided, send it as a Bearer token. This keeps
            # headers configurable but ensures the coordinator-provided key is used.
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def async_get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        """Fetch tracking info for a single package.

        Returns a dict representing the API response. On error the dict
        should contain an "error" key so the coordinator can detect failures.
        """
        url = f"{API_URL}trackings"
        payload = {"tracking_number": tracking_number}

        session = await self._get_session()
        try:
            # Use a ClientTimeout for compatibility and clarity
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.post(url, json=payload, timeout=timeout) as resp:
                text = await resp.text()
                # Try to parse JSON; if parsing fails return an error dict
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    _LOGGER.error("Invalid JSON from 17TRACK for %s: %s", tracking_number, text[:200])
                    return {"error": f"Invalid JSON response"}

                if not isinstance(data, dict):
                    _LOGGER.error("Unexpected data type from 17TRACK for %s: %s", tracking_number, type(data))
                    return {"error": "Unexpected data format"}

                # If the upstream API encloses an error field, propagate it
                if "error" in data:
                    return {"error": data.get("error")}

                return data

        except asyncio.TimeoutError:
            _LOGGER.warning("17TRACK request timed out for %s", tracking_number)
            return {"error": "API request timed out"}
        except aiohttp.ClientError as e:
            _LOGGER.exception("HTTP error while fetching %s: %s", tracking_number, e)
            return {"error": f"HTTP error: {e}"}

    async def fetch_single(self, tracking_number: str) -> Dict[str, Any]:
        """Fetch a single package and return a mapping suitable for
        coordinator.data.update(...) which expects { number: data }.
        """
        data = await self.async_get_tracking(tracking_number)
        # If async_get_tracking returned an error payload, keep that shape
        # so the coordinator can log/handle it. Wrap under the tracking number.
        return {tracking_number: data}

    async def async_close(self) -> None:
        """Close the aiohttp session if open."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
