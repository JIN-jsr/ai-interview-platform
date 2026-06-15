from typing import Any, Dict, List, Optional

from src.answer_analyzer import extract_keywords
from src.rag_retriever import retrieve_by_profile, retrieve_by_query


def build_project_question(profile: Dict[str, Any], question_count: int) -> str:
    projects = profile.get("project_names", [])
    project_hint = projects[0] if projects else "你简历中最重要的一个项目"

    if question_count == 1:
        return f"请详细介绍一下「{project_hint}」，包括项目背景、你的职责和使用的核心技术。"
    if question_count == 2:
        return f"在「{project_hint}」中，你遇到的最大技术难点是什么？你是如何分析和解决的？"
    return f"如果让你重新优化「{project_hint}」，你会从架构、性能或用户体验中的哪个方面改进？为什么？"


def build_rag_question(item: Dict[str, Any], index: int) -> str:
    tags = "、".join(item.get("tags", []))
    question = item.get("question", "请解释一个相关基础知识点。")
    followups = item.get("follow_up", [])

    if index == 0:
        prefix = "下面进入基础知识考察。"
    else:
        prefix = "继续考察一个相关基础知识点。"

    followup_text = ""
    if followups:
        followup_text = f" 回答后我可能会继续追问：{followups[0]}"

    return f"{prefix}这个问题与你简历中的技术栈相关（{tags}）：{question}{followup_text}"


def build_project_followup(user_answer: str, profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Generate a project follow-up based on technologies mentioned in the answer."""
    keywords = extract_keywords(user_answer)
    if not keywords:
        return None

    # Prefer technical keywords that are good for deep-dive questions.
    priority = ["Redis", "MySQL", "数据库", "索引", "事务", "缓存", "Flask", "Spring Boot", "API", "Docker", "机器学习", "PyTorch", "RAG"]
    selected = None
    for p in priority:
        if p in keywords:
            selected = p
            break
    if selected is None:
        selected = keywords[0]

    related = retrieve_by_query(selected, top_k=1)
    if related:
        item = related[0]
        followups = item.get("follow_up", [])
        if followups:
            q = f"你刚才提到了 {selected}。我想继续追问一下：{followups[0]} 请结合你的项目场景回答。"
        else:
            q = f"你刚才提到了 {selected}。请你进一步说明它在项目中的具体作用、实现方式和可能的风险。"
        return {
            "question": q,
            "type": "project_followup",
            "knowledge_id": item.get("id"),
            "reference_answer": item.get("answer", ""),
            "tags": item.get("tags", []),
            "source": "answer_keyword_followup"
        }

    return {
        "question": f"你刚才提到了 {selected}。请你进一步说明它在项目中的具体作用、实现方式和遇到的问题。",
        "type": "project_followup",
        "tags": [selected],
        "source": "answer_keyword_followup"
    }


def build_rag_followup(previous_meta: Dict[str, Any], analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Ask a follow-up when a RAG answer misses important points."""
    followups = previous_meta.get("follow_up", [])
    if not followups:
        followups = previous_meta.get("followups", [])

    missing = analysis.get("missing_points", [])
    if followups:
        question = f"你这个回答还可以更完整。继续追问：{followups[0]}"
    elif missing:
        question = f"你刚才的回答里还缺少一些关键点，例如：{'、'.join(missing[:3])}。请你补充说明这些点。"
    else:
        return None

    return {
        "question": question,
        "type": "rag_followup",
        "knowledge_id": previous_meta.get("knowledge_id"),
        "reference_answer": previous_meta.get("reference_answer", ""),
        "tags": previous_meta.get("tags", []),
        "source": "rag_missing_points_followup"
    }


def get_next_question(
    profile: Dict[str, Any],
    history: List[Dict[str, str]],
    rag_items: List[Dict[str, Any]],
    rag_index: int,
    last_answer: str = "",
    last_question_meta: Optional[Dict[str, Any]] = None,
    last_analysis: Optional[Dict[str, Any]] = None,
    followup_count: int = 0,
    max_followups: int = 3
) -> Dict[str, Any]:
    """Return next interview question with context-aware follow-up.

    Day 4 improvement:
    - Analyze the previous answer.
    - If the candidate mentions a technical keyword in a project answer, ask a project deep-dive follow-up.
    - If a RAG answer misses key points, ask a knowledge follow-up.
    - Limit follow-up count to avoid infinite questioning.
    """
    assistant_count = len([m for m in history if m.get("role") == "assistant"])

    if assistant_count == 0:
        return {
            "question": "你好，我是今天的 AI 技术面试官。请你先用 1 分钟做一个简短的自我介绍，重点说明你的技术栈、项目经历以及目标岗位。",
            "type": "intro",
            "rag_index": rag_index,
            "followup_count": followup_count
        }

    # Context-aware follow-up
    if last_question_meta and last_analysis and followup_count < max_followups:
        last_type = last_question_meta.get("type")

        if last_type == "project":
            follow = build_project_followup(last_answer, profile)
            if follow:
                follow["rag_index"] = rag_index
                follow["followup_count"] = followup_count + 1
                return follow

        if last_type == "rag_basic" and last_analysis.get("coverage_ratio", 1) < 0.45:
            follow = build_rag_followup(last_question_meta, last_analysis)
            if follow:
                follow["rag_index"] = rag_index
                follow["followup_count"] = followup_count + 1
                return follow

    # Main staged flow
    if assistant_count in [1, 2]:
        return {
            "question": build_project_question(profile, assistant_count),
            "type": "project",
            "rag_index": rag_index,
            "followup_count": followup_count
        }

    if assistant_count in [3, 4, 5, 6]:
        if rag_index < len(rag_items):
            item = rag_items[rag_index]
            meta = {
                "question": build_rag_question(item, rag_index),
                "type": "rag_basic",
                "knowledge_id": item.get("id"),
                "reference_answer": item.get("answer"),
                "tags": item.get("tags", []),
                "follow_up": item.get("follow_up", []),
                "rag_index": rag_index + 1,
                "followup_count": followup_count
            }
            return meta

        return {
            "question": "接下来考察基础知识。请你选择一个简历中写到的技术点，说明它的核心原理和项目应用场景。",
            "type": "basic",
            "rag_index": rag_index,
            "followup_count": followup_count
        }

    if assistant_count == 7:
        role = profile.get("target_role", "目标岗位")
        return {
            "question": f"最后一个综合问题：你认为自己为什么适合{role}？请结合项目经历、技术能力和后续学习计划回答。",
            "type": "comprehensive",
            "rag_index": rag_index,
            "followup_count": followup_count
        }

    return {
        "question": "本轮 Day 4 面试流程已结束。你可以到下方查看面试记录、回答分析和上下文追问情况。Day 5 会加入正式评分反馈报告。",
        "type": "end",
        "rag_index": rag_index,
        "followup_count": followup_count
    }


def prepare_rag_items_for_interview(profile: Dict[str, Any], top_k: int = 6) -> List[Dict[str, Any]]:
    return retrieve_by_profile(profile, top_k=top_k)
