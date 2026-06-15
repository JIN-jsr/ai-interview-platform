import re
from typing import Dict, List


COMMON_SKILLS = [
    "Python", "Java", "C++", "C#", "JavaScript", "TypeScript",
    "HTML", "CSS", "React", "Vue", "Node.js",
    "Flask", "Django", "FastAPI", "Spring Boot",
    "MySQL", "PostgreSQL", "SQLite", "Redis", "MongoDB",
    "机器学习", "深度学习", "PyTorch", "TensorFlow",
    "数据结构", "算法", "计算机网络", "操作系统"
]


def extract_skills(text: str) -> List[str]:
    """Day 1 simple keyword-based skill extraction."""
    found = []
    lower_text = text.lower()
    for skill in COMMON_SKILLS:
        if skill.lower() in lower_text or skill in text:
            found.append(skill)
    return sorted(set(found))


def simple_resume_summary(text: str) -> Dict:
    """Create a simple local summary without LLM.

    This is only a Day 1 placeholder. Later it can be replaced by LLM-based
    structured resume parsing.
    """
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
