"""
This isn't really used anymore and could probably be removed, because tls_client rarely gets blocked by cloudflare.
In the case of a cloudflare block when requesting token provider, we will just retrieve to tokens and cookies
using undetected_chromedriver / selenium.
"""
import json
import time
import logging
import requests

import undetected_chromedriver as webdriver

from selenium.webdriver.common.by import By
from requests.cookies import RequestsCookieJar, create_cookie

from .constants import KickChromedriverException

logger = logging.getLogger(__name__)


def get_cookies_and_tokens_via_selenium() -> tuple[dict, RequestsCookieJar]:
    driver = webdriver.Chrome(headless=True)
    logger.info("Fetching kick.com...")
    driver.get("https://kick.com/")
    logger.info("Fetching kick-token-provider...")
    driver.get("https://kick.com/kick-token-provider")
    time.sleep(3)
    body_element = driver.find_element(By.TAG_NAME, "body")
    logger.info("Parsing body and cookies...")
    body_text = body_element.text
    cookies = driver.get_cookies()
    driver.close()
    driver.quit()
    request_cookies = _cookie_jar_from_selenium(cookies)
    try:
        request_data = json.loads(body_text)
        return request_data, request_cookies
    except json.JSONDecodeError:
        raise KickChromedriverException("Error parsing response data/tokens from kick-token-provider")


def _cookie_jar_from_selenium(cookies) -> RequestsCookieJar:
    request_cookies = requests.cookies.RequestsCookieJar()
    for item in cookies:
        cookie_dict = {
            'name': item['name'],
            'value': item['value'],
            'domain': item['domain'],
            'path': item['path'],
            'expires': item['expiry'],
            'secure': item['secure']
        }
        new_cookie = create_cookie(**cookie_dict)
        request_cookies.set_cookie(new_cookie)
    return request_cookies


if __name__ == '__main__':
    response, cookie = get_cookies_and_tokens_via_selenium()
    breakpoint()

