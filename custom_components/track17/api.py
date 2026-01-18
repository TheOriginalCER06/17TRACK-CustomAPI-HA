import aiohttp
import asyncio
import json
from .const import API_URL, DEFAULT_HEADERS

class Track17Api:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None

    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def async_get_tracking(self, tracking_number: str) -> dict:
        """Fetch tracking info for a single package safely."""
        url = f"{API_URL}/trackings"
        payload = {
            "tracking_number": tracking_number
        }

        session = await self._get_session()
        try:
            async with session.post(url, headers=DEFAULT_HEADERS, json=payload, timeout=10) as resp:
                text = await resp.text()

                # Attempt to parse JSON safely
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    # Log and return a structured error
                    return {
                        "tracking_number": tracking_number,
                        "error": f"Invalid JSON response from API: {text[:100]}..."
                    }

                # Ensure it is a dictionary
                if not isinstance(data, dict):
                    return {
                        "tracking_number": tracking_number,
                        "error": f"Unexpected data format: {data}"
                    }

                # Check for error returned by API
                if "error" in data:
                    return {
                        "tracking_number": tracking_number,
                        "error": data["error"]
                    }

                return data

        except asyncio.TimeoutError:
            return {
                "tracking_number": tracking_number,
                "error": "API request timed out"
            }
        except aiohttp.ClientError as e:
            return {
                "tracking_number": tracking_number,
                "error": f"HTTP error: {str(e)}"
            }

    async def async_close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
