BASE_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
}


class KickBotException(Exception):
    ...


class KickAuthException(Exception):
    ...


class KickHelperException(Exception):
    ...


class KickChromedriverException(Exception):
    ...

