import aiohttp

API_URL = "https://api.17track.net/track/v2.4/gettrackinfo"

class Track17Api:
    def __init__(self, api_key):
        self._api_key = api_key

    async def fetch(self, numbers):
        if not numbers:
            return {}

        headers = {
            "17token": self._api_key,
            "Content-Type": "application/json",
        }

        payload = {"number": numbers}

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()

        return {item["number"]: item for item in data.get("data", [])}

    async def fetch_single(self, number):
        return await self.fetch([number])
