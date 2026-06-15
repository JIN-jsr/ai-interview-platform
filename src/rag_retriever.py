import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple


DEFAULT_KB_PATH = "data/knowledge_base.json"


def load_knowledge_base(path: str = DEFAULT_KB_PATH) -> List[Dict[str, Any]]:
    """Load knowledge base entries from JSON."""
    kb_path = Path(path)
    if not kb_path.exists():
        return []
    return json.loads(kb_path.read_text(encoding="utf-8"))


def normalize_text(text: str) -> str:
    return str(text or "").lower().replace("＋", "+").replace("＃", "#")


def tokenize(text: str) -> List[str]:
    """A lightweight tokenizer for mixed Chinese and English text."""
    text = normalize_text(text)
    english_tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.]*", text)
    chinese_chunks = re.findall(r"[一-鿿]{2,}", text)
    return english_tokens + chinese_chunks


def flatten_profile_keywords(profile: Dict[str, Any]) -> List[str]:
    """Collect useful keywords from profile generated after resume parsing."""
    keywords = []

    for key in ["target_role", "difficulty"]:
        value = profile.get(key)
        if value:
            keywords.append(str(value))

    for key in ["detected_skills", "project_names", "interview_focus", "possible_weaknesses"]:
        value = profile.get(key, [])
        if isinstance(value, list):
            keywords.extend(str(v) for v in value if str(v).strip())
        elif isinstance(value, str):
            keywords.append(value)

    candidate_profile = profile.get("candidate_profile", "")
    if candidate_profile:
        keywords.append(candidate_profile)

    # Add role-related expansion words
    role = str(profile.get("target_role", ""))
    if "后端" in role:
        keywords.extend(["后端开发", "数据库", "MySQL", "Redis", "接口", "RESTful API", "Spring Boot", "Flask", "FastAPI"])
    if "前端" in role:
        keywords.extend(["前端开发", "HTML", "CSS", "JavaScript", "React", "Vue"])
    if "AI" in role or "人工智能" in role:
        keywords.extend(["人工智能", "机器学习", "深度学习", "PyTorch", "模型", "RAG"])
    if "数据" in role:
        keywords.extend(["Python", "数据库", "SQL", "机器学习", "评价指标"])

    return keywords


def item_text(item: Dict[str, Any]) -> str:
    parts = [
        item.get("id", ""),
        item.get("category", ""),
        " ".join(item.get("tags", [])),
        item.get("difficulty", ""),
        item.get("question", ""),
        item.get("answer", ""),
        " ".join(item.get("follow_up", [])),
    ]
    return " ".join(str(p) for p in parts)


def score_item(query_tokens: List[str], item: Dict[str, Any]) -> int:
    """Score an item using category/tags/question/answer keyword overlap."""
    if not query_tokens:
        return 0

    text = normalize_text(item_text(item))
    tags = [normalize_text(t) for t in item.get("tags", [])]
    category = normalize_text(item.get("category", ""))
    question = normalize_text(item.get("question", ""))

    score = 0
    for token in query_tokens:
        token_norm = normalize_text(token)
        if not token_norm:
            continue
        if token_norm in tags:
            score += 8
        if token_norm in category:
            score += 5
        if token_norm in question:
            score += 4
        if token_norm in text:
            score += 2

    # Light difficulty preference: medium questions are usually best for demos
    if item.get("difficulty") == "medium":
        score += 1
    return score


def retrieve_by_query(query: str, top_k: int = 5, path: str = DEFAULT_KB_PATH) -> List[Dict[str, Any]]:
    """Retrieve relevant knowledge entries based on a query string."""
    kb = load_knowledge_base(path)
    query_tokens = tokenize(query)

    scored: List[Tuple[int, Dict[str, Any]]] = []
    for item in kb:
        score = score_item(query_tokens, item)
        if score > 0:
            item_copy = dict(item)
            item_copy["_score"] = score
            scored.append((score, item_copy))

    scored.sort(key=lambda x: (x[0], x[1].get("difficulty") == "medium"), reverse=True)
    return [item for _, item in scored[:top_k]]


def retrieve_by_profile(profile: Dict[str, Any], top_k: int = 6, path: str = DEFAULT_KB_PATH) -> List[Dict[str, Any]]:
    """Retrieve relevant knowledge entries based on parsed resume profile."""
    keywords = flatten_profile_keywords(profile)
    query = " ".join(keywords)
    results = retrieve_by_query(query, top_k=top_k * 2, path=path)

    # Diversify categories
    diversified = []
    category_count = Counter()
    for item in results:
        cat = item.get("category", "其他")
        if category_count[cat] < 3:
            diversified.append(item)
            category_count[cat] += 1
        if len(diversified) >= top_k:
            break

    return diversified


def get_kb_stats(path: str = DEFAULT_KB_PATH) -> Dict[str, Any]:
    kb = load_knowledge_base(path)
    category_counter = Counter(item.get("category", "未分类") for item in kb)
    difficulty_counter = Counter(item.get("difficulty", "unknown") for item in kb)
    return {
        "total_entries": len(kb),
        "categories": dict(category_counter),
        "difficulties": dict(difficulty_counter)
    }


def format_rag_item_for_prompt(item: Dict[str, Any]) -> str:
    """Format one retrieved item into readable context."""
    return (
        f"知识点ID：{item.get('id', '')}\n"
        f"方向：{item.get('category', '')}\n"
        f"标签：{', '.join(item.get('tags', []))}\n"
        f"难度：{item.get('difficulty', '')}\n"
        f"参考问题：{item.get('question', '')}\n"
        f"参考答案：{item.get('answer', '')}\n"
        f"可追问：{'；'.join(item.get('follow_up', []))}"
    )
