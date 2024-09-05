# api id, hash
API_ID = 1488
API_HASH = 'abcde1488'

DELAYS = {
    "RELOGIN": [5, 7],  # delay after a login attempt
    'ACCOUNT': [5, 15],  # delay between connections to accounts (the more accounts, the longer the delay)
    'CLAIM': [10, 20],   # delay between pour beers
    'TASK': [2, 5],  # delay after complete task
    'REPEAT': [2, 5]  # delay after complete while
}

PROXY = {
    "USE_PROXY_FROM_FILE": False,  # True - if use proxy from file, False - if use proxy from accounts.json
    "PROXY_PATH": "data/proxy.txt",  # path to file proxy
    "TYPE": {
        "TG": "http",  # proxy type for tg client. "socks4", "socks5" and "http" are supported
        "REQUESTS": "http"  # proxy type for requests. "http" for https and http proxys, "socks5" for socks5 proxy.
        }
}

# session folder (do not change)
WORKDIR = "sessions/"

# timeout in seconds for checking accounts on valid
TIMEOUT = 30

SOFT_INFO = f"""{"TON Station".center(40)}
Soft for https://t.me/tonstationgames_bot
{"Functional:".center(40)}
Register accounts in web app; start and claim farming; 

The soft also collects statistics on accounts and uses proxies from {f"the {PROXY['PROXY_PATH']} file" if PROXY['USE_PROXY_FROM_FILE'] else "the accounts.json file"}
To buy this soft with the option to set your referral link write me: https://t.me/Axcent_ape
"""