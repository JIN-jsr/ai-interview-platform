from typing import Any, Dict, List, Optional

from src.answer_analyzer import extract_keywords
from src.llm_interviewer import generate_llm_question
from src.rag_retriever import retrieve_by_profile, retrieve_by_query

MIN_PROJECT_DEEP_DIVE_FOR_COMPLETE = 2
MIN_CONTEXTUAL_FOLLOWUP_FOR_COMPLETE = 1


def get_selected_difficulty(profile: Dict[str, Any], fallback: str = "中等") -> str:
    return str(profile.get("difficulty") or fallback)


def difficulty_reason_for(difficulty: str, generated_by: str) -> str:
    source = "LLM 出题" if generated_by == "llm" else "备用出题机制"
    if "基础" in difficulty:
        level = "基础难度，优先考察定义、常见用途、基本原理和简单项目应用"
    elif "困难" in difficulty:
        level = "困难难度，可考察底层机制、系统设计、并发、性能权衡和生产问题"
    else:
        level = "中等难度，重点考察技术原理、优缺点、常见问题和工程场景"
    return f"{source}已根据当前难度选择问题：{level}"


def build_project_question(profile: Dict[str, Any], question_count: int) -> str:
    projects = profile.get("project_names", [])
    project_hint = projects[0] if projects else "你简历中最重要的一个项目"
    difficulty = get_selected_difficulty(profile)

    if "基础" in difficulty:
        if question_count == 1:
            return f"请用比较简单清楚的方式介绍一下「{project_hint}」：它解决了什么问题、你主要负责什么、用了哪些核心技术？"
        if question_count == 2:
            return f"在「{project_hint}」里，你用到的一个技术点是什么？它在项目中具体起到了什么作用？"
        return f"如果让你对「{project_hint}」做一个小优化，你会先改进哪一处？为什么？"

    if "困难" in difficulty:
        if question_count == 1:
            return f"请从架构、核心链路、数据流和你的关键贡献几个角度介绍「{project_hint}」，重点说明技术决策依据。"
        if question_count == 2:
            return f"在「{project_hint}」中，如果遇到高并发、数据一致性或故障恢复问题，你会如何分析和设计解决方案？"
        return f"如果要把「{project_hint}」提升到更接近生产环境的质量，你会如何设计监控、降级、性能优化和数据安全方案？"

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


def build_expected_points_for_difficulty(item: Dict[str, Any], difficulty: str) -> List[str]:
    tags = [str(tag) for tag in item.get("tags", []) if str(tag).strip()]
    main_topic = tags[0] if tags else str(item.get("category", "该知识点"))

    if "基础" in difficulty:
        return [
            f"{main_topic}的基本定义或作用",
            "常见使用场景",
            "一个简单项目应用例子",
        ]
    if "困难" in difficulty:
        return [
            f"{main_topic}的底层机制或关键原理",
            "性能、并发或一致性方面的权衡",
            "生产环境中的风险和解决思路",
        ]
    return [
        f"{main_topic}的核心原理",
        "优缺点或适用边界",
        "常见问题和工程场景",
    ]


def build_basic_followup(selected: str) -> str:
    return f"这个点可以再落到项目里看：{selected} 通常解决什么问题，使用时要注意什么？"


def build_medium_followup(selected: str) -> str:
    return f"从实际场景看，{selected} 的优势和风险分别是什么？什么情况下可能出现问题？"


def build_hard_followup(selected: str) -> str:
    return f"如果把 {selected} 放到高并发或生产故障场景下，你会如何权衡性能、一致性和可恢复性？"


def select_next_rag_item(
    rag_items: List[Dict[str, Any]],
    rag_index: int,
    used_knowledge_ids: Optional[List[str]] = None,
    used_categories: Optional[List[str]] = None
) -> Optional[tuple]:
    """Pick the next RAG item while avoiding recently used knowledge and categories."""
    used_ids = set(used_knowledge_ids or [])
    recent_categories = list(used_categories or [])[-3:]

    fallback = None
    for idx in range(rag_index, len(rag_items)):
        item = rag_items[idx]
        knowledge_id = item.get("id")
        category = item.get("category", "")
        if knowledge_id in used_ids:
            continue
        if fallback is None:
            fallback = (idx, item)
        if category not in recent_categories:
            return idx, item
    return fallback


def build_project_followup(user_answer: str, profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Generate a project follow-up based on technologies mentioned in the answer."""
    keywords = extract_keywords(user_answer)
    if not keywords:
        return None
    difficulty = get_selected_difficulty(profile)

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
        if "基础" in difficulty:
            q = build_basic_followup(selected)
        elif "困难" in difficulty:
            q = build_hard_followup(selected)
        elif followups:
            q = f"围绕 {selected}，我想继续追问一个项目场景问题：{followups[0]}"
        else:
            q = build_medium_followup(selected)
        return {
            "question": q,
            "type": "project_followup",
            "knowledge_id": item.get("id"),
            "reference_answer": item.get("answer", ""),
            "expected_points": item.get("expected_points", build_expected_points_for_difficulty(item, difficulty)),
            "difficulty": difficulty,
            "difficulty_reason": difficulty_reason_for(difficulty, "rule_fallback"),
            "tags": item.get("tags", []),
            "source": "answer_keyword_followup"
        }

    if "基础" in difficulty:
        fallback_question = build_basic_followup(selected)
    elif "困难" in difficulty:
        fallback_question = build_hard_followup(selected)
    else:
        fallback_question = build_medium_followup(selected)

    return {
        "question": fallback_question,
        "type": "project_followup",
        "difficulty": difficulty,
        "difficulty_reason": difficulty_reason_for(difficulty, "rule_fallback"),
        "tags": [selected],
        "source": "answer_keyword_followup"
    }


def build_rag_followup(previous_meta: Dict[str, Any], analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Ask a follow-up when a RAG answer misses important points."""
    difficulty = str(previous_meta.get("difficulty", "中等"))
    followups = previous_meta.get("follow_up", [])
    if not followups:
        followups = previous_meta.get("followups", [])
    scenarios = previous_meta.get("related_project_scenarios", [])

    missing = analysis.get("missing_points", [])
    if "基础" in difficulty and missing:
        question = f"这个点我们先不用展开太深。请你用自己的话补充说明：{'、'.join(missing[:2])} 分别是什么意思，或者在项目里有什么简单用途？"
    elif "基础" in difficulty:
        question = "请你再用一个简单项目场景说明刚才这个知识点通常怎么使用。"
    elif "困难" in difficulty and followups:
        question = f"继续深入一点：{followups[0]} 请结合并发、性能或故障场景说明你的判断。"
    elif "困难" in difficulty and missing:
        question = f"你的回答还可以从更深层机制补充，例如：{'、'.join(missing[:3])}。请结合工程风险继续说明。"
    elif followups:
        question = f"你这个回答还可以更完整。继续追问：{followups[0]}"
    elif scenarios:
        question = f"请结合一个更真实的项目场景继续说明，比如：{scenarios[0]}。你会如何使用或验证这个知识点？"
    elif missing:
        question = f"这个回答里还缺少一些关键点，例如：{'、'.join(missing[:3])}。请结合常见工程场景补充说明这些点。"
    else:
        return None

    return {
        "question": question,
        "type": "rag_followup",
        "knowledge_id": previous_meta.get("knowledge_id"),
        "reference_answer": previous_meta.get("reference_answer", ""),
        "expected_points": previous_meta.get("expected_points", previous_meta.get("tags", [])),
        "difficulty": difficulty,
        "difficulty_reason": difficulty_reason_for(difficulty, "rule_fallback"),
        "tags": previous_meta.get("tags", []),
        "related_project_scenarios": scenarios,
        "source": "rag_missing_points_followup"
    }


def _get_rule_based_question(
    profile: Dict[str, Any],
    history: List[Dict[str, str]],
    rag_items: List[Dict[str, Any]],
    rag_index: int,
    last_answer: str = "",
    last_question_meta: Optional[Dict[str, Any]] = None,
    last_analysis: Optional[Dict[str, Any]] = None,
    followup_count: int = 0,
    max_followups: int = 3,
    used_knowledge_ids: Optional[List[str]] = None,
    used_categories: Optional[List[str]] = None,
    asked_project_count: int = 0,
    asked_followup_count: int = 0,
    target_question_count: int = 8
) -> Dict[str, Any]:
    """Return next interview question with context-aware follow-up.

    This keeps the interview moving with contextual follow-up questions.
    """
    assistant_count = len([m for m in history if m.get("role") == "assistant"])
    difficulty = get_selected_difficulty(profile)
    has_project_context = bool(profile.get("project_names") or profile.get("candidate_profile") or profile.get("interview_focus"))

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

    remaining_slots = max(0, target_question_count - assistant_count)
    if (
        has_project_context
        and assistant_count >= max(4, target_question_count - 2)
        and asked_project_count < MIN_PROJECT_DEEP_DIVE_FOR_COMPLETE
        and remaining_slots > 0
    ):
        return {
            "question": build_project_question(profile, asked_project_count + 1),
            "type": "project",
            "rag_index": rag_index,
            "followup_count": followup_count,
            "coverage_repair_reason": "项目深挖题数量不足，系统优先补齐项目证据。"
        }

    if (
        assistant_count >= max(5, target_question_count - 2)
        and asked_followup_count < MIN_CONTEXTUAL_FOLLOWUP_FOR_COMPLETE
        and last_question_meta
        and last_answer
    ):
        follow = build_project_followup(last_answer, profile) or build_rag_followup(last_question_meta, last_analysis or {})
        if follow:
            follow["rag_index"] = rag_index
            follow["followup_count"] = followup_count + 1
            follow["coverage_repair_reason"] = "上下文追问题数量不足，系统优先补齐追问证据。"
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
        selected = select_next_rag_item(rag_items, rag_index, used_knowledge_ids, used_categories)
        if selected:
            selected_index, item = selected
            meta = {
                "question": build_rag_question(item, selected_index),
                "type": "rag_basic",
                "knowledge_id": item.get("id"),
                "reference_answer": item.get("answer"),
                "expected_points": item.get("expected_points", build_expected_points_for_difficulty(item, difficulty)),
                "difficulty": difficulty,
                "difficulty_reason": difficulty_reason_for(difficulty, "rule_fallback"),
                "tags": item.get("tags", []),
                "follow_up": item.get("follow_up", []),
                "category": item.get("category", ""),
                "related_project_scenarios": item.get("related_project_scenarios", []),
                "rag_index": selected_index + 1,
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
        "question": "本轮模拟面试已结束。你可以查看面试记录、回答分析，并生成正式评分报告。",
        "type": "end",
        "rag_index": rag_index,
        "followup_count": followup_count
    }


def prepare_rag_items_for_interview(profile: Dict[str, Any], top_k: int = 6) -> List[Dict[str, Any]]:
    return retrieve_by_profile(profile, top_k=top_k)


def normalize_question_metadata(
    meta: Dict[str, Any],
    generated_by: str,
    fallback_meta: Optional[Dict[str, Any]] = None,
    profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Keep question metadata compatible and enforce generation/fallback invariants."""
    fallback_meta = fallback_meta or {}
    normalized = dict(fallback_meta)
    normalized.update(meta or {})

    question_type = (
        normalized.get("type")
        or normalized.get("question_type")
        or fallback_meta.get("type")
        or "unknown"
    )
    normalized["type"] = question_type
    normalized["question_type"] = question_type
    normalized["generated_by"] = generated_by
    if generated_by == "rule_fallback" and not normalized.get("fallback_reason"):
        normalized["fallback_reason"] = "本轮已启用备用出题机制，面试流程将继续进行。"
    if generated_by == "llm":
        normalized.pop("fallback_reason", None)

    difficulty = (
        normalized.get("difficulty")
        or fallback_meta.get("difficulty")
        or (profile or {}).get("difficulty")
        or "中等"
    )
    normalized["difficulty"] = difficulty
    if not normalized.get("difficulty_reason"):
        normalized["difficulty_reason"] = fallback_meta.get(
            "difficulty_reason",
            difficulty_reason_for(str(difficulty), generated_by)
        )

    if not normalized.get("knowledge_id"):
        normalized["knowledge_id"] = fallback_meta.get("knowledge_id", "")
    if not normalized.get("reference_answer"):
        normalized["reference_answer"] = fallback_meta.get("reference_answer", "")

    expected_points = normalized.get("expected_points", [])
    if not expected_points:
        expected_points = fallback_meta.get("expected_points", [])
    if not expected_points:
        expected_points = fallback_meta.get("tags", [])
    if isinstance(expected_points, str):
        expected_points = [expected_points]
    if not isinstance(expected_points, list):
        expected_points = []
    normalized["expected_points"] = [str(point).strip() for point in expected_points if str(point).strip()]

    if not normalized.get("tags"):
        normalized["tags"] = fallback_meta.get("tags", []) or normalized["expected_points"]
    if not normalized.get("category"):
        normalized["category"] = fallback_meta.get("category", "")

    normalized["rag_index"] = normalized.get("rag_index", fallback_meta.get("rag_index", 0))
    normalized["followup_count"] = normalized.get(
        "followup_count",
        fallback_meta.get("followup_count", 0)
    )
    return normalized


def _normalize_question_meta(
    meta: Dict[str, Any],
    generated_by: str,
    fallback_meta: Optional[Dict[str, Any]] = None,
    profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    return normalize_question_metadata(meta, generated_by, fallback_meta, profile)


def _select_llm_rag_context(
    fallback_meta: Dict[str, Any],
    rag_items: List[Dict[str, Any]],
    rag_index: int,
    used_knowledge_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Prefer the exact RAG item used by the fallback question, then nearby items."""
    knowledge_id = fallback_meta.get("knowledge_id")
    used_ids = set(used_knowledge_ids or [])
    selected: List[Dict[str, Any]] = []

    if knowledge_id:
        selected.extend([item for item in rag_items if item.get("id") == knowledge_id])

    if not selected and 0 <= rag_index < len(rag_items) and rag_items[rag_index].get("id") not in used_ids:
        selected.append(rag_items[rag_index])

    for item in rag_items:
        if item.get("id") in used_ids and item.get("id") != knowledge_id:
            continue
        if item not in selected:
            selected.append(item)
        if len(selected) >= 3:
            break

    return selected


def get_next_question(
    profile: Dict[str, Any],
    history: List[Dict[str, str]],
    rag_items: List[Dict[str, Any]],
    rag_index: int,
    last_answer: str = "",
    last_question_meta: Optional[Dict[str, Any]] = None,
    last_analysis: Optional[Dict[str, Any]] = None,
    followup_count: int = 0,
    max_followups: int = 3,
    used_knowledge_ids: Optional[List[str]] = None,
    used_categories: Optional[List[str]] = None,
    asked_project_count: int = 0,
    asked_followup_count: int = 0,
    target_question_count: int = 8
) -> Dict[str, Any]:
    """Return the next question, using LLM+RAG first and rule logic as fallback."""
    fallback = _get_rule_based_question(
        profile=profile,
        history=history,
        rag_items=rag_items,
        rag_index=rag_index,
        last_answer=last_answer,
        last_question_meta=last_question_meta,
        last_analysis=last_analysis,
        followup_count=followup_count,
        max_followups=max_followups,
        used_knowledge_ids=used_knowledge_ids,
        used_categories=used_categories,
        asked_project_count=asked_project_count,
        asked_followup_count=asked_followup_count,
        target_question_count=target_question_count
    )
    fallback = _normalize_question_meta(fallback, generated_by="rule_fallback", profile=profile)

    interview_stage = fallback.get("type", "unknown")
    if interview_stage == "end":
        return fallback

    try:
        llm_meta = generate_llm_question(
            profile=profile,
            interview_stage=interview_stage,
            history=history,
            rag_items=_select_llm_rag_context(fallback, rag_items, rag_index, used_knowledge_ids),
            fallback_question_meta=fallback,
            previous_question_meta=last_question_meta,
            previous_answer_analysis=last_analysis
        )
    except Exception as exc:
        fallback["llm_error"] = str(exc)
        fallback["fallback_reason"] = f"LLM 出题暂时不可用，已启用备用出题机制。原因：{exc}"
        return fallback

    if not llm_meta:
        fallback["fallback_reason"] = "LLM 未启用或未返回有效题目，已启用备用出题机制。"
        return fallback

    llm_knowledge_id = llm_meta.get("knowledge_id")
    if llm_knowledge_id and llm_knowledge_id in set(used_knowledge_ids or []):
        fallback["fallback_reason"] = f"LLM 返回了近期已使用的知识点 {llm_knowledge_id}，已切换到不重复的备用题目。"
        fallback["llm_rejected_reason"] = "repeated_knowledge_id"
        return fallback

    return _normalize_question_meta(llm_meta, generated_by="llm", fallback_meta=fallback, profile=profile)
