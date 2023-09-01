import cloudscraper
import requests

from requests.cookies import RequestsCookieJar
from .selenium_help import get_cookies_and_tokens_via_selenium


class AuthException(Exception):
    ...


class KickClient:
    def __init__(self, username: str, password: str) -> None:
        self.username: str = username
        self.password: str = password
        self.scraper = cloudscraper.create_scraper()
        self.xsrf: str | None = None
        self.cookies: RequestsCookieJar | None = None
        self.auth_token: str | None = None
        self.user_data: dict[str, str | dict] | None = None
        self.user_id: int | None = None
        self._login()

    def _login(self) -> None:
        print("Logging user-bot in...")
        try:
            r = self._request_token_provider()
            token_data = r.json()
            self.cookies = r.cookies
            self.xsrf = r.cookies['XSRF-TOKEN']

        except (requests.exceptions.HTTPError, requests.exceptions.JSONDecodeError):
            print("Cloudflare Block. Taking the harder way 😈 (headless selenium)...")
            token_data, cookies = get_cookies_and_tokens_via_selenium()
            print("Done retrieving data via selenium")
            self.cookies = cookies
            self.xsrf = cookies['XSRF-TOKEN']

        name_field_name = token_data.get('nameFieldName')
        token_field = token_data.get('validFromFieldName')
        login_token = token_data.get('encryptedValidFrom')
        if any(value is None for value in [name_field_name, token_field, login_token]):
            raise AuthException("Error when parsing token fields while attempting login.")

        print("Tokens parsed. Sending login post...")
        r2 = self._send_login_request(name_field_name, token_field, login_token)
        login_data = r2.json()
        login_status = r2.status_code
        match login_status:
            case 200:
                self.auth_token = login_data.get('token')
                twofactor = login_data.get('2fa_required')
                if twofactor:
                    raise AuthException("Must disable 2-factor authentication on the bot account.")
            case 422:
                raise AuthException("Login Failed:", login_data)
            case 419:
                raise AuthException("Csrf Error:", login_data)
            case 403:
                raise AuthException("Cloudflare blocked (gay). Might need to set a proxy. Response:", login_data)
            case _:
                raise AuthException(f"Unexpected Response. Status Code: {login_status} | Response: {login_data}")
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
        self.cookies['XSRF-TOKEN'] = self.xsrf
        rs = self._make_get_request(url, cookies=self.cookies, headers=headers)
        if rs.status_code != 200:
            raise AuthException("Error fetching user info.")
        data = rs.json()
        self.user_data = data
        self.user_id = data.get('id')

    def get_socket_auth_token(self, socket_id: str) -> str:
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
            'channel_name': f'private-userfeed.{self.user_id}',
        }
        r = self._make_post_request(url, payload=payload, cookies=self.cookies, headers=headers)
        if r.status_code != 200:
            raise AuthException("Error retrieving socket auth token.")
        socket_auth_token = r.json().get('auth')
        return socket_auth_token

    def _request_token_provider(self) -> requests.Response:
        base = self._make_get_request('https://kick.com/')
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
        return self._make_get_request(url, cookies=base.cookies, headers=headers)

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
        return self._make_post_request(url, payload=payload, cookies=self.cookies, headers=headers)

    def _make_get_request(self,
                          url,
                          cookies: RequestsCookieJar = None,
                          headers: dict[str, str] = None) -> requests.Response:
        r = self.scraper.get(url, cookies=cookies, headers=headers)
        return r

    def _make_post_request(self,
                           url,
                           payload: dict[str, str],
                           cookies: RequestsCookieJar = None,
                           headers: dict[str, str] = None) -> requests.Response:
        r = self.scraper.post(url, json=payload, cookies=cookies, headers=headers)
        return r
