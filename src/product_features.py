from collections import Counter
from datetime import datetime
from typing import Any, Dict, List


ROLE_KEYWORDS = {
    "后端开发": [
        "Java", "Spring", "Spring Boot", "Flask", "FastAPI", "Go", "Gin",
        "MySQL", "Redis", "Kafka", "RabbitMQ", "接口", "高并发", "分布式",
        "缓存", "数据库", "API", "Docker", "Linux"
    ],
    "AI应用开发": [
        "LLM", "大模型", "RAG", "Embedding", "向量数据库", "Prompt",
        "LangChain", "Streamlit", "模型调用", "结构化输出", "Agent",
        "Function Calling", "Rerank", "Token"
    ],
    "数据分析": [
        "SQL", "Pandas", "NumPy", "Excel", "Tableau", "Power BI", "数据清洗",
        "指标体系", "可视化", "A/B测试", "统计分析", "留存分析", "漏斗分析", "报表"
    ],
    "前端开发": [
        "HTML", "CSS", "JavaScript", "TypeScript", "Vue", "React",
        "组件化", "状态管理", "响应式布局"
    ],
    "软件测试": [
        "测试用例", "自动化测试", "pytest", "接口测试", "性能测试", "缺陷管理"
    ],
}


DIMENSION_RECOMMENDATIONS = {
    "基础知识掌握程度": "建议复习核心知识点的定义、原理、适用场景和常见追问。",
    "项目理解深度": "建议补充项目背景、个人职责、技术难点、方案取舍和量化结果。",
    "回答逻辑性": "建议使用总分总、STAR 或“背景-问题-方案-结果”结构表达。",
    "表达完整性": "建议回答时主动补充边界条件、异常场景、指标和项目案例。",
    "岗位匹配度": "建议围绕目标岗位整理关键词，并在回答中主动关联相关技能。"
}


def _flatten_values(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(_flatten_values(item))
        return result
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(_flatten_values(item))
        return result
    return [str(value)]


def _text_blob(*values: Any) -> str:
    return "\n".join(_flatten_values(list(values)))


def infer_resume_roles(parsed_resume: Dict[str, Any], profile: Dict[str, Any] = None) -> List[str]:
    text = _text_blob(parsed_resume, profile)
    explicit_roles = []
    for role in parsed_resume.get("target_roles", []) if isinstance(parsed_resume, dict) else []:
        role_text = str(role).strip()
        if role_text:
            explicit_roles.append(role_text)

    scores = {}
    for role, keywords in ROLE_KEYWORDS.items():
        score = 0
        compact_text = text.lower().replace(" ", "")
        for keyword in keywords:
            key = str(keyword).lower().replace(" ", "")
            if key and key in compact_text:
                score += 1
        if score:
            scores[role] = score

    inferred = [role for role, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:2]]
    merged = []
    for role in explicit_roles + inferred:
        normalized = normalize_role(role)
        if normalized and normalized not in merged:
            merged.append(normalized)
    return merged


def normalize_role(role: str) -> str:
    role = str(role or "").replace(" ", "")
    if "后端" in role:
        return "后端开发"
    if "AI" in role or "人工智能" in role or "大模型" in role:
        return "AI应用开发"
    if "数据" in role or "分析" in role:
        return "数据分析"
    if "前端" in role:
        return "前端开发"
    if "测试" in role:
        return "软件测试"
    return role


def detect_role_mismatch(parsed_resume: Dict[str, Any], profile: Dict[str, Any], target_role: str) -> Dict[str, Any]:
    selected = normalize_role(target_role)
    inferred_roles = infer_resume_roles(parsed_resume or {}, profile or {})
    if not inferred_roles or selected in inferred_roles:
        return {"warning": "", "inferred_roles": inferred_roles}
    role_text = " / ".join(inferred_roles[:2])
    warning = (
        f"检测到当前简历内容更偏向“{role_text}”，但当前选择岗位为“{selected}”。"
        f"系统将优先按照当前目标岗位出题，并结合简历中的可迁移技能进行追问。"
    )
    return {"warning": warning, "inferred_roles": inferred_roles}


def generate_resume_optimization_suggestions(
    parsed_resume: Dict[str, Any],
    profile: Dict[str, Any],
    target_role: str,
    mismatch_warning: str = ""
) -> List[str]:
    role = normalize_role(target_role)
    detected_skills = set(str(skill) for skill in (profile or {}).get("detected_skills", []))
    projects = (parsed_resume or {}).get("projects", [])
    text = _text_blob(parsed_resume, profile)
    suggestions = []

    if mismatch_warning:
        suggestions.append(mismatch_warning)

    target_keywords = ROLE_KEYWORDS.get(role, [])
    missing_keywords = [kw for kw in target_keywords if kw not in detected_skills and kw.lower() not in text.lower()]
    if missing_keywords:
        suggestions.append(f"岗位匹配度：如果目标岗位为{role}，建议补充或突出：{'、'.join(missing_keywords[:8])}。")
    else:
        suggestions.append(f"岗位匹配度：简历中的关键词与{role}已有一定匹配，建议在项目描述中继续强化应用场景。")

    if detected_skills:
        suggestions.append("技术栈表达：建议把核心技术按“熟悉程度 + 使用场景 + 项目成果”展开，而不只是罗列关键词。")
    else:
        suggestions.append("技术栈表达：建议补充编程语言、框架、数据库、工具链等明确技能关键词。")

    if projects:
        suggestions.append("项目经历表达：建议每个项目补充背景、个人职责、技术难点、解决方案和最终结果。")
    else:
        suggestions.append("项目经历表达：当前项目经历不够明显，建议补充 1-2 个与目标岗位相关的项目案例。")

    if not any(word in text for word in ["负责", "我实现", "我设计", "主导", "个人职责"]):
        suggestions.append("个人职责清晰度：建议明确写出自己负责的模块、具体动作和技术决策。")

    if not any(word in text.lower() for word in ["qps", "rt", "提升", "降低", "用户", "%", "ms", "秒", "准确率"]):
        suggestions.append("量化成果：建议补充性能、准确率、效率、用户规模或业务指标等量化结果。")

    suggestions.append(f"可补充关键词：{'、'.join(target_keywords[:10]) if target_keywords else '结合目标岗位补充高频技能关键词'}。")
    return suggestions[:8]


def summarize_weak_points(records: List[Dict[str, Any]], dimension_scores: Dict[str, float] = None) -> List[str]:
    weak_items = []
    category_counter = Counter()
    for record in records or []:
        analysis = record.get("analysis", {})
        coverage = float(analysis.get("coverage_ratio", 1) or 0)
        score = float(analysis.get("overall_temp_score", 10) or 0)
        missing = analysis.get("missing_points", [])
        category = record.get("question_type") or record.get("knowledge_id") or "综合问题"
        if coverage < 0.6 or missing or score < 6:
            category_counter[category] += 1
            topic = record.get("knowledge_id") or record.get("question_type") or "综合问题"
            if missing:
                weak_items.append(f"{topic}：回答缺少 {'、'.join(str(p) for p in missing[:3])}。")
            else:
                weak_items.append(f"{topic}：回答覆盖度或临时评分偏低，建议补充原理、场景和项目案例。")

    for dim, score in (dimension_scores or {}).items():
        try:
            if float(score) < 80:
                weak_items.append(f"{dim}：当前得分 {score}，建议进行专项提升。")
        except Exception:
            continue

    if not weak_items:
        return ["本次面试暂无明显薄弱知识点，建议继续提升回答深度和项目案例表达。"]
    return list(dict.fromkeys(weak_items))[:8]


def generate_learning_recommendations(
    target_role: str,
    dimension_scores: Dict[str, float] = None,
    weak_points: List[str] = None,
    detected_skills: List[str] = None
) -> List[str]:
    role = normalize_role(target_role)
    recommendations = []
    if role == "后端开发":
        recommendations.append("建议重点复习 MySQL 索引、事务隔离、Redis 缓存一致性、接口幂等性和分布式故障恢复。")
    elif role == "AI应用开发":
        recommendations.append("建议重点补充 RAG 检索流程、Embedding、向量数据库、Prompt 结构化输出、模型评估和上下文管理。")
    elif role == "数据分析":
        recommendations.append("建议重点准备 SQL 聚合与窗口函数、指标体系设计、数据清洗、可视化表达、A/B 测试和业务分析案例。")
    elif role == "前端开发":
        recommendations.append("建议重点复习组件化、状态管理、接口联调、浏览器机制、性能优化和响应式布局。")
    else:
        recommendations.append("建议围绕目标岗位整理 3-5 个高频知识点，并准备对应项目案例。")

    for dim, text in DIMENSION_RECOMMENDATIONS.items():
        try:
            if float((dimension_scores or {}).get(dim, 100)) < 80:
                recommendations.append(text)
        except Exception:
            continue

    if weak_points:
        recommendations.append("针对本次暴露的薄弱点，建议用“定义-原理-适用场景-项目应用”四步法复盘。")
    return list(dict.fromkeys(recommendations))[:6]


def analyze_growth_reports(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    if len(reports) < 2:
        return {"summary": "请至少选择两条已生成报告的面试记录。", "recommendations": []}

    sorted_reports = sorted(reports, key=lambda item: item.get("generated_at", ""))
    first = float(sorted_reports[0].get("total_score", 0) or 0)
    last = float(sorted_reports[-1].get("total_score", 0) or 0)
    delta = round(last - first, 1)

    dims = sorted_reports[-1].get("dimension_scores", {})
    lowest_dim = ""
    if dims:
        lowest_dim = min(dims.items(), key=lambda item: float(item[1] or 0))[0]

    improvements = {}
    first_dims = sorted_reports[0].get("dimension_scores", {})
    last_dims = sorted_reports[-1].get("dimension_scores", {})
    for dim, value in last_dims.items():
        improvements[dim] = float(value or 0) - float(first_dims.get(dim, value) or 0)
    fastest = max(improvements.items(), key=lambda item: item[1])[0] if improvements else ""

    direction = "提升" if delta >= 0 else "下降"
    summary = (
        f"所选记录中，总分整体{direction} {abs(delta)} 分。"
        f"{'提升最快的是' + fastest + '。' if fastest else ''}"
        f"{'当前相对薄弱的是' + lowest_dim + '。' if lowest_dim else ''}"
    )
    recommendations = []
    if lowest_dim:
        recommendations.append(DIMENSION_RECOMMENDATIONS.get(lowest_dim, "建议继续围绕目标岗位进行专项练习。"))
    recommendations.append("建议只选择真实有效的完整面试记录进行趋势分析，避免测试会话影响判断。")
    return {"summary": summary, "recommendations": recommendations}


def format_report_time(value: str) -> str:
    try:
        return datetime.strptime(str(value)[:19], "%Y-%m-%d %H:%M:%S").strftime("%m-%d %H:%M")
    except Exception:
        return str(value or "")[:16]
