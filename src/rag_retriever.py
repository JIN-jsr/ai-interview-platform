import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.product_features import ROLE_KEYWORDS, normalize_role


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

    role = normalize_role(str(profile.get("target_role", "")))
    keywords.extend(ROLE_KEYWORDS.get(role, []))
    if role == "后端开发":
        keywords.extend(["计算机网络", "操作系统", "Linux", "Docker", "事务", "索引", "缓存"])
    elif role == "AI应用开发":
        keywords.extend(["人工智能", "机器学习", "深度学习", "PyTorch", "模型", "检索增强生成"])
    elif role == "数据分析":
        keywords.extend(["Python", "数据库", "SQL", "评价指标", "业务指标"])

    return keywords


def role_priority_score(profile: Dict[str, Any], item: Dict[str, Any]) -> int:
    """Give role-specific items a small ranking boost without changing retrieval rules."""
    role = str(profile.get("target_role", ""))
    text = normalize_text(item_text(item))
    score = 0

    if "后端" in role:
        preferred_terms = [
            "mysql", "redis", "数据库", "事务", "索引", "缓存", "api", "接口",
            "restful", "http", "tcp", "网络", "操作系统", "进程", "线程",
            "linux", "docker", "部署", "后端", "spring", "flask", "fastapi"
        ]
        frontend_terms = ["html", "css", "javascript", "react", "vue", "前端", "浏览器", "页面"]
        for term in preferred_terms:
            if term in text:
                score += 6
        for term in frontend_terms:
            if term in text:
                score -= 8

    if "前端" in role:
        preferred_terms = ["html", "css", "javascript", "react", "vue", "前端", "浏览器", "页面"]
        for term in preferred_terms:
            if term in text:
                score += 6

    if "AI" in role or "人工智能" in role:
        preferred_terms = [
            "rag", "llm", "大模型", "大模型api", "prompt", "prompt engineering",
            "embedding", "向量数据库", "chroma", "langchain", "function calling",
            "agent", "rerank", "token", "检索增强", "向量检索", "模型幻觉"
        ]
        for term in preferred_terms:
            if term in text:
                score += 7

    if "数据" in role:
        preferred_terms = [
            "sql", "pandas", "numpy", "excel", "数据清洗", "指标", "可视化",
            "a/b", "假设检验", "置信区间", "漏斗", "留存", "报表", "样本量"
        ]
        for term in preferred_terms:
            if term in text:
                score += 7

    if "测试" in role:
        preferred_terms = [
            "测试", "pytest", "接口测试", "自动化测试", "回归测试", "冒烟测试",
            "边界值", "等价类", "mock", "fixture", "flaky", "性能测试",
            "压力测试", "日志分析", "异常场景", "缺陷", "ci/cd", "playwright",
            "selenium", "rag 相关性", "json 合法性", "fallback"
        ]
        for term in preferred_terms:
            if term in text:
                score += 8

    return score


def normalize_profile_difficulty(profile: Dict[str, Any]) -> str:
    difficulty = str(profile.get("difficulty", "")).strip()
    if "基础" in difficulty or difficulty.lower() in {"easy", "basic"}:
        return "easy"
    if "困难" in difficulty or "高级" in difficulty or difficulty.lower() in {"hard", "difficult"}:
        return "hard"
    return "medium"


def difficulty_priority_score(profile: Dict[str, Any], item: Dict[str, Any]) -> int:
    """Prefer knowledge entries that match the selected interview difficulty."""
    target = normalize_profile_difficulty(profile)
    item_difficulty = str(item.get("difficulty", "medium")).lower()

    preference = {
        "easy": {"easy": 30, "medium": 10, "hard": -30},
        "medium": {"medium": 30, "easy": 12, "hard": 8},
        "hard": {"hard": 35, "medium": 16, "easy": -20},
    }
    return preference.get(target, preference["medium"]).get(item_difficulty, 0)


def item_text(item: Dict[str, Any]) -> str:
    parts = [
        item.get("id", ""),
        item.get("category", ""),
        " ".join(item.get("tags", [])),
        item.get("difficulty", ""),
        item.get("question_type", ""),
        item.get("question", ""),
        item.get("answer", ""),
        " ".join(item.get("expected_points", [])),
        " ".join(item.get("follow_up", [])),
        " ".join(item.get("bad_answer_signals", [])),
        " ".join(item.get("related_project_scenarios", [])),
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
    question_type = normalize_text(item.get("question_type", ""))

    score = 0
    for token in query_tokens:
        token_norm = normalize_text(token)
        if not token_norm:
            continue
        if token_norm in tags:
            score += 8
        if token_norm in category:
            score += 5
        if token_norm in question_type:
            score += 3
        if token_norm in question:
            score += 4
        if token_norm in text:
            score += 2

    return score


def topic_key(item: Dict[str, Any]) -> str:
    tags = item.get("tags", [])
    if tags:
        first = normalize_text(tags[0])
        if first in {"mysql", "redis", "python", "java", "http", "tcp", "linux", "rag"}:
            return first
        return first[:12]
    return normalize_text(item.get("category", "其他"))


def interleave_diverse_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Reorder selected items so adjacent questions avoid the same topic when possible."""
    remaining = list(items)
    ordered = []
    while remaining:
        if not ordered:
            ordered.append(remaining.pop(0))
            continue

        last = ordered[-1]
        last_category = last.get("category", "")
        last_topic = topic_key(last)
        pick_index = 0
        for idx, item in enumerate(remaining):
            if item.get("category", "") != last_category and topic_key(item) != last_topic:
                pick_index = idx
                break
        ordered.append(remaining.pop(pick_index))
    return ordered


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


def retrieve_by_profile(
    profile: Dict[str, Any],
    top_k: int = 6,
    path: str = DEFAULT_KB_PATH,
    recent_context: str = "",
    used_knowledge_ids: List[str] = None,
    used_categories: List[str] = None
) -> List[Dict[str, Any]]:
    """Retrieve relevant knowledge entries based on parsed resume profile."""
    keywords = flatten_profile_keywords(profile)
    if recent_context:
        keywords.append(recent_context)
    query = " ".join(keywords)
    results = retrieve_by_query(query, top_k=top_k * 8, path=path)
    used_knowledge_ids = set(used_knowledge_ids or [])
    recent_categories = list(used_categories or [])[-4:]
    if used_knowledge_ids:
        results = [item for item in results if item.get("id") not in used_knowledge_ids]
    results.sort(
        key=lambda item: (
            -recent_categories.count(item.get("category", "")),
            difficulty_priority_score(profile, item),
            role_priority_score(profile, item),
            item.get("_score", 0),
            item.get("difficulty") == "medium"
        ),
        reverse=True
    )

    # Diversify categories and primary topics to avoid Redis/Redis/Redis style interviews.
    diversified = []
    category_count = Counter()
    topic_count = Counter()
    for item in results:
        cat = item.get("category", "其他")
        topic = topic_key(item)
        if category_count[cat] < 2 and topic_count[topic] < 2:
            diversified.append(item)
            category_count[cat] += 1
            topic_count[topic] += 1
        if len(diversified) >= top_k:
            break

    if len(diversified) < top_k:
        used_ids = {item.get("id") for item in diversified}
        for item in results:
            if item.get("id") in used_ids:
                continue
            diversified.append(item)
            used_ids.add(item.get("id"))
            if len(diversified) >= top_k:
                break

    return interleave_diverse_items(diversified)


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
        f"题型：{item.get('question_type', '')}\n"
        f"参考问题：{item.get('question', '')}\n"
        f"参考答案：{item.get('answer', '')}\n"
        f"期望要点：{'；'.join(item.get('expected_points', []))}\n"
        f"可追问：{'；'.join(item.get('follow_up', []))}\n"
        f"相关项目场景：{'；'.join(item.get('related_project_scenarios', []))}"
    )
