import cloudscraper
import requests
import tls_client

from requests.cookies import RequestsCookieJar
from .selenium_help import get_cookies_and_tokens_via_selenium


class KickAuthException(Exception):
    ...


class KickClient:
    def __init__(self, username: str, password: str) -> None:
        self.username: str = username
        self.password: str = password
        self.scraper = tls_client.Session(
            client_identifier="chrome116",
            random_tls_extension_order=True
        )
        # self.scraper = cloudscraper.create_scraper()
        self.xsrf: str | None = None
        self.cookies: RequestsCookieJar | None = None
        self.auth_token: str | None = None
        self.user_data: dict[str, str | dict] | None = None
        self.user_id: int | None = None
        self._login()

    def _login(self) -> None:
        print("Logging user-bot in...")
        try:
            initial_token_response = self._request_token_provider()
            token_data = initial_token_response.json()
            self.cookies = initial_token_response.cookies
            self.xsrf = initial_token_response.cookies['XSRF-TOKEN']

        except (requests.exceptions.HTTPError, requests.exceptions.JSONDecodeError):
            print("Cloudflare Block. Getting tokens and cookies with chromedriver...")
            token_data, cookies = get_cookies_and_tokens_via_selenium()
            print("Done retrieving data via selenium")
            self.cookies = cookies
            self.xsrf = cookies['XSRF-TOKEN']

        name_field_name = token_data.get('nameFieldName')
        token_field = token_data.get('validFromFieldName')
        login_token = token_data.get('encryptedValidFrom')
        if any(value is None for value in [name_field_name, token_field, login_token]):
            raise KickAuthException("Error when parsing token fields while attempting login.")

        print("Tokens parsed. Sending login post...")
        login_response = self._send_login_request(name_field_name, token_field, login_token)
        breakpoint()
        login_data = login_response.json()
        login_status = login_response.status_code
        match login_status:
            case 200:
                self.auth_token = login_data.get('token')
                twofactor = login_data.get('2fa_required')
                if twofactor:
                    raise KickAuthException("Must disable 2-factor authentication on the bot account.")
            case 422:
                raise KickAuthException("Login Failed:", login_data)
            case 419:
                raise KickAuthException("Csrf Error:", login_data)
            case 403:
                raise KickAuthException("Cloudflare blocked (gay). Might need to set a proxy. Response:", login_data)
            case _:
                raise KickAuthException(f"Unexpected Response. Status Code: {login_status} | Response: {login_data}")
        print("Login Successful...")
        self._get_user_info()

    def _get_user_info(self) -> None:
        url = 'https://kick.com/api/v1/user'
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Authorization": "Bearer " + self.auth_token,
            "X-Xsrf-Token": self.xsrf,
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",

        }
        user_info_response = self.scraper.get(url, cookies=self.cookies, headers=headers)
        breakpoint()
        if user_info_response.status_code != 200:
            raise KickAuthException(f"Error fetching user info from {url}")
        data = user_info_response.json()
        self.user_data = data
        self.user_id = data.get('id')

    def get_socket_auth_token(self, socket_id: str, channel_name: str) -> str:
        url = 'https://kick.com/broadcasting/auth'
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Authorization": "Bearer " + self.auth_token,
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        }
        payload = {
            'socket_id': socket_id,
            'channel_name': channel_name,
        }
        auth_token_response = self.scraper.post(url, json=payload, cookies=self.cookies, headers=headers)
        breakpoint()
        if auth_token_response.status_code != 200:
            raise KickAuthException(f"Error retrieving socket auth token from {url}")
        socket_auth_token = auth_token_response.json().get('auth')
        cookie_refresh = self._request_token_provider()
        breakpoint()
        self.cookies = cookie_refresh.cookies
        return socket_auth_token

    def _request_token_provider(self) -> requests.Response:
        url = "https://kick.com/kick-token-provider"
        headers = {
            "authority": "kick.com",
            "method": "GET",
            "path": "/kick-token-provider",
            "scheme": "https",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://kick.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",

        }
        cookies = self.cookies if self.cookies is not None else None
        return self.scraper.get(url, cookies=cookies, headers=headers)

    def _send_login_request(self, name_field_name: str, token_field: str, login_token: str) -> requests.Response:
        url = 'https://kick.com/mobile/login'
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "X-Xsrf-Token": self.xsrf,
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        }
        payload = {
            name_field_name: '',
            token_field: login_token,
            "email": self.username,
            "isMobileRequest": True,
            "password": self.password,
        }
        return self.scraper.post(url, json=payload, cookies=self.cookies, headers=headers)
