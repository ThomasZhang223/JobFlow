import requests
proxy = requests.get(
    "https://ipv4.webshare.io/",
    proxies={
        "http": "http://uyddgisl:xp94bd2fpxkp@142.111.48.253:7030/",
        "https": "http://uyddgisl:xp94bd2fpxkp@142.111.48.253:7030/"
    }
).text

print(proxy)