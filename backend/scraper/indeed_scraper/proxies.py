"""
Webshare rotating proxy integration
Each request gets a random IP address
"""
import random
import os
import json

def get_proxy():
    """Get random proxy from environment variables - returns (server, username, password)"""
    # Get proxy configuration from environment variables
    proxy_str = os.environ.get('PROXY_STR')
    proxy_username = os.environ.get('PROXY_USERNAME')
    proxy_password = os.environ.get('PROXY_PASSWORD')

    print(f"DEBUG PROXY_STR raw value: {repr(proxy_str)}")

    if not proxy_str or not proxy_username or not proxy_password:
        raise ValueError("Missing proxy environment variables: PROXY_STR, PROXY_USERNAME, PROXY_PASSWORD")

    # Parse JSON array of proxies
    proxy_list = json.loads(proxy_str)

    # Return random proxy with credentials
    return (random.choice(proxy_list), proxy_username, proxy_password)
