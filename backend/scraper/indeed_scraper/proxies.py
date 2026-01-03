"""
HTTP Proxy rotation for anti-bot measures
Loads proxies from http.txt file
"""

import os
import random

def load_proxies_from_file():
    """Load proxies from http.txt file"""
    proxies = []
    proxy_file = os.path.join(os.path.dirname(__file__), 'http.txt')

    try:
        with open(proxy_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Add http:// prefix if not present
                    if not line.startswith(('http://', 'https://')):
                        line = 'http://' + line
                    proxies.append(line)
    except FileNotFoundError:
        print(f"Proxy file {proxy_file} not found. Create http.txt with proxy list.")
    except Exception as e:
        print(f"Error loading proxies: {e}")

    return proxies

# Load proxies on import
HTTP_PROXIES = load_proxies_from_file()

def get_random_proxy():
    """Get a random proxy from the list"""
    if not HTTP_PROXIES:
        return None
    return random.choice(HTTP_PROXIES)

def is_proxy_enabled():
    """Check if proxy rotation is enabled (has proxies configured)"""
    return len(HTTP_PROXIES) > 0

# Proxy rotation settings
PROXY_SETTINGS = {
    'enabled': is_proxy_enabled(),
    'max_retries': 3,  # Retry failed requests up to 3 times with different proxies
    'failure_threshold': 5,  # Remove proxy from rotation after 5 consecutive failures
}