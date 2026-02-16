# core/intelligence.py

from config import AGGRESSIVE_MODE

EXTENSION_GROUPS = {
    "code": ["py", "js", "ts", "go", "java", "php", "rb", "cs", "cpp", "rs"],
    "config": ["json", "yaml", "yml", "env", "ini", "xml", "conf", "toml", "properties"],
    "text": ["txt", "md", "csv", "log", "sql"]
}

SIZE_RANGES = [
    "<1000",          # < 1KB 
    "1000..10000",    # 1KB - 10KB 
    "10000..50000",   # 10KB - 50KB 
    ">50000"          # > 50KB 
]

def generate_smart_queries(base_query: str) -> list[str]:
    """
    Принимает базовый запрос (например 'filename:.env') и возвращает список
    уточненных запросов, чтобы обойти лимит в 1000 результатов.
    """
    refined_queries = []

    for size in SIZE_RANGES:
        refined_queries.append(f"{base_query} size:{size}")

        deep_queries = []
        all_exts = EXTENSION_GROUPS["code"] + EXTENSION_GROUPS["config"] + EXTENSION_GROUPS["text"]
        
        for ext in all_exts:
            for size in SIZE_RANGES:
                deep_queries.append(f"{base_query} extension:{ext} size:{size}")
        
        return deep_queries

    return refined_queries
