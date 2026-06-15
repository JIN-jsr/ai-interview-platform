from typing import Any, Dict, List

from src.resume_parser import extract_skills


def flatten_skills(parsed_resume: Dict[str, Any]) -> List[str]:
    skills_obj = parsed_resume.get("skills", {})
    if isinstance(skills_obj, dict):
        skills = []
        for value in skills_obj.values():
            if isinstance(value, list):
                skills.extend(value)
        return sorted(set(str(s) for s in skills if str(s).strip()))
    if isinstance(skills_obj, list):
        return sorted(set(str(s) for s in skills_obj if str(s).strip()))
    return []


def generate_profile_from_parsed_resume(
    parsed_resume: Dict[str, Any],
    target_role: str,
    difficulty: str
) -> Dict[str, Any]:
    skills = flatten_skills(parsed_resume)
    projects = parsed_resume.get("projects", [])
    focus = parsed_resume.get("interview_focus", [])

    if not focus:
        focus = []
        if any(skill in skills for skill in ["Python", "Java", "C++", "JavaScript"]):
            focus.append("编程语言基础与代码能力")
        if any(skill in skills for skill in ["MySQL", "PostgreSQL", "SQLite", "Redis", "MongoDB"]):
            focus.append("数据库设计、事务、索引与数据存储")
        if any(skill in skills for skill in ["Flask", "Django", "FastAPI", "Spring Boot"]):
            focus.append("后端框架、接口设计与项目工程化")
        if any(skill in skills for skill in ["机器学习", "深度学习", "PyTorch", "TensorFlow"]):
            focus.append("AI 模型原理、训练流程与评价指标")
        if not focus:
            focus = ["项目经历真实性", "基础知识掌握程度", "表达逻辑与岗位匹配度"]

    project_names = []
    for project in projects:
        if isinstance(project, dict) and project.get("name"):
            project_names.append(project["name"])

    return {
        "target_role": target_role,
        "difficulty": difficulty,
        "detected_skills": skills,
        "project_names": project_names,
        "candidate_profile": (
            f"该候选人目标岗位为{target_role}，简历中体现的主要技术包括："
            f"{'、'.join(skills) if skills else '暂未识别到明确技术栈'}。"
            "后续面试将围绕简历技术栈、项目经历和岗位匹配度展开。"
        ),
        "interview_focus": focus,
        "possible_weaknesses": parsed_resume.get("possible_weaknesses", []),
        "suggested_flow": [
            "自我介绍",
            "基础知识考察",
            "项目经历深挖",
            "综合追问",
            "评分反馈"
        ]
    }


def generate_basic_profile(resume_text: str, target_role: str, difficulty: str) -> Dict[str, Any]:
    """Backward-compatible Day 1 function."""
    skills = extract_skills(resume_text)
    parsed = {
        "skills": {"others": skills},
        "projects": [],
        "interview_focus": []
    }
    return generate_profile_from_parsed_resume(parsed, target_role, difficulty)
