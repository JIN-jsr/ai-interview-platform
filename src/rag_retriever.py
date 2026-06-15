import json
from pathlib import Path
from typing import List, Dict


def load_knowledge_base(path: str = "data/knowledge_base.json") -> List[Dict]:
    kb_path = Path(path)
    if not kb_path.exists():
        return []
    return json.loads(kb_path.read_text(encoding="utf-8"))


def keyword_retrieve(query: str, top_k: int = 3) -> List[Dict]:
    """Day 1 placeholder: simple keyword matching.

    Later this can be replaced by FAISS/Chroma vector retrieval.
    """
    items = load_knowledge_base()
    scored = []
    query_lower = query.lower()

    for item in items:
        text = " ".join([
            item.get("category", ""),
            " ".join(item.get("tags", [])),
            item.get("question", ""),
            item.get("answer", "")
        ]).lower()
        score = sum(1 for word in query_lower.split() if word in text)
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_k]]
