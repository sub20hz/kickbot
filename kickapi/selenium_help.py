import json
import time
import requests

import undetected_chromedriver as webdriver
from selenium.webdriver.common.by import By

from requests.cookies import RequestsCookieJar, create_cookie


def get_cookies_and_tokens_via_selenium() -> tuple[dict, RequestsCookieJar]:
    driver = webdriver.Chrome(headless=True)
    print("Fetching kick.com...")
    driver.get("https://kick.com/")
    print("Fetching kick-token-provider...")
    driver.get("https://kick.com/kick-token-provider")
    time.sleep(3)
    body_element = driver.find_element(By.TAG_NAME, "body")
    print("Parsing body and cookies...")
    body_text = body_element.text
    cookies = driver.get_cookies()
    driver.quit()
    request_cookies = _cookie_jar_from_selenium(cookies)
    try:
        request_data = json.loads(body_text)
        return request_data, request_cookies
    except Exception as e:
        raise e


def _cookie_jar_from_selenium(cookies) -> RequestsCookieJar:
    request_cookies = requests.cookies.RequestsCookieJar()
    for cookie in cookies:
        cookie_dict = {
            'name': cookie['name'],
            'value': cookie['value'],
            'domain': cookie['domain'],
            'path': cookie['path'],
            'expires': cookie['expiry'],
            'secure': cookie['secure']
        }
        new_cookie = create_cookie(**cookie_dict)
        request_cookies.set_cookie(new_cookie)
    return request_cookies


if __name__ == '__main__':
    response, cookie = get_cookies_and_tokens_via_selenium()
    breakpoint()

