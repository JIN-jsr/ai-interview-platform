import json
from typing import Any, Dict, List

from src.llm_client import call_chat, extract_json_from_text, is_llm_enabled


LOCAL_FALLBACK_NOTE = "LLM 暂时不可用，已使用本地规则生成反馈内容。"
DEFAULT_FEEDBACK_TIMEOUT_SECONDS = 120
GROWTH_CURVE_TIMEOUT_SECONDS = 120
ANSWER_FEEDBACK_TIMEOUT_SECONDS = 60


def _clean_list(value: Any, limit: int = 6) -> List[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()][:limit]


def _compact_answer_record(record: Dict[str, Any]) -> Dict[str, Any]:
    analysis = (record or {}).get("analysis") or {}
    return {
        "question": str((record or {}).get("question", ""))[:300],
        "question_type": (record or {}).get("question_type", ""),
        "display_topic": (record or {}).get("display_topic", ""),
        "display_category": (record or {}).get("display_category", ""),
        "expected_points": _clean_list((record or {}).get("expected_points", []), limit=8),
        "user_answer": str((record or {}).get("user_answer", ""))[:900],
        "analysis": {
            "coverage_ratio": analysis.get("coverage_ratio", 0),
            "covered_points": _clean_list(analysis.get("covered_points", []), limit=6),
            "missing_points": _clean_list(analysis.get("missing_points", []), limit=6),
            "problems": _clean_list(analysis.get("problems", []), limit=5),
            "suggestions": _clean_list(analysis.get("suggestions", []), limit=5),
            "matched_misconceptions": _clean_list(analysis.get("matched_misconceptions", []), limit=4),
            "matched_critical_errors": _clean_list(analysis.get("matched_critical_errors", []), limit=4),
        },
    }


def _safe_json_chat(payload: Dict[str, Any], task: str, timeout: int = DEFAULT_FEEDBACK_TIMEOUT_SECONDS) -> Dict[str, Any]:
    if not is_llm_enabled():
        raise RuntimeError("disabled")
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个中文 AI 面试训练产品的反馈文案润色助手。"
                "只能基于输入的结构化数据改写和提炼，不得编造简历、面试原文、分数或事实。"
                "只输出合法 JSON，不要输出 Markdown，也不要解释。"
            ),
        },
        {
            "role": "user",
            "content": f"{task}\n\n{json.dumps(payload, ensure_ascii=False, indent=2)}",
        },
    ]
    content = call_chat(messages=messages, temperature=0.25, timeout=timeout)
    data = extract_json_from_text(content)
    if not isinstance(data, dict):
        raise ValueError("invalid_json")
    return data


def polish_answer_feedback_with_llm(
    record: Dict[str, Any],
    local_summary: Dict[str, Any],
) -> Dict[str, Any]:
    fallback = {
        "status": str((local_summary or {}).get("status", "")).strip() or "基本到位，仍可补充",
        "highlights": _clean_list((local_summary or {}).get("highlights", []), limit=3),
        "missing": _clean_list((local_summary or {}).get("missing", []), limit=3),
        "suggestion": str((local_summary or {}).get("suggestion", "")).strip(),
        "source": "rule_based",
        "llm_note": LOCAL_FALLBACK_NOTE,
        "fallback_reason": "disabled" if not is_llm_enabled() else "",
    }
    if not is_llm_enabled():
        return fallback

    payload = {
        "answer_record": _compact_answer_record(record),
        "local_feedback": fallback,
        "required_output": {
            "status": "覆盖较完整 / 基本到位，仍可补充 / 存在明显遗漏 / 建议重新组织回答",
            "highlights": ["亮点1", "亮点2"],
            "missing": ["最重要缺失1", "最重要缺失2"],
            "suggestion": "一条可执行改进建议",
        },
    }
    try:
        data = _safe_json_chat(
            payload,
            (
                "请基于本地分析结果润色单题答后即时反馈。要求中文、简洁、可执行。"
                "不得展示完整参考答案，不得编造事实，不得输出分数，不得改变覆盖率或评分。"
            ),
            timeout=ANSWER_FEEDBACK_TIMEOUT_SECONDS,
        )
        status = str(data.get("status", "")).strip()
        if status not in {"覆盖较完整", "基本到位，仍可补充", "存在明显遗漏", "建议重新组织回答"}:
            status = fallback["status"]
        suggestion = str(data.get("suggestion", "")).strip() or fallback["suggestion"]
        return {
            "status": status,
            "highlights": _clean_list(data.get("highlights", []), limit=3) or fallback["highlights"],
            "missing": _clean_list(data.get("missing", []), limit=3) or fallback["missing"],
            "suggestion": suggestion,
            "source": "llm",
            "llm_note": "已使用 LLM 辅助润色本题反馈，评分依据仍来自本地规则。",
            "fallback_reason": "",
        }
    except Exception as exc:
        fallback["fallback_reason"] = str(exc)
        fallback["llm_note"] = f"{LOCAL_FALLBACK_NOTE}原因：{exc}"
        return fallback


def polish_interview_answer_summary_with_llm(
    records: List[Dict[str, Any]],
    rule_summary: Dict[str, Any],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    fallback = {
        "summary": "本轮回答分析已基于本地规则生成，可结合逐题反馈继续复盘。",
        "strengths": [],
        "main_gaps": _clean_list((rule_summary or {}).get("common_problems", []), limit=5),
        "recommendations": ["优先复盘低覆盖题目，补充项目例子、验证方式和边界条件。"],
        "source": "rule_based",
        "llm_note": LOCAL_FALLBACK_NOTE,
        "fallback_reason": "disabled" if not is_llm_enabled() else "",
    }
    if not is_llm_enabled():
        return fallback

    compact_records = []
    for record in records or []:
        item = _compact_answer_record(record)
        item.pop("user_answer", None)
        compact_records.append(item)
    payload = {
        "target_role": (profile or {}).get("target_role", ""),
        "difficulty": (profile or {}).get("difficulty", ""),
        "rule_summary": rule_summary or {},
        "answer_records": compact_records[:10],
        "required_output": {
            "summary": "一段总体回答表现总结",
            "strengths": ["总体亮点1", "总体亮点2"],
            "main_gaps": ["主要短板1", "主要短板2"],
            "recommendations": ["后续训练建议1", "后续训练建议2"],
        },
    }
    try:
        data = _safe_json_chat(
            payload,
            (
                "请基于本地逐题分析润色总体回答分析。要求中文、具体、克制。"
                "不得修改最终分数、不得生成招聘结论、不得输出完整参考答案。"
            ),
            timeout=ANSWER_FEEDBACK_TIMEOUT_SECONDS,
        )
        summary = str(data.get("summary", "")).strip()
        if not summary:
            raise ValueError("empty_summary")
        return {
            "summary": summary,
            "strengths": _clean_list(data.get("strengths", []), limit=5),
            "main_gaps": _clean_list(data.get("main_gaps", []), limit=5),
            "recommendations": _clean_list(data.get("recommendations", []), limit=5),
            "source": "llm",
            "llm_note": "已使用 LLM 辅助润色总体回答分析，最终评分仍由本地规则计算。",
            "fallback_reason": "",
        }
    except Exception as exc:
        fallback["fallback_reason"] = str(exc)
        fallback["llm_note"] = f"{LOCAL_FALLBACK_NOTE}原因：{exc}"
        return fallback


def _compact_growth_reports(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    compact = []
    for report in reports or []:
        compact.append({
            "title": report.get("title", ""),
            "generated_at": report.get("generated_at", ""),
            "target_role": report.get("target_role", ""),
            "difficulty": report.get("difficulty", ""),
            "total_score": report.get("total_score", 0),
            "dimension_scores": report.get("dimension_scores", {}),
        })
    return compact


def polish_growth_curve_with_llm(
    reports: List[Dict[str, Any]],
    rule_analysis: Dict[str, Any],
) -> Dict[str, Any]:
    fallback = dict(rule_analysis or {})
    fallback.setdefault("dimension_analysis", [])
    fallback.setdefault("recommendations", [])
    fallback["source"] = fallback.get("source", "rule_based")
    fallback["llm_note"] = LOCAL_FALLBACK_NOTE

    payload = {
        "selected_reports": _compact_growth_reports(reports),
        "rule_based_summary": fallback.get("summary", ""),
        "weakest_dimension": fallback.get("weakest_dimension", ""),
        "fastest_improving_dimension": fallback.get("fastest_improving_dimension", ""),
        "most_volatile_dimension": fallback.get("most_volatile_dimension", ""),
        "rule_based_recommendations": fallback.get("recommendations", []),
        "required_output": {
            "growth_summary": "一段简洁总结",
            "dimension_analysis": ["维度变化分析1", "维度变化分析2"],
            "recommendations": ["建议1", "建议2", "建议3"],
        },
    }
    try:
        data = _safe_json_chat(
            payload,
            "请基于所选报告润色能力成长曲线的总结、维度变化分析和后续建议。要求中文、具体、简洁，不过度鼓励。",
            timeout=GROWTH_CURVE_TIMEOUT_SECONDS,
        )
        summary = str(data.get("growth_summary", "")).strip()
        if not summary:
            raise ValueError("empty_summary")
        return {
            "summary": summary,
            "dimension_analysis": _clean_list(data.get("dimension_analysis", []), limit=5),
            "recommendations": _clean_list(data.get("recommendations", []), limit=5),
            "source": "llm",
            "llm_note": "已使用 LLM 优化成长分析表达。",
        }
    except Exception as exc:
        fallback["source"] = "rule_based"
        fallback["llm_note"] = f"{LOCAL_FALLBACK_NOTE}原因：{exc}"
        return fallback


def _compact_projects(parsed_resume: Dict[str, Any], limit: int = 3) -> List[str]:
    projects = []
    for project in (parsed_resume or {}).get("projects", []) or []:
        if not isinstance(project, dict):
            continue
        parts = [
            project.get("name", ""),
            "、".join(str(x) for x in project.get("tech_stack", [])[:6]) if isinstance(project.get("tech_stack"), list) else "",
            "；".join(str(x) for x in project.get("responsibilities", [])[:2]) if isinstance(project.get("responsibilities"), list) else "",
            str(project.get("results", ""))[:120],
        ]
        text = "：".join(part for part in parts if part)
        if text:
            projects.append(text[:260])
        if len(projects) >= limit:
            break
    return projects


def polish_role_mismatch_with_llm(
    parsed_resume: Dict[str, Any],
    profile: Dict[str, Any],
    target_role: str,
    inferred_roles: List[str],
    rule_warning: str,
    rule_analysis: str,
    rule_suggestions: List[str],
    target_keywords: List[str],
) -> Dict[str, Any]:
    fallback = {
        "warning_title": "简历与目标岗位匹配提醒",
        "summary": rule_warning or rule_analysis,
        "analysis": _clean_list([rule_analysis] if rule_analysis else [], limit=3),
        "suggestions": _clean_list(rule_suggestions, limit=5),
        "severity": "high" if rule_warning else "low",
        "polished_by_llm": False,
        "fallback_reason": "disabled" if not is_llm_enabled() else "",
    }
    if not rule_warning:
        return fallback

    payload = {
        "selected_target_role": target_role,
        "resume_declared_target": " / ".join((parsed_resume or {}).get("target_roles", []) or []),
        "inferred_resume_roles": inferred_roles,
        "detected_skills": (profile or {}).get("detected_skills", [])[:16],
        "project_summaries": _compact_projects(parsed_resume),
        "rule_based_mismatch_reason": rule_warning,
        "rule_based_analysis": rule_analysis,
        "target_role_expected_keywords": target_keywords[:12],
        "required_output": {
            "warning_title": "简历与目标岗位匹配提醒",
            "summary": "一句话总结匹配情况",
            "analysis": ["具体分析1", "具体分析2", "具体分析3"],
            "suggestions": ["优化建议1", "优化建议2", "优化建议3"],
            "severity": "low / medium / high",
        },
    }
    try:
        data = _safe_json_chat(
            payload,
            "请润色简历与目标岗位不匹配提醒。要求中文、具体、克制，不阻止用户继续。",
            timeout=30,
        )
        summary = str(data.get("summary", "")).strip()
        if not summary:
            raise ValueError("empty_summary")
        severity = str(data.get("severity", "medium")).strip().lower()
        if severity not in {"low", "medium", "high"}:
            severity = "medium"
        return {
            "warning_title": str(data.get("warning_title") or "简历与目标岗位匹配提醒").strip(),
            "summary": summary,
            "analysis": _clean_list(data.get("analysis", []), limit=4),
            "suggestions": _clean_list(data.get("suggestions", []), limit=5),
            "severity": severity,
            "polished_by_llm": True,
            "fallback_reason": "",
        }
    except Exception as exc:
        fallback["fallback_reason"] = str(exc)
        return fallback


def polish_final_report_text_with_llm(report: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    polished_report = dict(report or {})
    if not is_llm_enabled():
        polished_report["report_text_polished_by_llm"] = False
        polished_report["report_text_polish_fallback_reason"] = "disabled"
        return polished_report

    payload = {
        "target_role": polished_report.get("target_role", ""),
        "difficulty": polished_report.get("difficulty", ""),
        "total_score": polished_report.get("total_score", 0),
        "level": polished_report.get("level", ""),
        "dimension_scores": polished_report.get("dimension_scores", {}),
        "dimension_details": polished_report.get("dimension_details", {}),
        "weak_points_summary": polished_report.get("weak_points_summary", []),
        "detected_skills": (profile or {}).get("detected_skills", [])[:16],
        "knowledge_ids": (polished_report.get("interview_summary", {}) or {}).get("knowledge_ids", []),
        "question_distribution": polished_report.get("question_distribution", {}),
        "answer_stability": polished_report.get("answer_stability", {}),
        "role_ability_coverage": polished_report.get("role_ability_coverage", {}),
        "weak_point_cards": polished_report.get("weak_point_cards", []),
        "role_mismatch_warning": polished_report.get("role_mismatch_warning", ""),
        "rule_based_strengths": polished_report.get("strengths", []),
        "rule_based_main_problems": polished_report.get("main_problems", []),
        "rule_based_recommendations": polished_report.get("recommendations", []),
        "rule_based_learning_recommendations": polished_report.get("learning_recommendations", []),
        "rule_based_resume_suggestions": polished_report.get("resume_optimization_suggestions", []),
        "required_output": {
            "strengths": ["..."],
            "main_problems": ["..."],
            "recommendations": ["..."],
            "weak_points_summary": ["..."],
            "learning_recommendations": ["..."],
            "resume_optimization_suggestions": ["..."],
            "question_distribution_summary": "...",
            "answer_stability_summary": "...",
            "role_ability_summary": "...",
            "covered_abilities": ["..."],
            "missing_or_weak_abilities": ["..."],
            "weak_point_cards": [
                {"title": "...", "evidence": "...", "suggestion": "..."}
            ],
            "role_aware_resume_advice": ["..."],
        },
    }
    try:
        data = _safe_json_chat(
            payload,
            "请只润色最终报告的文字反馈部分。不得修改分数、等级、权重、维度分、答题数量或知识点 ID。",
            timeout=120,
        )
        for key, limit in {
            "strengths": 5,
            "main_problems": 6,
            "recommendations": 6,
            "weak_points_summary": 8,
            "learning_recommendations": 6,
            "resume_optimization_suggestions": 6,
        }.items():
            cleaned = _clean_list(data.get(key, []), limit=limit)
            if cleaned:
                polished_report[key] = cleaned
        role_advice = _clean_list(data.get("role_aware_resume_advice", []), limit=6)
        if role_advice:
            polished_report["resume_optimization_suggestions"] = role_advice
        if data.get("question_distribution_summary") and polished_report.get("question_distribution"):
            polished_report["question_distribution"]["summary"] = str(data.get("question_distribution_summary")).strip()
            polished_report["question_distribution"]["polished_by_llm"] = True
        if data.get("answer_stability_summary") and polished_report.get("answer_stability"):
            polished_report["answer_stability"]["summary"] = str(data.get("answer_stability_summary")).strip()
            polished_report["answer_stability"]["polished_by_llm"] = True
        if data.get("role_ability_summary") and polished_report.get("role_ability_coverage"):
            polished_report["role_ability_coverage"]["summary"] = str(data.get("role_ability_summary")).strip()
            polished_report["role_ability_coverage"]["polished_by_llm"] = True
        if polished_report.get("role_ability_coverage"):
            covered = _clean_list(data.get("covered_abilities", []), limit=10)
            weak = _clean_list(data.get("missing_or_weak_abilities", []), limit=8)
            if covered:
                polished_report["role_ability_coverage"]["covered_abilities"] = covered
                polished_report["role_ability_coverage"]["polished_by_llm"] = True
            if weak:
                polished_report["role_ability_coverage"]["missing_or_weak_abilities"] = weak
                polished_report["role_ability_coverage"]["polished_by_llm"] = True
        cards = data.get("weak_point_cards", [])
        if isinstance(cards, list):
            cleaned_cards = []
            for card in cards[:6]:
                if not isinstance(card, dict):
                    continue
                cleaned_cards.append({
                    "title": str(card.get("title", "")).strip(),
                    "evidence": str(card.get("evidence", "")).strip(),
                    "suggestion": str(card.get("suggestion", "")).strip(),
                })
            cleaned_cards = [
                card for card in cleaned_cards
                if card["title"] or card["evidence"] or card["suggestion"]
            ]
            if cleaned_cards:
                polished_report["weak_point_cards"] = cleaned_cards
        polished_report["report_text_polished_by_llm"] = True
        polished_report["report_text_polish_fallback_reason"] = ""
        return polished_report
    except Exception as exc:
        polished_report["report_text_polished_by_llm"] = False
        polished_report["report_text_polish_fallback_reason"] = str(exc)
        return polished_report
