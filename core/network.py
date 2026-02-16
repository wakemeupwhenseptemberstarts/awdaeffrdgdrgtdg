# core/network.py

import requests
import random
import time
import urllib3
from config import (
    PROXY_FILE, 
    TIMEOUT, 
    RETRIES, 
    USER_AGENTS, 
    TAG_ERROR, 
    TAG_WARN
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_proxies():
    try:
        with open(PROXY_FILE, 'r', encoding='utf-8') as f:
            proxies = [line.strip() for line in f if line.strip()]
        if not proxies:
            print(f"{TAG_ERROR} Proxy file {PROXY_FILE} is empty!")
            return []
        return proxies
    except FileNotFoundError:
        print(f"{TAG_ERROR} Proxy file {PROXY_FILE} not found!")
        return []

PROXY_LIST = load_proxies()

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'application/vnd.github.v3+json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

def format_proxy(proxy_str):
    # Очищаем от лишнего мусора, если он есть
    proxy_str = proxy_str.replace("https://", "").replace("http://", "").replace("/", "")
    
    parts = proxy_str.split(':')
    if len(parts) == 4:
        ip, port, user, pw = parts
        if not ip[0].isdigit():
            user, pw, ip, port = parts
        formatted = f"http://{user}:{pw}@{ip}:{port}"
    else:
        formatted = f"http://{proxy_str}"
        
    return {"http": formatted, "https": formatted}

def make_request(url, params=None, method="GET", json_data=None, headers_extra=None):
    if not PROXY_LIST:
        return None

    for attempt in range(RETRIES):
        current_proxy = random.choice(PROXY_LIST)
        proxies = format_proxy(current_proxy)
        headers = get_random_headers()
        
        if headers_extra:
            headers.update(headers_extra)

        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=TIMEOUT, verify=False)
            elif method == "POST":
                response = requests.post(url, json=json_data, headers=headers, proxies=proxies, timeout=TIMEOUT, verify=False)
            
            if response.status_code in [429, 403]:
                if "api.github.com" not in url:
                    raise requests.exceptions.RequestException(f"Banned/Captcha ({response.status_code})")
            
            return response

        except requests.exceptions.RequestException as e:
            if attempt == RETRIES - 1:
                print(f"\n{TAG_ERROR} Proxy Drop: {proxies['http']} -> {type(e).__name__}")
            time.sleep(random.uniform(0.5, 1.5))

    return None
