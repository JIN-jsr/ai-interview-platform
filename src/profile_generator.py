from typing import Dict
from src.resume_parser import extract_skills


def generate_basic_profile(resume_text: str, target_role: str, difficulty: str) -> Dict:
    """Generate a simple profile for Day 1.

    Later this module should call an LLM and output a more accurate JSON profile.
    """
    skills = extract_skills(resume_text)

    interview_focus = []
    if any(skill in skills for skill in ["Python", "Java", "C++", "JavaScript"]):
        interview_focus.append("编程语言基础与代码能力")
    if any(skill in skills for skill in ["MySQL", "PostgreSQL", "SQLite", "Redis", "MongoDB"]):
        interview_focus.append("数据库设计、事务、索引与数据存储")
    if any(skill in skills for skill in ["Flask", "Django", "FastAPI", "Spring Boot"]):
        interview_focus.append("后端框架、接口设计与项目工程化")
    if any(skill in skills for skill in ["机器学习", "深度学习", "PyTorch", "TensorFlow"]):
        interview_focus.append("AI 模型原理、训练流程与评价指标")

    if not interview_focus:
        interview_focus = ["项目经历真实性", "基础知识掌握程度", "表达逻辑与岗位匹配度"]

    return {
        "target_role": target_role,
        "difficulty": difficulty,
        "detected_skills": skills,
        "candidate_profile": "该候选人具备一定计算机相关背景，后续面试将围绕简历技术栈和项目经历展开。",
        "interview_focus": interview_focus,
        "suggested_flow": [
            "自我介绍",
            "基础知识考察",
            "项目经历深挖",
            "综合追问",
            "评分反馈"
        ]
    }
