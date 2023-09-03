import requests
import logging
import tls_client

from requests.cookies import RequestsCookieJar

from .constants import BASE_HEADERS, KickAuthException
from .selenium_help import get_cookies_and_tokens_via_selenium

logger = logging.getLogger(__name__)


class KickClient:
    """
    Class mainly for authenticating user, and handling http requests using tls_client to bypass cloudflare
    """
    def __init__(self, username: str, password: str) -> None:
        self.username: str = username
        self.password: str = password
        self.scraper = tls_client.Session(
            client_identifier="chrome116",
            random_tls_extension_order=True
        )
        self.xsrf: str | None = None
        self.cookies: RequestsCookieJar | None = None
        self.auth_token: str | None = None
        self.user_data: dict[str, str | dict] | None = None
        self.user_id: int | None = None
        self._login()

    def _login(self) -> None:
        """
        Main function to authenticate the user bot.

        Attempts to retrieve tokens and cookies from /kick-token-provider with self.scraper (tls-client),
        but will user undetected_chromedriver in the case of it failing cloudflare (it normally doesn't).

        In the case on it failing cloudflare, it will parse the tokens and cookies via chromedriver,
        then send the login post with the scraper over http with self.scraper (tls_client).
        The cf_clearence cookie from chromedriver will bypass cloudflare blocking again.
        """
        logger.info("Logging user-bot in...")
        try:
            initial_token_response = self._request_token_provider()
            token_data = initial_token_response.json()
            self.cookies = initial_token_response.cookies
            self.xsrf = initial_token_response.cookies['XSRF-TOKEN']

        except (requests.exceptions.HTTPError, requests.exceptions.JSONDecodeError):
            logger.info("Cloudflare Block. Getting tokens and cookies with chromedriver...")
            token_data, cookies = get_cookies_and_tokens_via_selenium()
            logger.info("Done retrieving data via selenium")
            self.cookies = cookies
            self.xsrf = cookies['XSRF-TOKEN']

        name_field_name = token_data.get('nameFieldName')
        token_field = token_data.get('validFromFieldName')
        login_token = token_data.get('encryptedValidFrom')
        if any(value is None for value in [name_field_name, token_field, login_token]):
            raise KickAuthException("Error when parsing token fields while attempting login.")

        login_response = self._send_login_request(name_field_name, token_field, login_token)
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
        logger.info("Login Successful...")
        self._get_user_info()

    def _get_user_info(self) -> None:
        """
        Retrieve user info after authenticating.
        Sets self.user_data and self.user_id (data of the user bot)
        """
        url = 'https://kick.com/api/v1/user'
        headers = BASE_HEADERS.copy()
        headers['Authorization'] = "Bearer " + self.auth_token
        headers['X-Xsrf-Token'] = self.xsrf
        user_info_response = self.scraper.get(url, cookies=self.cookies, headers=headers)
        if user_info_response.status_code != 200:
            raise KickAuthException(f"Error fetching user info from {url}")
        data = user_info_response.json()
        self.user_data = data
        self.user_id = data.get('id')

    def _request_token_provider(self) -> requests.Response:
        """
         Request the token provider to retrieve some useful tokens, and cookies

         :return: Response from the token provider request using the scraper (tls-client)
         """
        url = "https://kick.com/kick-token-provider"
        headers = BASE_HEADERS.copy()
        headers['Referer'] = "https://kick.com"
        headers['path'] = "/kick-token-provider"
        return self.scraper.get(url, cookies=self.cookies, headers=headers)

    def _send_login_request(self, name_field_name: str, token_field: str, login_token: str) -> requests.Response:
        """
        Perform the login post request to the mobile login endpoint. On desktop, I get 2fa more, and a csrf error (419).

        :param name_field_name: Token field received from _request_token_provider
        :param token_field: Token field received from _request_token_provider
        :param login_token: Token field received from _request_token_provider
        :return: Login post request response
        """
        url = 'https://kick.com/mobile/login'
        headers = BASE_HEADERS.copy()
        headers['X-Xsrf-Token'] = self.xsrf
        payload = {
            name_field_name: '',
            token_field: login_token,
            "email": self.username,
            "isMobileRequest": True,
            "password": self.password,
        }
        return self.scraper.post(url, json=payload, cookies=self.cookies, headers=headers)
