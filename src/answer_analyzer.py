import re
from typing import Any, Dict, List


TECH_KEYWORDS = [
    "Python", "Java", "C++", "JavaScript", "Flask", "Django", "FastAPI", "Spring Boot",
    "MySQL", "Redis", "MongoDB", "SQLite", "PostgreSQL", "索引", "事务", "缓存",
    "HTTP", "HTTPS", "TCP", "UDP", "进程", "线程", "锁", "数据库", "接口",
    "机器学习", "深度学习", "PyTorch", "TensorFlow", "RAG", "API", "Git", "Docker"
]

LOGIC_MARKERS = [
    "首先", "其次", "然后", "最后", "因为", "所以", "例如", "比如",
    "一方面", "另一方面", "因此", "总结", "结果", "目标", "问题", "方案"
]


def normalize_text(text: str) -> str:
    return str(text or "").lower().replace("＋", "+").replace("＃", "#")


def extract_keywords(text: str) -> List[str]:
    found = []
    lower_text = normalize_text(text)
    for kw in TECH_KEYWORDS:
        if kw.lower() in lower_text or kw in text:
            found.append(kw)
    return sorted(set(found))


def split_reference_points(reference_answer: str, tags: List[str]) -> List[str]:
    """Extract lightweight reference points from reference answer and tags."""
    points = []

    for tag in tags or []:
        if tag and len(str(tag).strip()) >= 2:
            points.append(str(tag).strip())

    if reference_answer:
        parts = re.split(r"[，。；;、,.\s]+", reference_answer)
        for part in parts:
            part = part.strip()
            if len(part) >= 2 and len(part) <= 12:
                points.append(part)

    seen = set()
    result = []
    for p in points:
        key = normalize_text(p)
        if key not in seen:
            result.append(p)
            seen.add(key)
    return result[:12]


def calculate_coverage(answer: str, reference_points: List[str]) -> Dict[str, Any]:
    lower_answer = normalize_text(answer)
    covered = []
    missing = []

    for point in reference_points:
        point_norm = normalize_text(point)
        if point_norm and point_norm in lower_answer:
            covered.append(point)
        else:
            missing.append(point)

    if not reference_points:
        ratio = 0.0
    else:
        ratio = len(covered) / len(reference_points)

    return {
        "covered_points": covered,
        "missing_points": missing[:6],
        "coverage_ratio": round(ratio, 2)
    }


def analyze_answer(question_meta: Dict[str, Any], user_answer: str) -> Dict[str, Any]:
    """Analyze one user answer with simple, explainable rules.

    This is not the final scoring module. It is used in Day 4 to support
    continuous follow-up and context-aware interview flow.
    """
    answer = user_answer.strip()
    answer_len = len(answer)
    keywords = extract_keywords(answer)

    reference_answer = question_meta.get("reference_answer", "")
    tags = question_meta.get("tags", [])
    reference_points = split_reference_points(reference_answer, tags)
    coverage = calculate_coverage(answer, reference_points)

    logic_count = sum(1 for marker in LOGIC_MARKERS if marker in answer)
    has_example = any(marker in answer for marker in ["例如", "比如", "项目中", "实际", "场景"])
    has_result = any(marker in answer for marker in ["结果", "提升", "降低", "完成", "实现", "优化"])

    length_score = min(10, max(2, answer_len // 18))
    logic_score = min(10, 4 + logic_count * 2 + (1 if has_example else 0) + (1 if has_result else 0))
    technical_score = min(10, 3 + len(keywords) + int(coverage["coverage_ratio"] * 5))

    if answer_len < 30:
        overall = min(5, (length_score + logic_score + technical_score) // 3)
    else:
        overall = round(length_score * 0.3 + logic_score * 0.3 + technical_score * 0.4, 1)

    problems = []
    suggestions = []

    if answer_len < 50:
        problems.append("回答偏短，信息量不足")
        suggestions.append("补充背景、具体做法和结果，避免只给概念定义")
    if logic_count == 0:
        problems.append("回答结构不够明显")
        suggestions.append("可以使用“背景—问题—方案—结果”的结构回答")
    if question_meta.get("type") == "rag_basic" and coverage["coverage_ratio"] < 0.35:
        problems.append("基础知识关键点覆盖不足")
        suggestions.append("围绕定义、原理、应用场景和优缺点补充回答")
    if question_meta.get("type") == "project" and not has_result:
        problems.append("项目回答缺少结果或效果描述")
        suggestions.append("补充项目成果、性能提升、用户价值或个人贡献")

    needs_followup = (
        answer_len < 70
        or coverage["coverage_ratio"] < 0.35
        or question_meta.get("type") in {"project", "rag_basic"}
    )

    return {
        "answer_length": answer_len,
        "detected_keywords": keywords,
        "covered_points": coverage["covered_points"],
        "missing_points": coverage["missing_points"],
        "coverage_ratio": coverage["coverage_ratio"],
        "length_score": length_score,
        "logic_score": logic_score,
        "technical_score": technical_score,
        "overall_temp_score": overall,
        "problems": problems,
        "suggestions": suggestions,
        "needs_followup": needs_followup
    }


def summarize_interview_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not records:
        return {
            "total_answers": 0,
            "average_temp_score": 0,
            "frequent_keywords": [],
            "common_problems": []
        }

    scores = []
    keyword_counter = {}
    problem_counter = {}

    for record in records:
        analysis = record.get("analysis", {})
        score = analysis.get("overall_temp_score")
        if isinstance(score, (int, float)):
            scores.append(score)

        for kw in analysis.get("detected_keywords", []):
            keyword_counter[kw] = keyword_counter.get(kw, 0) + 1

        for problem in analysis.get("problems", []):
            problem_counter[problem] = problem_counter.get(problem, 0) + 1

    frequent_keywords = sorted(keyword_counter.items(), key=lambda x: x[1], reverse=True)[:8]
    common_problems = sorted(problem_counter.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_answers": len(records),
        "average_temp_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "frequent_keywords": frequent_keywords,
        "common_problems": common_problems
    }
