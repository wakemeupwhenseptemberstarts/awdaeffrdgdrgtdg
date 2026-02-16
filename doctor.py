import time
import os
import requests
from config import (
    GITHUB_TOKENS,
    GITLAB_TOKENS,
    PROXY_FILE,
    TAG_INFO,
    TAG_ERROR,
    TAG_WARN,
    TAG_FOUND
)
from core.network import make_request

def check_files():
    print(f"{TAG_INFO} Checking file system...")
    if not os.path.exists(PROXY_FILE):
        print(f"{TAG_ERROR} Proxy file '{PROXY_FILE}' NOT FOUND!")
        return False
    
    with open(PROXY_FILE, 'r', encoding='utf-8') as f:
        proxies = [l.strip() for l in f if l.strip()]
    
    if not proxies:
        print(f"{TAG_ERROR} Proxy file is EMPTY!")
        return False
        
    print(f"{TAG_FOUND} Proxies loaded: {len(proxies)}")
    
    if not os.path.exists("core/__init__.py"):
        print(f"{TAG_WARN} Missing 'core/__init__.py'. Script might fail!")
    else:
        print(f"{TAG_FOUND} Core structure seems OK.")
    
    return True

def check_github_token(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    url = "https://api.github.com/rate_limit"
    response = make_request(url, headers_extra=headers)
    
    mask_token = token[:6] + "..." + token[-4:]
    
    if response and response.status_code == 200:
        data = response.json()
        core_limit = data.get("resources", {}).get("core", {})
        remaining = core_limit.get("remaining", 0)
        reset_time = core_limit.get("reset", 0)
        print(f"{TAG_FOUND} GitHub Token {mask_token} | Valid | Limit: {remaining}")
    elif response and response.status_code == 401:
        print(f"{TAG_ERROR} GitHub Token {mask_token} | INVALID (401)")
    else:
        status = response.status_code if response else "Connection Error"
        print(f"{TAG_WARN} GitHub Token {mask_token} | Network Error ({status})")

def check_gitlab_token(token):
    headers = {"PRIVATE-TOKEN": token}
    url = "https://gitlab.com/api/v4/user"
    response = make_request(url, headers_extra=headers)
    
    mask_token = token[:6] + "..." + token[-4:]
    
    if response and response.status_code == 200:
        user = response.json().get("username", "Unknown")
        print(f"{TAG_FOUND} GitLab Token {mask_token} | Valid | User: {user}")
    elif response and response.status_code == 401:
        print(f"{TAG_ERROR} GitLab Token {mask_token} | INVALID (401)")
    else:
        status = response.status_code if response else "Connection Error"
        print(f"{TAG_WARN} GitLab Token {mask_token} | Network Error ({status})")

def main():
    print("==========================================")
    print("   DOCTOR.PY")
    print("==========================================\n")

    if not check_files():
        print(f"\n{TAG_ERROR} Critical file check failed. Exiting.")
        return

    print(f"\n{TAG_INFO} Testing Network & Tokens (via Proxies)...")
    
    print("\n--- GitHub Tokens ---")
    if GITHUB_TOKENS:
        for token in GITHUB_TOKENS:
            check_github_token(token)
    else:
        print(f"{TAG_WARN} No GitHub tokens in config.")

    print("\n--- GitLab Tokens ---")
    if GITLAB_TOKENS:
        for token in GITLAB_TOKENS:
            check_gitlab_token(token)
    else:
        print(f"{TAG_INFO} No GitLab tokens in config.")

    print("\n==========================================")
    print("   COMPLETE")
    print("==========================================")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
