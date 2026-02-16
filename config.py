# config.py

TAG_ERROR = "❌ [ERROR]"
TAG_FOUND = "🔵 [KEY_FOUND]"
TAG_INFO  = "ℹ️ [INFO]"
TAG_WARN  = "⚠️ [WARN]"

PROXY_FILE = "proxies.txt"
OUTPUT_FILE = "raw_keys_found.txt"

GITHUB_TOKENS = [
    "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",
    "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",
    "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",
    "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",
]

GITLAB_TOKENS = [
    "glpat-q_mb4o5ID0RHDzHpkVdJ-m86MQp1Omp1N2V2Cw.01.120btjek9", 
]

HUGGINGFACE_TOKEN = "" 

THREADS = 20         
TIMEOUT = 5         # Таймаут
RETRIES = 1          # Ретраи если будут ошибки с сетью

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
]

USE_SMART_SEARCH = True   # Включить дробление запросов (обход лимита 1000)
AGGRESSIVE_MODE = False   # True = дробить еще и по расширениям (x10 к количеству запросов)
RESULT_LIMIT = 1000       # Порог, после которого включается дробление

BLACKLIST_EXTENSIONS = [
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".css", 
    ".exe", ".bin", ".dll", ".so", ".zip", ".tar", ".gz", ".pdf", ".lock"
]

REGEX_MAP = {
    "OPENAI": r"(sk-[a-zA-Z0-9]{48})",
    "OPENAI_PROJ": r"(sk-proj-[a-zA-Z0-9\-_]{20,})",
    "ANTHROPIC": r"(sk-ant-api03-[a-zA-Z0-9\-_]{20,})",
    "GEMINI": r"(AIza[0-9A-Za-z\-_]{35})",
    "AWS_ID": r"(A[SK]IA[0-9A-Z]{16})",
    "STRIPE": r"(sk_live_[0-9a-zA-Z]{24})",
    "GOOGLE_CLOUD": r"(AIza[0-9A-Za-z\-_]{35})",
    "HUGGINGFACE": r"(hf_[a-zA-Z0-9]{34})",
}

SEARCH_QUERIES = [
    'ext:env "AIza"',
    'ext:env "sk-"',
    'ext:log "AIza"',
    'ext:yml "api_key"',
    'ext:json "google_api_key"',
    'ext:xml "aws_access_key_id"',
    'filename:.env',
    'filename:config.json',
    'filename:credentials',
    'filename:secrets.yaml',
    'auth_key',
    'access_token',
]
