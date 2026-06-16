import json
from typing import Any, Dict, List, Optional

from src.llm_client import call_chat, extract_json_from_text, is_llm_enabled


ALLOWED_QUESTION_TYPES = {
    "intro",
    "project",
    "project_followup",
    "rag_basic",
    "rag_followup",
    "comprehensive",
}


def get_difficulty_policy(difficulty: str) -> str:
    if "基础" in str(difficulty):
        return (
            "当前难度是【基础】。问题必须直接、友好、偏入门。"
            "优先考察定义、常见用途、基本原理、简单项目应用。"
            "不要追问源码级、分布式系统级、复杂并发或生产故障恢复细节。"
            "expected_points 应包含 2-3 个基础要点。"
        )
    if "困难" in str(difficulty):
        return (
            "当前难度是【困难】。问题可以更深入。"
            "优先考察底层机制、系统设计、性能权衡、并发一致性、故障恢复、生产级工程决策。"
            "问题仍然必须基于候选人画像和RAG，不要自由发散。"
            "expected_points 应包含 3-5 个较深入要点。"
        )
    return (
        "当前难度是【中等】。问题应考察技术原理、优缺点、常见失败场景和实际工程场景。"
        "不要过于入门，也不要跳到源码级或复杂分布式设计。"
        "expected_points 应包含 3-4 个中等深度要点。"
    )


def _compact_history(history: List[Dict[str, str]], limit: int = 6) -> List[Dict[str, str]]:
    recent = history[-limit:] if history else []
    compact = []
    for message in recent:
        role = message.get("role", "")
        content = str(message.get("content", "")).strip()
        if role and content:
            compact.append({"role": role, "content": content[:800]})
    return compact


def _compact_rag_items(rag_items: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    compact = []
    for item in (rag_items or [])[:limit]:
        compact.append({
            "id": item.get("id", ""),
            "category": item.get("category", ""),
            "tags": item.get("tags", []),
            "difficulty": item.get("difficulty", ""),
            "question_type": item.get("question_type", ""),
            "question": item.get("question", ""),
            "answer": item.get("answer", ""),
            "expected_points": item.get("expected_points", []),
            "bad_answer_signals": item.get("bad_answer_signals", []),
            "follow_up": item.get("follow_up", []),
            "related_project_scenarios": item.get("related_project_scenarios", []),
        })
    return compact


def _recent_question_openings(history: List[Dict[str, str]], limit: int = 4) -> List[str]:
    openings = []
    for message in reversed(history or []):
        if message.get("role") != "assistant":
            continue
        content = str(message.get("content", "")).strip()
        if not content:
            continue
        first_part = content.split("。", 1)[0].split("？", 1)[0].split("?", 1)[0]
        openings.append(first_part[:24])
        if len(openings) >= limit:
            break
    return list(reversed(openings))


def build_llm_interviewer_prompt(
    profile: Dict[str, Any],
    interview_stage: str,
    history: List[Dict[str, str]],
    rag_items: List[Dict[str, Any]],
    fallback_question_meta: Optional[Dict[str, Any]] = None,
    previous_question_meta: Optional[Dict[str, Any]] = None,
    previous_answer_analysis: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, str]]:
    """Build messages for grounded LLM interview question generation."""
    difficulty = str(profile.get("difficulty", "") or (fallback_question_meta or {}).get("difficulty", "中等"))
    difficulty_policy = get_difficulty_policy(difficulty)
    system_prompt = (
        "你是一名专业、友好、克制的中文技术面试官。"
        "你必须基于候选人画像、最近对话、RAG知识条目和系统建议来生成下一道面试题。"
        "RAG决定应该考察什么知识点，你只负责把问题问得自然、贴合上下文。"
        f"{difficulty_policy}"
        "每次只问一个问题，问题要简洁自然，不要在问题里泄露答案。"
        "请主动变化问题开场，不要连续使用“你刚才”“刚才我们”“顺着这个”作为开头。"
        "可以使用更像真实面试官的开场，例如："
        "“我们换个角度看这个问题”、"
        "“接下来我想考察一个更贴近生产环境的点”、"
        "“这个方案在正常流程下是成立的，但我想进一步看一下异常场景”、"
        "“从工程落地角度看，这里还有一个关键问题”、"
        "“如果把这个场景放到线上高并发环境中”、"
        "“我们先不看正常链路，重点看失败分支”、"
        "“这部分思路比较清楚了，我想进一步追问一个边界情况”、"
        "“下面我想把问题从实现层拉到架构层”。"
        "不要编造候选人画像、项目经历或知识点中没有出现的事实。"
        "如果使用RAG条目，必须保留对应knowledge_id。"
        "只输出合法JSON，不要输出Markdown代码块，不要输出解释文字。"
    )

    payload = {
        "candidate_profile": profile,
        "interview_stage": interview_stage,
        "recent_history": _compact_history(history),
        "recent_question_openings": _recent_question_openings(history),
        "rag_items": _compact_rag_items(rag_items),
        "fallback_question_meta": fallback_question_meta or {},
        "previous_question_meta": previous_question_meta or {},
        "previous_answer_analysis": previous_answer_analysis or {},
        "selected_difficulty": difficulty,
        "difficulty_policy": difficulty_policy,
        "required_json_format": {
            "question": "一个自然的中文面试问题",
            "question_type": "intro / project / project_followup / rag_basic / rag_followup / comprehensive",
            "knowledge_id": "如果使用RAG条目，填写对应id；否则为空字符串",
            "expected_points": ["候选人回答中应覆盖的要点1", "要点2", "要点3"],
            "reference_answer": "可选的简短参考答案，优先来自RAG条目",
            "reason": "为什么此时问这个问题",
            "difficulty": difficulty,
            "difficulty_reason": "说明这个问题为什么符合当前难度",
        },
    }

    user_prompt = (
        "请根据以下JSON上下文生成下一道面试题。"
        "请参考recent_question_openings，避免和最近问题使用相同或高度相似的开场。"
        "必须返回一个JSON对象，字段与required_json_format一致。\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def parse_llm_question_response(
    text: str,
    fallback_question_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Parse and normalize the LLM JSON response."""
    data = extract_json_from_text(text)
    if not isinstance(data, dict):
        raise ValueError("LLM response is not a JSON object.")

    question = str(data.get("question", "")).strip()
    if not question:
        raise ValueError("LLM response is missing question.")

    fallback_type = ""
    if fallback_question_meta:
        fallback_type = fallback_question_meta.get("type") or fallback_question_meta.get("question_type") or ""

    question_type = str(data.get("question_type") or data.get("type") or fallback_type).strip()
    if question_type not in ALLOWED_QUESTION_TYPES:
        question_type = fallback_type or "rag_basic"

    fallback_expected_points = []
    if fallback_question_meta:
        fallback_expected_points = fallback_question_meta.get("expected_points", [])
        if not fallback_expected_points:
            fallback_expected_points = fallback_question_meta.get("tags", [])

    expected_points = data.get("expected_points", []) or fallback_expected_points
    if isinstance(expected_points, str):
        expected_points = [expected_points]
    if not isinstance(expected_points, list):
        expected_points = []
    expected_points = [str(point).strip() for point in expected_points if str(point).strip()]

    normalized = {
        "question": question,
        "type": question_type,
        "question_type": question_type,
        "knowledge_id": str(
            data.get("knowledge_id")
            or (fallback_question_meta or {}).get("knowledge_id", "")
        ).strip(),
        "expected_points": expected_points,
        "reference_answer": str(
            data.get("reference_answer")
            or (fallback_question_meta or {}).get("reference_answer", "")
        ).strip(),
        "reason": str(data.get("reason", "")).strip(),
        "difficulty": str(
            data.get("difficulty")
            or (fallback_question_meta or {}).get("difficulty", "")
        ).strip(),
        "difficulty_reason": str(
            data.get("difficulty_reason")
            or (fallback_question_meta or {}).get("difficulty_reason", "")
        ).strip(),
        "generated_by": "llm",
    }

    return normalized


def generate_llm_question(
    profile: Dict[str, Any],
    interview_stage: str,
    history: List[Dict[str, str]],
    rag_items: List[Dict[str, Any]],
    fallback_question_meta: Optional[Dict[str, Any]] = None,
    previous_question_meta: Optional[Dict[str, Any]] = None,
    previous_answer_analysis: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Generate a grounded interview question with LLM, or return None if disabled."""
    if not is_llm_enabled():
        return None

    messages = build_llm_interviewer_prompt(
        profile=profile,
        interview_stage=interview_stage,
        history=history,
        rag_items=rag_items,
        fallback_question_meta=fallback_question_meta,
        previous_question_meta=previous_question_meta,
        previous_answer_analysis=previous_answer_analysis,
    )
    content = call_chat(messages=messages, temperature=0.35, timeout=75)
    return parse_llm_question_response(content, fallback_question_meta=fallback_question_meta)
