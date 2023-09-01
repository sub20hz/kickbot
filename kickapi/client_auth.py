import cloudscraper
import requests

from requests.cookies import RequestsCookieJar


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
        r = self._request_token_provider()
        token_data = r.json()
        self.cookies = r.cookies
        self.xsrf = r.cookies['XSRF-TOKEN']
        name_field_name = token_data.get('nameFieldName')
        token_field = token_data.get('validFromFieldName')
        login_token = token_data.get('encryptedValidFrom')
        if name_field_name is None or token_field is None or login_token is None:
            raise AuthException("Error when parsing token fields while attempting login.")

        r2 = self._send_login_request(name_field_name, token_field, login_token)
        self.cookies = r2.cookies
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
                raise AuthException("Cloudflare blocked (gay). Might need to set a proxy.")
            case _:
                raise AuthException(f"Unexpected Response. Status Code: {r2.status_code} | Response: {r2.json()}")
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
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0_3 like Mac OS X) '
                          'AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
        }
        self.cookies['XSRF-TOKEN'] = self.xsrf
        r = self._make_get_request(url, cookies=self.cookies, headers=headers)
        if r.status_code != 200:
            raise AuthException("Error fetching user info.")
        data = r.json()
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
            "User-Agent": 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0_3 like Mac OS X) '
                          'AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
        }
        payload = {
            'socket_id': socket_id,
            'channel_name': f'private-userfeed.{self.user_id}',
        }
        r1 = self._make_post_request(url, payload=payload, cookies=self.cookies, headers=headers)
        r1.raise_for_status()
        socket_auth_token = r1.json().get('auth')
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
            "User-Agent": 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0_3 like Mac OS X) '
                          'AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',

        }
        return self._make_get_request(url, cookies=self.cookies, headers=headers)

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
            "User-Agent": 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0_3 like Mac OS X) '
                          'AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
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
