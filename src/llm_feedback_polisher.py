import json
from typing import Any, Dict, List

from src.llm_client import call_chat, extract_json_from_text, is_llm_enabled


LOCAL_FALLBACK_NOTE = "LLM 暂时不可用，已使用本地规则生成反馈内容。"


def _clean_list(value: Any, limit: int = 6) -> List[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()][:limit]


def _safe_json_chat(payload: Dict[str, Any], task: str, timeout: int = 35) -> Dict[str, Any]:
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
            timeout=120,
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
        polished_report["report_text_polished_by_llm"] = True
        polished_report["report_text_polish_fallback_reason"] = ""
        return polished_report
    except Exception as exc:
        polished_report["report_text_polished_by_llm"] = False
        polished_report["report_text_polish_fallback_reason"] = str(exc)
        return polished_report
