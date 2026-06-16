import re
from typing import Any, Dict, List

from src.resume_parser import extract_skills


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
}


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


def role_keywords_for(target_role: str) -> List[str]:
    if "后端" in target_role:
        return ROLE_SKILL_KEYWORDS["后端"]
    if "AI" in target_role or "人工智能" in target_role:
        return ROLE_SKILL_KEYWORDS["AI"]
    if "前端" in target_role:
        return ROLE_SKILL_KEYWORDS["前端"]
    return []


def detect_role_skills(parsed_resume: Dict[str, Any], target_role: str) -> List[str]:
    resume_text = str(parsed_resume or "")
    detected = []
    for keyword in role_keywords_for(target_role):
        if term_in_text(keyword, resume_text):
            detected.append(keyword)
    return detected


def generate_profile_from_parsed_resume(
    parsed_resume: Dict[str, Any],
    target_role: str,
    difficulty: str
) -> Dict[str, Any]:
    skills = sorted(set(flatten_skills(parsed_resume) + detect_role_skills(parsed_resume, target_role)))
    projects = parsed_resume.get("projects", [])
    focus = parsed_resume.get("interview_focus", [])

    if not focus:
        focus = []
        if any(skill in skills for skill in ["Python", "Java", "C++", "JavaScript", "Go", "TypeScript"]):
            focus.append("编程语言基础与代码能力")
        if any(skill in skills for skill in ["MySQL", "PostgreSQL", "SQLite", "Redis", "MongoDB"]):
            focus.append("数据库设计、事务、索引与数据存储")
        if any(skill in skills for skill in ["Flask", "Django", "FastAPI", "Spring Boot", "Gin", "RabbitMQ", "Kafka", "RESTful API", "接口设计", "微服务"]):
            focus.append("后端框架、接口设计与项目工程化")
        if any(skill in skills for skill in ["机器学习", "深度学习", "PyTorch", "TensorFlow", "LLM", "RAG", "Embedding", "向量数据库", "Chroma", "LangChain"]):
            focus.append("AI 应用流程、RAG 检索与工程落地")
        if any(skill in skills for skill in ["Vue", "React", "TypeScript", "组件化", "状态管理"]):
            focus.append("前端组件化、状态管理与交互实现")
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
