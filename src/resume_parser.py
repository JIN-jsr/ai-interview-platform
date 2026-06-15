import re
from typing import Any, Dict, List

from src.llm_client import call_chat, extract_json_from_text, is_llm_enabled
from src.prompts import RESUME_PARSE_SYSTEM_PROMPT, RESUME_PARSE_USER_PROMPT


COMMON_SKILLS = [
    "Python", "Java", "C++", "C#", "JavaScript", "TypeScript",
    "HTML", "CSS", "React", "Vue", "Node.js",
    "Flask", "Django", "FastAPI", "Spring Boot",
    "MySQL", "PostgreSQL", "SQLite", "Redis", "MongoDB",
    "Git", "Docker", "Linux", "RESTful API",
    "机器学习", "深度学习", "PyTorch", "TensorFlow", "NLP",
    "数据结构", "算法", "计算机网络", "操作系统"
]


def extract_skills(text: str) -> List[str]:
    """Simple keyword-based skill extraction."""
    found = []
    lower_text = text.lower()
    for skill in COMMON_SKILLS:
        if skill.lower() in lower_text or skill in text:
            found.append(skill)
    return sorted(set(found))


def guess_target_roles(skills: List[str]) -> List[str]:
    roles = []
    if any(s in skills for s in ["Flask", "Django", "FastAPI", "Spring Boot", "MySQL", "Redis"]):
        roles.append("后端开发")
    if any(s in skills for s in ["React", "Vue", "JavaScript", "TypeScript", "HTML", "CSS"]):
        roles.append("前端开发")
    if any(s in skills for s in ["机器学习", "深度学习", "PyTorch", "TensorFlow", "NLP"]):
        roles.append("AI应用开发")
    if any(s in skills for s in ["Python", "MySQL"]) and "AI应用开发" not in roles:
        roles.append("数据分析")
    return roles or ["软件开发"]


def build_interview_focus_from_skills(skills: List[str]) -> List[str]:
    focus = []
    if any(skill in skills for skill in ["Python", "Java", "C++", "JavaScript"]):
        focus.append("编程语言基础、面向对象、常见数据结构")
    if any(skill in skills for skill in ["MySQL", "PostgreSQL", "SQLite", "Redis", "MongoDB"]):
        focus.append("数据库设计、事务、索引、缓存与数据一致性")
    if any(skill in skills for skill in ["Flask", "Django", "FastAPI", "Spring Boot"]):
        focus.append("后端框架、接口设计、异常处理与部署")
    if any(skill in skills for skill in ["机器学习", "深度学习", "PyTorch", "TensorFlow"]):
        focus.append("模型结构、训练流程、评价指标与优化方法")
    if not focus:
        focus = ["项目经历真实性", "基础知识掌握程度", "表达逻辑与岗位匹配度"]
    return focus


def heuristic_resume_parse(text: str) -> Dict[str, Any]:
    """Fallback parser used when no LLM API is configured."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    skills = extract_skills(text)
    target_roles = guess_target_roles(skills)

    project_lines = [
        line for line in lines
        if any(keyword in line for keyword in ["项目", "Project", "project", "系统", "平台", "开发"])
    ]

    possible_name = ""
    for line in lines[:8]:
        if "姓名" in line:
            possible_name = re.sub(r"姓名[:：]", "", line).strip()
            break

    return {
        "basic_info": {
            "name": possible_name,
            "major": "计算机相关专业" if "计算机" in text else "",
            "school": "",
            "degree": "",
            "email": "",
            "phone": ""
        },
        "education": [],
        "skills": {
            "programming_languages": [s for s in skills if s in ["Python", "Java", "C++", "C#", "JavaScript", "TypeScript"]],
            "frameworks": [s for s in skills if s in ["Flask", "Django", "FastAPI", "Spring Boot", "React", "Vue", "Node.js"]],
            "databases": [s for s in skills if s in ["MySQL", "PostgreSQL", "SQLite", "Redis", "MongoDB"]],
            "tools": [s for s in skills if s in ["Git", "Docker", "Linux"]],
            "ai_ml": [s for s in skills if s in ["机器学习", "深度学习", "PyTorch", "TensorFlow", "NLP"]],
            "others": [s for s in skills if s in ["数据结构", "算法", "计算机网络", "操作系统", "RESTful API"]]
        },
        "projects": [
            {
                "name": "从简历文本中识别的项目经历",
                "background": "",
                "tech_stack": skills,
                "role": "",
                "responsibilities": project_lines[:3],
                "highlights": project_lines[3:6],
                "difficulties": [],
                "results": ""
            }
        ] if project_lines else [],
        "internships": [],
        "competitions": [],
        "certificates": [],
        "target_roles": target_roles,
        "resume_keywords": skills,
        "possible_weaknesses": [
            "部分项目职责和量化成果可能需要进一步补充",
            "需要在面试中验证技术细节掌握程度"
        ],
        "interview_focus": build_interview_focus_from_skills(skills)
    }


def parse_resume_with_llm(text: str) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": RESUME_PARSE_SYSTEM_PROMPT},
        {"role": "user", "content": RESUME_PARSE_USER_PROMPT.replace("{resume_text}", text[:12000])}
    ]
    content = call_chat(messages=messages, temperature=0.1)
    return extract_json_from_text(content)


def parse_resume(text: str, prefer_llm: bool = True) -> Dict[str, Any]:
    """Parse resume into a stable JSON schema."""
    if prefer_llm and is_llm_enabled():
        try:
            result = parse_resume_with_llm(text)
            result["_parser"] = "llm"
            return result
        except Exception as exc:
            fallback = heuristic_resume_parse(text)
            fallback["_parser"] = "heuristic_fallback"
            fallback["_llm_error"] = str(exc)
            return fallback

    result = heuristic_resume_parse(text)
    result["_parser"] = "heuristic"
    return result


def simple_resume_summary(text: str) -> Dict[str, Any]:
    """Backward-compatible summary for quick display."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    skills = extract_skills(text)
    project_lines = [
        line for line in lines
        if any(keyword in line for keyword in ["项目", "Project", "project", "系统", "平台"])
    ]
    return {
        "text_length": len(text),
        "line_count": len(lines),
        "detected_skills": skills,
        "possible_project_lines": project_lines[:5],
        "raw_preview": text[:300]
    }
