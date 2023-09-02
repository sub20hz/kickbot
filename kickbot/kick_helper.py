import json

from .kick_client import KickClient


class KickHelperException(Exception):
    ...


class KickHelper:
    @staticmethod
    def get_streamer_info(client: KickClient, streamer_name: str) -> dict:
        if not client.xsrf:
            raise KickHelperException("No xsrf token is set in the client. This token is required.")

        url = f"https://kick.com/api/v1/channels/{streamer_name}"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Xsrf-Token": client.xsrf,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        }
        response = client.scraper.get(url, cookies=client.cookies, headers=headers)
        if response.status_code == 403:
            raise KickHelperException("Error retrieving streamer info. Blocked By cloudflare.")
        try:
            return response.json()
        except json.JSONDecodeError:
            raise KickHelperException("Error parsing streamer info json from response.")
