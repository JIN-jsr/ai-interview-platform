from datetime import datetime
import re
from typing import Any, Dict, List, Tuple

from src.llm_feedback_polisher import polish_final_report_text_with_llm
from src.product_features import generate_learning_recommendations, summarize_weak_points
from src.rag_display import attach_rag_display_fields


WEIGHTS = {
    "基础知识掌握程度": 0.25,
    "项目理解深度": 0.25,
    "回答逻辑性": 0.20,
    "表达完整性": 0.15,
    "岗位匹配度": 0.15
}


BASIC_TYPES = {"rag_basic", "rag_followup", "basic"}
PROJECT_TYPES = {"project", "project_followup"}

ROLE_SKILL_KEYWORDS = {
    "后端": [
        "Python", "Java", "Go", "Gin", "Flask", "FastAPI", "Spring Boot",
        "MySQL", "PostgreSQL", "Redis", "RabbitMQ", "Kafka", "RESTful API",
        "接口设计", "微服务", "高并发", "分布式锁", "幂等性", "限流", "熔断",
        "降级", "监控告警", "异步任务", "消息队列", "本地消息表", "Lua", "Lua 脚本",
        "布隆过滤器", "数据库事务", "索引优化", "缓存一致性", "部署", "Docker", "Kubernetes"
    ],
    "AI": [
        "LLM", "大语言模型", "大模型 API", "大模型API", "RAG", "Embedding",
        "向量数据库", "Chroma", "Milvus", "FAISS", "LangChain", "Prompt Engineering",
        "Function Calling", "Agent", "Rerank", "Token", "Token 管理", "上下文管理",
        "上下文压缩", "结构化输出", "模型评估", "AI 工程化", "Streamlit", "FastAPI",
        "模型调用", "检索增强生成"
    ],
    "前端": [
        "HTML", "CSS", "JavaScript", "TypeScript", "Vue", "React", "Element Plus",
        "前端工程化", "组件化", "状态管理", "响应式布局"
    ],
    "数据": ["SQL", "数据", "分析", "指标", "可视化", "统计", "报表"]
}


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def avg(values: List[float], default: float = 0) -> float:
    valid = [v for v in values if isinstance(v, (int, float))]
    if not valid:
        return default
    return sum(valid) / len(valid)


def get_records_by_type(records: List[Dict[str, Any]], types: set) -> List[Dict[str, Any]]:
    return [r for r in records if r.get("question_type") in types]


def _record_question_type(record: Dict[str, Any]) -> str:
    return str(record.get("question_type") or record.get("type") or "unknown")


QUESTION_TYPE_LABELS = {
    "intro": "自我介绍",
    "project": "项目问题",
    "project_followup": "项目追问",
    "rag_basic": "基础知识题",
    "rag_followup": "知识点追问",
    "basic": "基础题",
    "comprehensive": "综合问题",
    "end": "结束提示",
    "unknown": "未标注题型",
}


def question_type_label(question_type: str) -> str:
    return QUESTION_TYPE_LABELS.get(str(question_type or "unknown"), str(question_type or "未标注题型"))


def _role_text(profile: Dict[str, Any]) -> str:
    return str((profile or {}).get("target_role", ""))


def _display_record(record: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    return attach_rag_display_fields(record, _role_text(profile))


def build_question_distribution(records: List[Dict[str, Any]], profile: Dict[str, Any]) -> Dict[str, Any]:
    type_counts: Dict[str, int] = {}
    generated_counts = {"llm": 0, "rule_fallback": 0, "unknown": 0}
    for record in records or []:
        question_type = _record_question_type(record)
        type_counts[question_type] = type_counts.get(question_type, 0) + 1
        generated_by = str(record.get("generated_by") or "unknown")
        if generated_by not in generated_counts:
            generated_by = "unknown"
        generated_counts[generated_by] += 1

    basic_count = len(get_records_by_type(records, BASIC_TYPES))
    project_count = len(get_records_by_type(records, PROJECT_TYPES))
    summary = (
        f"本次共回答 {len(records or [])} 题，其中基础知识题 {basic_count} 题、项目深挖题 {project_count} 题。"
        f"LLM 生成 {generated_counts['llm']} 题，备用规则生成 {generated_counts['rule_fallback']} 题。"
    )
    return {
        "answer_count": len(records or []),
        "basic_question_count": basic_count,
        "project_question_count": project_count,
        "other_question_count": max(0, len(records or []) - basic_count - project_count),
        "difficulty": (profile or {}).get("difficulty", ""),
        "llm_question_count": generated_counts["llm"],
        "fallback_question_count": generated_counts["rule_fallback"],
        "unknown_generation_count": generated_counts["unknown"],
        "type_counts": type_counts,
        "summary": summary,
        "polished_by_llm": False,
    }


def build_answer_stability(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    ratios = [
        float((record.get("analysis") or {}).get("coverage_ratio", 0) or 0)
        for record in records or []
    ]
    average_coverage = round(avg(ratios, 0), 2) if ratios else 0
    high_count = len([ratio for ratio in ratios if ratio >= 0.7])
    low_count = len([ratio for ratio in ratios if ratio < 0.45])
    summary = (
        f"平均要点覆盖率为 {average_coverage:.2f}。"
        f"高覆盖回答 {high_count} 个，低覆盖回答 {low_count} 个。"
    )
    return {
        "summary": summary,
        "average_coverage": average_coverage,
        "high_coverage_count": high_count,
        "low_coverage_count": low_count,
        "polished_by_llm": False,
    }


def build_role_ability_coverage(
    records: List[Dict[str, Any]],
    profile: Dict[str, Any],
    dimension_scores: Dict[str, float],
) -> Dict[str, Any]:
    role_keywords = get_role_keywords(_role_text(profile))
    answer_text = "\n".join(
        " ".join([
            str(record.get("question", "")),
            str(record.get("user_answer", "")),
            str(record.get("display_topic", "")),
            str(record.get("display_category", "")),
            str(record.get("knowledge_id", "")),
        ])
        for record in records or []
    )
    covered = [kw for kw in role_keywords if term_in_text(kw, answer_text)]
    weak = [kw for kw in role_keywords if kw not in covered][:8]
    low_dimensions = [
        dim for dim, score in (dimension_scores or {}).items()
        if isinstance(score, (int, float)) and score < 75
    ][:3]
    if low_dimensions:
        weak.extend(low_dimensions)
    weak = list(dict.fromkeys(str(item) for item in weak if str(item).strip()))[:8]
    covered = list(dict.fromkeys(str(item) for item in covered if str(item).strip()))[:10]
    summary = (
        f"岗位相关能力已覆盖 {len(covered)} 项，仍建议重点补强 {len(weak)} 项。"
        if role_keywords else
        "当前岗位能力词库不足，建议结合目标岗位继续补充能力画像。"
    )
    return {
        "covered_abilities": covered,
        "missing_or_weak_abilities": weak,
        "summary": summary,
        "polished_by_llm": False,
    }


def build_weak_point_cards(records: List[Dict[str, Any]], weak_points: List[str], profile: Dict[str, Any]) -> List[Dict[str, str]]:
    cards = []
    for record in records or []:
        analysis = record.get("analysis") or {}
        missing = analysis.get("missing_points", []) or []
        coverage = float(analysis.get("coverage_ratio", 0) or 0)
        score = float(analysis.get("overall_temp_score", 0) or 0)
        if not missing and coverage >= 0.6 and score >= 6:
            continue
        display_record = _display_record(record, profile)
        title = display_record.get("display_topic") or display_record.get("display_id") or record.get("question_type") or "综合薄弱点"
        evidence = "、".join(str(item) for item in missing[:3]) if missing else f"覆盖率 {coverage:.2f}，临时评分 {score}/10"
        cards.append({
            "title": str(title),
            "evidence": str(evidence),
            "suggestion": "建议按“定义-原理-场景-项目案例”补全回答，并主动说明边界条件和验证方式。",
        })
        if len(cards) >= 6:
            break
    if not cards:
        for item in (weak_points or [])[:3]:
            cards.append({
                "title": "综合提升点",
                "evidence": str(item),
                "suggestion": "建议继续用真实项目案例支撑技术判断，避免只停留在概念层面。",
            })
    return cards[:6]


def ensure_report_auxiliary_sections(
    report: Dict[str, Any],
    records: List[Dict[str, Any]],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    """Backfill report sections added after older reports were generated."""
    if not report:
        return report

    patched = dict(report)
    dimension_scores = patched.get("dimension_scores", {}) or {}
    weak_points = patched.get("weak_points_summary", []) or summarize_weak_points(records, dimension_scores)
    record_count = len(records or [])

    stability = patched.get("answer_stability", {}) or {}
    distribution = patched.get("question_distribution", {}) or {}
    ability = patched.get("role_ability_coverage", {}) or {}

    if not stability or (record_count and not stability.get("average_coverage") and not stability.get("high_coverage_count") and not stability.get("low_coverage_count")):
        patched["answer_stability"] = build_answer_stability(records)
    if not distribution or (record_count and not distribution.get("answer_count")):
        patched["question_distribution"] = build_question_distribution(records, profile)
    if not ability or (record_count and not ability.get("covered_abilities") and not ability.get("missing_or_weak_abilities")):
        patched["role_ability_coverage"] = build_role_ability_coverage(records, profile, dimension_scores)
    if not patched.get("weak_point_cards"):
        patched["weak_point_cards"] = build_weak_point_cards(records, weak_points, profile)

    summary = dict(patched.get("interview_summary", {}) or {})
    distribution = patched.get("question_distribution", {}) or {}
    if records and not summary.get("answer_count"):
        summary["answer_count"] = len(records)
    if records and not summary.get("basic_question_count"):
        summary["basic_question_count"] = len(get_records_by_type(records, BASIC_TYPES))
    if records and not summary.get("project_question_count"):
        summary["project_question_count"] = len(get_records_by_type(records, PROJECT_TYPES))
    if not summary.get("knowledge_display_ids"):
        summary["knowledge_display_ids"] = [
            (_display_record(r, profile).get("display_id") or r.get("knowledge_id"))
            for r in records or [] if r.get("knowledge_id")
        ]
    if not summary.get("knowledge_ids"):
        summary["knowledge_ids"] = [r.get("knowledge_id") for r in records or [] if r.get("knowledge_id")]
    if distribution and not summary.get("answer_count"):
        summary["answer_count"] = distribution.get("answer_count", 0)
    patched["interview_summary"] = summary
    return patched


def normalize_match_text(text: str) -> str:
    return str(text or "").lower().replace(" ", "").replace("_", "").replace("-", "")


def term_in_text(term: str, text: str) -> bool:
    normalized_term = str(term or "").lower().strip()
    normalized_text = str(text or "").lower()
    if not normalized_term:
        return False
    if re.search(r"[\u4e00-\u9fff]", normalized_term):
        return normalize_match_text(term) in normalize_match_text(text)
    if re.fullmatch(r"[a-z0-9+#.]+", normalized_term):
        return re.search(rf"(?<![a-z0-9+#.]){re.escape(normalized_term)}(?![a-z0-9+#.])", normalized_text) is not None
    return normalize_match_text(term) in normalize_match_text(text)


def get_role_keywords(target_role: str) -> List[str]:
    if "后端" in target_role:
        return ROLE_SKILL_KEYWORDS["后端"]
    if "AI" in target_role or "人工智能" in target_role:
        return ROLE_SKILL_KEYWORDS["AI"]
    if "前端" in target_role:
        return ROLE_SKILL_KEYWORDS["前端"]
    if "数据" in target_role:
        return ROLE_SKILL_KEYWORDS["数据"]
    return []


def score_basic_knowledge(records: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    basic_records = get_records_by_type(records, BASIC_TYPES)
    evidence = []

    if not basic_records:
        return 55.0, ["基础知识题数量不足，系统按保守分数处理。"]

    technical_scores = []
    coverage_scores = []
    for record in basic_records:
        analysis = record.get("analysis", {})
        technical_scores.append(analysis.get("technical_score", 0) * 10)
        coverage_scores.append(analysis.get("coverage_ratio", 0) * 100)

        missing = analysis.get("missing_points", [])
        if missing:
            evidence.append(
                f"题目“{record.get('question', '')[:35]}...”中缺少关键点：{'、'.join(missing[:3])}"
            )
        else:
            evidence.append(
                f"题目“{record.get('question', '')[:35]}...”回答覆盖度较好。"
            )

    score = avg(technical_scores) * 0.6 + avg(coverage_scores) * 0.4
    return clamp(round(score, 1)), evidence[:4]


def score_project_depth(records: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    project_records = get_records_by_type(records, PROJECT_TYPES)
    evidence = []

    if not project_records:
        return 55.0, ["项目深挖题数量不足，系统按保守分数处理。"]

    temp_scores = []
    detail_bonus = []
    for record in project_records:
        answer = record.get("user_answer", "")
        analysis = record.get("analysis", {})
        temp_scores.append(analysis.get("overall_temp_score", 0) * 10)

        has_role = any(x in answer for x in ["负责", "我做", "我的职责", "个人职责", "实现"])
        has_difficulty = any(x in answer for x in ["难点", "问题", "挑战", "瓶颈", "解决"])
        has_result = any(x in answer for x in ["结果", "提升", "降低", "完成", "实现", "优化"])
        bonus = 50 + 15 * has_role + 20 * has_difficulty + 15 * has_result
        detail_bonus.append(bonus)

        missing_parts = []
        if not has_role:
            missing_parts.append("个人职责")
        if not has_difficulty:
            missing_parts.append("技术难点")
        if not has_result:
            missing_parts.append("项目结果")
        if missing_parts:
            evidence.append(f"项目回答还可补充：{'、'.join(missing_parts)}。")
        else:
            evidence.append("项目回答包含职责、难点和结果，完整度较好。")

    score = avg(temp_scores) * 0.5 + avg(detail_bonus) * 0.5
    return clamp(round(score, 1)), evidence[:4]


def score_logic(records: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    if not records:
        return 50.0, ["暂无回答记录，无法充分评估回答逻辑性。"]

    logic_scores = [r.get("analysis", {}).get("logic_score", 0) * 10 for r in records]
    evidence = []

    weak_count = 0
    for r in records:
        analysis = r.get("analysis", {})
        if analysis.get("logic_score", 0) < 6:
            weak_count += 1

    if weak_count:
        evidence.append(f"共有 {weak_count} 个回答结构不够明显，建议使用“背景—问题—方案—结果”结构。")
    else:
        evidence.append("多数回答具有较清晰的逻辑连接词或分层表达。")

    return clamp(round(avg(logic_scores), 1)), evidence


def score_completeness(records: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    if not records:
        return 50.0, ["暂无回答记录，无法充分评估表达完整性。"]

    length_scores = [r.get("analysis", {}).get("length_score", 0) * 10 for r in records]
    coverage_scores = [r.get("analysis", {}).get("coverage_ratio", 0) * 100 for r in records]

    short_answers = [
        r for r in records
        if r.get("analysis", {}).get("answer_length", 0) < 50
    ]

    evidence = []
    if short_answers:
        evidence.append(f"共有 {len(short_answers)} 个回答偏短，信息量不足。")
    else:
        evidence.append("大多数回答长度较充分，能够展开说明。")

    score = avg(length_scores) * 0.7 + avg(coverage_scores, 60) * 0.3
    return clamp(round(score, 1)), evidence


def score_job_match(records: List[Dict[str, Any]], profile: Dict[str, Any]) -> Tuple[float, List[str]]:
    target_role = profile.get("target_role", "")
    skills = set(str(s) for s in profile.get("detected_skills", []) if str(s).strip())

    answer_text = "\n".join(r.get("user_answer", "") for r in records)
    mentioned_skills = [skill for skill in skills if skill and term_in_text(skill, answer_text)]
    role_keywords = get_role_keywords(target_role)
    matched_role_keywords = [kw for kw in role_keywords if term_in_text(kw, answer_text)]

    base = 60
    if skills:
        base += min(25, len(mentioned_skills) / max(1, len(skills)) * 25)

    role_bonus = min(15, len(matched_role_keywords) * 2.5)

    score = clamp(base + role_bonus)

    evidence = [
        f"目标岗位：{target_role or '未明确'}。",
        f"简历识别技能数：{len(skills)}；回答中主动提到的简历技能数：{len(mentioned_skills)}。"
    ]
    if mentioned_skills:
        evidence.append(f"回答中体现的相关技能：{'、'.join(mentioned_skills[:8])}。")
    if matched_role_keywords:
        evidence.append(f"回答中体现的岗位关键词：{'、'.join(matched_role_keywords[:10])}。")
    else:
        evidence.append("回答中对目标岗位关键词的主动关联较少，岗位匹配度展示不足。")

    return round(score, 1), evidence


def level_from_score(score: float) -> str:
    if score >= 90:
        return "优秀"
    if score >= 80:
        return "良好"
    if score >= 70:
        return "中等"
    if score >= 60:
        return "及格"
    return "需要加强"


def collect_common_problems(records: List[Dict[str, Any]]) -> List[str]:
    counter: Dict[str, int] = {}
    for r in records:
        for p in r.get("analysis", {}).get("problems", []):
            counter[p] = counter.get(p, 0) + 1

    ranked = sorted(counter.items(), key=lambda x: x[1], reverse=True)
    return [f"{p}（出现 {n} 次）" for p, n in ranked[:6]]


def collect_recommendations(records: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[str]:
    recommendations = []

    common_problems = collect_common_problems(records)
    if common_problems:
        recommendations.append("针对高频问题进行专项改进：" + "；".join(common_problems[:3]) + "。")

    target_role = profile.get("target_role", "")
    if "后端" in target_role:
        recommendations.append("后端方向建议重点复习：接口设计、数据库事务与索引、Redis 缓存一致性、消息队列、幂等性、限流降级和部署。")
    elif "AI" in target_role or "人工智能" in target_role:
        recommendations.append("AI 应用方向建议重点补充：LLM API 调用、RAG 检索流程、Embedding、向量数据库、Prompt Engineering、结构化输出和工程落地。")
    elif "前端" in target_role:
        recommendations.append("前端方向建议重点补充：组件化、状态管理、接口联调、浏览器机制和页面性能优化。")
    else:
        recommendations.append("建议结合目标岗位整理 3-5 个高频技术点，并准备项目中的真实应用案例。")

    recommendations.append("项目类回答建议采用 STAR 或“背景—问题—方案—结果”结构，并补充量化成果。")
    recommendations.append("基础知识回答建议从定义、原理、优缺点、项目应用四个角度展开。")
    return recommendations


def build_final_report(records: List[Dict[str, Any]], profile: Dict[str, Any]) -> Dict[str, Any]:
    basic_score, basic_evidence = score_basic_knowledge(records)
    project_score, project_evidence = score_project_depth(records)
    logic_score, logic_evidence = score_logic(records)
    completeness_score, completeness_evidence = score_completeness(records)
    match_score, match_evidence = score_job_match(records, profile)

    dimension_scores = {
        "基础知识掌握程度": basic_score,
        "项目理解深度": project_score,
        "回答逻辑性": logic_score,
        "表达完整性": completeness_score,
        "岗位匹配度": match_score
    }

    weighted_total = sum(dimension_scores[k] * WEIGHTS[k] for k in WEIGHTS)
    weighted_total = round(weighted_total, 1)

    strengths = []
    if basic_score >= 75:
        strengths.append("基础知识回答具有一定覆盖度，能够联系部分技术概念。")
    if project_score >= 75:
        strengths.append("项目经历表达较具体，能够说明个人职责或技术难点。")
    if logic_score >= 75:
        strengths.append("回答逻辑较清晰，能够使用一定结构组织内容。")
    if match_score >= 75:
        strengths.append("回答内容与目标岗位有较明显关联。")
    if not strengths:
        strengths.append("候选人能够完成完整模拟面试流程，具备继续提升的基础。")

    weak_points_summary = summarize_weak_points(records, dimension_scores)
    answer_stability = build_answer_stability(records)
    question_distribution = build_question_distribution(records, profile)
    role_ability_coverage = build_role_ability_coverage(records, profile, dimension_scores)
    weak_point_cards = build_weak_point_cards(records, weak_points_summary, profile)
    learning_recommendations = generate_learning_recommendations(
        target_role=profile.get("target_role", ""),
        dimension_scores=dimension_scores,
        weak_points=weak_points_summary,
        detected_skills=profile.get("detected_skills", [])
    )
    role_mismatch_warning = profile.get("role_mismatch_warning", "")
    role_mismatch_detail = profile.get("role_mismatch_detail", {})
    resume_optimization_suggestions = profile.get("resume_optimization_suggestions", [])
    is_incomplete_interview = bool(profile.get("is_incomplete_interview", False))
    incomplete_report_warning = profile.get("incomplete_report_warning", "")

    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target_role": profile.get("target_role", ""),
        "difficulty": profile.get("difficulty", ""),
        "total_score": weighted_total,
        "level": level_from_score(weighted_total),
        "weights": WEIGHTS,
        "dimension_scores": dimension_scores,
        "is_incomplete_interview": is_incomplete_interview,
        "incomplete_report_warning": incomplete_report_warning if is_incomplete_interview else "",
        "dimension_details": {
            "基础知识掌握程度": {
                "score": basic_score,
                "weight": "25%",
                "evidence": basic_evidence
            },
            "项目理解深度": {
                "score": project_score,
                "weight": "25%",
                "evidence": project_evidence
            },
            "回答逻辑性": {
                "score": logic_score,
                "weight": "20%",
                "evidence": logic_evidence
            },
            "表达完整性": {
                "score": completeness_score,
                "weight": "15%",
                "evidence": completeness_evidence
            },
            "岗位匹配度": {
                "score": match_score,
                "weight": "15%",
                "evidence": match_evidence
            }
        },
        "strengths": strengths,
        "main_problems": collect_common_problems(records) or ["暂无明显高频问题，但建议继续增加回答细节和技术深度。"],
        "recommendations": collect_recommendations(records, profile),
        "role_mismatch_warning": role_mismatch_warning,
        "role_mismatch_detail": role_mismatch_detail,
        "resume_optimization_suggestions": resume_optimization_suggestions,
        "weak_points_summary": weak_points_summary,
        "weak_point_cards": weak_point_cards,
        "learning_recommendations": learning_recommendations,
        "answer_stability": answer_stability,
        "question_distribution": question_distribution,
        "role_ability_coverage": role_ability_coverage,
        "interview_summary": {
            "answer_count": len(records),
            "basic_question_count": len(get_records_by_type(records, BASIC_TYPES)),
            "project_question_count": len(get_records_by_type(records, PROJECT_TYPES)),
            "knowledge_ids": [r.get("knowledge_id") for r in records if r.get("knowledge_id")],
            "knowledge_display_ids": [
                (_display_record(r, profile).get("display_id") or r.get("knowledge_id"))
                for r in records if r.get("knowledge_id")
            ],
        }
    }
    return polish_final_report_text_with_llm(report, profile)


def report_to_markdown(report: Dict[str, Any]) -> str:
    lines = []
    lines.append("# AI 模拟面试评分报告")
    lines.append("")
    lines.append(f"生成时间：{report.get('generated_at', '')}")
    lines.append(f"目标岗位：{report.get('target_role', '')}")
    lines.append(f"总分：**{report.get('total_score')} / 100**")
    lines.append(f"等级：**{report.get('level')}**")
    lines.append("")
    if report.get("is_incomplete_interview"):
        lines.append("> " + (report.get("incomplete_report_warning") or "本次面试尚未完整完成，当前评分报告仅供阶段性参考。"))
        lines.append("")
    summary = report.get("interview_summary", {}) or {}
    distribution = report.get("question_distribution", {}) or {}
    stability = report.get("answer_stability", {}) or {}
    ability = report.get("role_ability_coverage", {}) or {}

    lines.append("## 本次面试概览")
    lines.append("")
    lines.append(f"- 目标岗位：{report.get('target_role', '') or '未明确'}")
    lines.append(f"- 难度：{report.get('difficulty', '') or '未明确'}")
    lines.append(f"- 答题数量：{summary.get('answer_count', 0)}")
    lines.append(f"- 基础知识题：{summary.get('basic_question_count', 0)}")
    lines.append(f"- 项目深挖题：{summary.get('project_question_count', 0)}")
    lines.append(f"- 总分与等级：{report.get('total_score')} / 100，{report.get('level')}")
    lines.append("")

    lines.append("## 问题难度与类型分布")
    lines.append("")
    lines.append(f"- {distribution.get('summary', '暂无问题分布摘要。')}")
    lines.append(f"- LLM 生成题数：{distribution.get('llm_question_count', 0)}")
    lines.append(f"- 备用规则题数：{distribution.get('fallback_question_count', 0)}")
    for question_type, count in (distribution.get("type_counts", {}) or {}).items():
        lines.append(f"- {question_type_label(question_type)}：{count} 题")
    lines.append("")

    lines.append("## 回答稳定性分析")
    lines.append("")
    lines.append(f"- {stability.get('summary', '暂无回答稳定性摘要。')}")
    lines.append(f"- 平均覆盖率：{stability.get('average_coverage', 0)}")
    lines.append(f"- 高覆盖回答：{stability.get('high_coverage_count', 0)}")
    lines.append(f"- 低覆盖回答：{stability.get('low_coverage_count', 0)}")
    lines.append("")

    lines.append("## 岗位能力覆盖图")
    lines.append("")
    lines.append(f"- {ability.get('summary', '暂无岗位能力覆盖摘要。')}")
    covered = ability.get("covered_abilities", []) or []
    weak = ability.get("missing_or_weak_abilities", []) or []
    lines.append(f"- 已覆盖能力：{'、'.join(covered) if covered else '暂无明显覆盖'}")
    lines.append(f"- 待补强能力：{'、'.join(weak) if weak else '暂无明显薄弱项'}")
    lines.append("")

    lines.append("## 五维度评分")
    lines.append("")
    lines.append("| 维度 | 权重 | 分数 |")
    lines.append("|---|---:|---:|")
    for dim, detail in report.get("dimension_details", {}).items():
        lines.append(f"| {dim} | {detail.get('weight')} | {detail.get('score')} |")
    lines.append("")
    lines.append("## 评分依据")
    lines.append("")
    for dim, detail in report.get("dimension_details", {}).items():
        lines.append(f"### {dim}")
        for ev in detail.get("evidence", []):
            lines.append(f"- {ev}")
        lines.append("")
    lines.append("## 表现较好的方面")
    for item in report.get("strengths", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 主要问题")
    for item in report.get("main_problems", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 简历与岗位匹配建议")
    mismatch = report.get("role_mismatch_warning", "")
    suggestions = report.get("resume_optimization_suggestions", [])
    if mismatch:
        lines.append(f"- {mismatch}")
    if suggestions:
        for item in suggestions[:5]:
            lines.append(f"- {item}")
    if not mismatch and not suggestions:
        lines.append("- 本次未发现明显简历与岗位方向冲突，建议继续强化与目标岗位相关的项目表达。")
    lines.append("")
    lines.append("## 错题与薄弱知识点总结")
    for card in report.get("weak_point_cards", []) or []:
        title = card.get("title", "薄弱点")
        evidence = card.get("evidence", "")
        suggestion = card.get("suggestion", "")
        lines.append(f"- **{title}**：{evidence}；建议：{suggestion}")
    for item in report.get("weak_points_summary", []) or ["本次面试暂无明显薄弱知识点，建议继续提升回答深度和项目案例表达。"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 学习建议推荐")
    for item in report.get("learning_recommendations", []) or ["建议围绕目标岗位持续复盘基础知识、项目表达和回答结构。"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 后续提升建议")
    for item in report.get("recommendations", []):
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)
