import time
import re
import os
import random
import urllib3
import concurrent.futures
import datetime
from threading import Lock

from config import (
    GITHUB_TOKENS,
    GITLAB_TOKENS,
    SEARCH_QUERIES, 
    REGEX_MAP, 
    THREADS, 
    OUTPUT_FILE, 
    TAG_ERROR, 
    TAG_FOUND, 
    TAG_INFO, 
    TAG_WARN,
    USE_SMART_SEARCH,
    RESULT_LIMIT,
    BLACKLIST_EXTENSIONS
)
from core.network import make_request
from core.intelligence import generate_smart_queries

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FOUND_KEYS = set()
FILE_LOCK = Lock()

def load_existing_keys():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.split(" | ")
                if parts:
                    FOUND_KEYS.add(parts[0].strip())
    print(f"{TAG_INFO} Loaded {len(FOUND_KEYS)} existing keys into memory.")

def save_key(key_type, key_value, source_url, context=""):
    with FILE_LOCK:
        if key_value in FOUND_KEYS:
            return
        
        FOUND_KEYS.add(key_value)
        
        log_entry = f"{key_value} | Type: {key_type} | URL: {source_url}"
        if context:
            log_entry += f" | Context: {context}"

        with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")
            
        print(f"{TAG_FOUND} [{key_type}] found in {source_url}")

def scan_content(text, source_url):
    if not text:
        return

    for key_type, pattern in REGEX_MAP.items():
        for match in re.finditer(pattern, text):
            key = match.group(0)
            if key not in FOUND_KEYS:
                start = match.end()
                end = min(start + 50, len(text))
                context = text[start:end].replace("\n", " ").strip()
                save_key(key_type, key, source_url, context)

def process_item_content(url, html_url, file_name):
    if any(file_name.endswith(ext) for ext in BLACKLIST_EXTENSIONS):
        return

    response = make_request(url)
    if response and response.status_code == 200:
        try:
            content = response.text
            scan_content(content, html_url)
        except Exception:
            pass

def process_github_item(item):
    raw_url = item.get('download_url')
    html_url = item.get('html_url', 'unknown')
    file_name = item.get('name', '').lower()
    if raw_url:
        process_item_content(raw_url, html_url, file_name)

def search_github(query, token):
    base_url = "https://api.github.com/search/code"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}

    params = {"q": query, "per_page": 1}
    response = make_request(base_url, params=params, headers_extra=headers)

    if not response or response.status_code != 200:
        return

    total_count = response.json().get('total_count', 0)
    queries_to_run = [query]
    
    if USE_SMART_SEARCH and total_count > RESULT_LIMIT:
        queries_to_run = generate_smart_queries(query)

    for sub_query in queries_to_run:
        page = 1
        while page <= 10: 
            params = {"q": sub_query, "per_page": 100, "page": page}
            resp = make_request(base_url, params=params, headers_extra=headers)
            
            if not resp or resp.status_code != 200: break
            items = resp.json().get('items', [])
            if not items: break
                
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                executor.map(process_github_item, items)
            page += 1
            time.sleep(2)

def worker_github_wrapper(query):
    if not GITHUB_TOKENS: return
    token = random.choice(GITHUB_TOKENS)
    try:
        search_github(query, token)
    except Exception:
        pass

def process_gitlab_item(item, token):
    project_id = item.get('project_id')
    file_path = item.get('path')
    blob_id = item.get('id')
    
    if project_id and blob_id:
        raw_url = f"https://gitlab.com/api/v4/projects/{project_id}/repository/blobs/{blob_id}/raw"
        html_url = f"https://gitlab.com/projects/{project_id}/repository/files/{file_path}"
        
        headers = {"PRIVATE-TOKEN": token}
        response = make_request(raw_url, headers_extra=headers)
        if response and response.status_code == 200:
            scan_content(response.text, html_url)

def search_gitlab(query, token):
    base_url = "https://gitlab.com/api/v4/search"
    headers = {"PRIVATE-TOKEN": token}
    
    page = 1
    while page <= 10:
        params = {"scope": "blobs", "search": query, "per_page": 100, "page": page}
        resp = make_request(base_url, params=params, headers_extra=headers)
        
        if not resp: break
        if resp.status_code == 429:
            time.sleep(5)
            continue
        if resp.status_code != 200: break
            
        items = resp.json()
        if not items or not isinstance(items, list): break
        
        print(f"{TAG_INFO} [GitLab] Scanning {len(items)} files for query: {query[:20]}... (Page {page})")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_gitlab_item, item, token) for item in items]
            concurrent.futures.wait(futures)
            
        page += 1
        time.sleep(1)

def worker_gitlab_wrapper(query):
    if not GITLAB_TOKENS: return
    token = random.choice(GITLAB_TOKENS)
    try:
        search_gitlab(query, token)
    except Exception:
        pass

def process_gist_item(gist):
    html_url = gist.get('html_url', 'unknown')
    files = gist.get('files', {})
    for file_name, file_data in files.items():
        raw_url = file_data.get('raw_url')
        if raw_url:
            process_item_content(raw_url, html_url, file_name.lower())

def search_gists(token):
    base_url = "https://api.github.com/gists/public"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    
    page = 1
    while page <= 10:
        params = {"per_page": 100, "page": page}
        resp = make_request(base_url, params=params, headers_extra=headers)
        
        if not resp: break
        if resp.status_code == 429:
            time.sleep(5)
            continue
        if resp.status_code != 200: break
            
        items = resp.json()
        if not items or not isinstance(items, list): break
            
        print(f"{TAG_INFO} [Gist] Scanning {len(items)} fresh public gists (Page {page})")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(process_gist_item, items)
            
        page += 1
        time.sleep(2)

def worker_gist_wrapper():
    if not GITHUB_TOKENS: return
    token = random.choice(GITHUB_TOKENS)
    try:
        search_gists(token)
    except Exception:
        pass

def process_huggingface_hit(hit):
    repo_id = hit.get('repoId')
    repo_type = hit.get('repoType', 'model')
    
    if not repo_id and 'repo' in hit:
        repo_data = hit['repo']
        if isinstance(repo_data, dict):
            repo_id = repo_data.get('name') or repo_data.get('id')
            repo_type = repo_data.get('type', 'model')
        elif isinstance(repo_data, str):
            repo_id = repo_data
            
    path = hit.get('path')
    if not repo_id or not path: return
    
    if any(path.lower().endswith(ext) for ext in BLACKLIST_EXTENSIONS): return
    
    if repo_type == 'space':
        raw_url = f"https://huggingface.co/spaces/{repo_id}/raw/main/{path}"
        html_url = f"https://huggingface.co/spaces/{repo_id}/blob/main/{path}"
    elif repo_type == 'dataset':
        raw_url = f"https://huggingface.co/datasets/{repo_id}/raw/main/{path}"
        html_url = f"https://huggingface.co/datasets/{repo_id}/blob/main/{path}"
    else:
        raw_url = f"https://huggingface.co/{repo_id}/raw/main/{path}"
        html_url = f"https://huggingface.co/{repo_id}/blob/main/{path}"
        
    process_item_content(raw_url, html_url, path.lower())

def search_huggingface(query):
    base_url = "https://huggingface.co/api/search/full-text"
    params = {"q": query, "type": "file", "limit": 100}
    
    resp = make_request(base_url, params=params)
    if not resp or resp.status_code != 200: return
    
    try:
        data = resp.json()
        hits = data.get('hits', [])
    except Exception:
        return
        
    if not hits: return
    
    print(f"{TAG_INFO} [HuggingFace] Scanning {len(hits)} files for query: {query[:20]}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_huggingface_hit, hits)

def worker_huggingface_wrapper(query):
    try:
        search_huggingface(query)
    except Exception:
        pass

def main():
    print("==========================================")
    print("   GreatScrap v1.2")
    print("==========================================\n")

    load_existing_keys()

    two_months_ago = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime('%Y-%m-%d')
    print(f"{TAG_INFO} Launching scrapers... (GitHub Filter: created:>{two_months_ago})")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = []
        
        if GITHUB_TOKENS:
            futures.append(executor.submit(worker_gist_wrapper))
            for q in SEARCH_QUERIES:
                gh_query = f"{q} created:>{two_months_ago}"
                futures.append(executor.submit(worker_github_wrapper, gh_query))
                
        if GITLAB_TOKENS:
            for q in SEARCH_QUERIES:
                futures.append(executor.submit(worker_gitlab_wrapper, q))
                
        for q in SEARCH_QUERIES:
            futures.append(executor.submit(worker_huggingface_wrapper, q))
        
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception:
                pass

    print(f"\n{TAG_INFO} All missions complete.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Stopped by user.")

if __name__ == "__main__":
    import time # На случай если забыли импорт наверху
    try:
        while True:
            main()
            print(f"\n{TAG_INFO} Круг завершен. Ждем 3 минуты, пока юзеры зальют новый код...")
            time.sleep(180) # Пауза 3 минуты перед следующим сканированием
    except KeyboardInterrupt:
        print("\n[!] Stopped by user.")
