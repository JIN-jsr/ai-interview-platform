from typing import Any, Dict, List

from src.rag_retriever import retrieve_by_profile


def build_project_question(profile: Dict[str, Any], question_count: int) -> str:
    projects = profile.get("project_names", [])
    project_hint = projects[0] if projects else "你简历中最重要的一个项目"

    if question_count == 1:
        return f"请详细介绍一下「{project_hint}」，包括项目背景、你的职责和使用的核心技术。"
    if question_count == 2:
        return f"在「{project_hint}」中，你遇到的最大技术难点是什么？你是如何分析和解决的？"
    return f"如果让你重新优化「{project_hint}」，你会从架构、性能或用户体验中的哪个方面改进？为什么？"


def build_rag_question(item: Dict[str, Any], index: int) -> str:
    tags = "、".join(item.get("tags", []))
    question = item.get("question", "请解释一个相关基础知识点。")
    followups = item.get("follow_up", [])

    if index == 0:
        prefix = "下面进入基础知识考察。"
    else:
        prefix = "继续考察一个相关基础知识点。"

    followup_text = ""
    if followups:
        followup_text = f" 回答后我可能会继续追问：{followups[0]}"

    return f"{prefix}这个问题与你简历中的技术栈相关（{tags}）：{question}{followup_text}"


def get_next_question(
    profile: Dict[str, Any],
    history: List[Dict[str, str]],
    rag_items: List[Dict[str, Any]],
    rag_index: int
) -> Dict[str, Any]:
    """Return next interview question with simple state control.

    Assistant question count controls the stage:
    1 intro already asked
    2-3 project deep dive
    4-6 RAG basic knowledge
    7 comprehensive question
    """
    assistant_count = len([m for m in history if m.get("role") == "assistant"])

    if assistant_count == 0:
        return {
            "question": "你好，我是今天的 AI 技术面试官。请你先用 1 分钟做一个简短的自我介绍，重点说明你的技术栈、项目经历以及目标岗位。",
            "type": "intro",
            "rag_index": rag_index
        }

    if assistant_count in [1, 2]:
        return {
            "question": build_project_question(profile, assistant_count),
            "type": "project",
            "rag_index": rag_index
        }

    if assistant_count in [3, 4, 5]:
        if rag_index < len(rag_items):
            item = rag_items[rag_index]
            return {
                "question": build_rag_question(item, rag_index),
                "type": "rag_basic",
                "knowledge_id": item.get("id"),
                "reference_answer": item.get("answer"),
                "rag_index": rag_index + 1
            }
        return {
            "question": "接下来考察基础知识。请你选择一个简历中写到的技术点，说明它的核心原理和项目应用场景。",
            "type": "basic",
            "rag_index": rag_index
        }

    if assistant_count == 6:
        role = profile.get("target_role", "目标岗位")
        return {
            "question": f"最后一个综合问题：你认为自己为什么适合{role}？请结合项目经历、技术能力和后续学习计划回答。",
            "type": "comprehensive",
            "rag_index": rag_index
        }

    return {
        "question": "本轮 Day 3 面试流程已结束。Day 4 将继续增强连续追问和上下文控制，Day 5 会加入正式评分反馈。",
        "type": "end",
        "rag_index": rag_index
    }


def prepare_rag_items_for_interview(profile: Dict[str, Any], top_k: int = 6) -> List[Dict[str, Any]]:
    return retrieve_by_profile(profile, top_k=top_k)
