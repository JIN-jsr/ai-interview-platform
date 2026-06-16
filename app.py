import json
from datetime import datetime
import streamlit.components.v1 as components

import streamlit as st

from src.answer_analyzer import analyze_answer, summarize_interview_records
from src.evaluator import build_final_report, report_to_markdown
from src.interviewer import get_next_question, prepare_rag_items_for_interview
from pathlib import Path

from src.llm_client import get_llm_config, get_masked_api_key, is_llm_enabled, test_llm_connection
from src.profile_generator import generate_profile_from_parsed_resume
from src.rag_retriever import get_kb_stats, retrieve_by_profile, retrieve_by_query
from src.resume_file_loader import load_resume_files
from src.resume_parser import parse_resume, simple_resume_summary
from src.session_manager import (
    create_new_session,
    delete_session,
    generate_session_title,
    list_sessions,
    load_session,
    rename_session,
    save_session,
)

st.set_page_config(
    page_title="AI Mock Interview Platform",
    page_icon="🎙️",
    layout="wide"
)

st.title("AI 模拟面试与能力提升平台")
st.caption("简历驱动 + RAG 知识库 + LLM 连续追问 + 五维度评分反馈")
st.markdown(
    """
    面向计算机相关专业学生的 AI 模拟技术面试训练平台。系统根据简历生成候选人画像，
    结合本地 RAG 知识库和可选 LLM 生成面试问题，记录回答过程并输出可下载的评分报告。
    """
)
st.code("简历输入 -> 用户画像 -> RAG 检索 -> 连续面试 -> 回答分析 -> 评分报告", language="text")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "uploaded_file_names" not in st.session_state:
    st.session_state.uploaded_file_names = []
if "extracted_file_text" not in st.session_state:
    st.session_state.extracted_file_text = ""
if "parsed_resume" not in st.session_state:
    st.session_state.parsed_resume = None
if "profile" not in st.session_state:
    st.session_state.profile = None
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "rag_items" not in st.session_state:
    st.session_state.rag_items = []
if "rag_index" not in st.session_state:
    st.session_state.rag_index = 0
if "question_meta" not in st.session_state:
    st.session_state.question_meta = []
if "current_question_meta" not in st.session_state:
    st.session_state.current_question_meta = None
if "interview_records" not in st.session_state:
    st.session_state.interview_records = []
if "followup_count" not in st.session_state:
    st.session_state.followup_count = 0
if "final_report" not in st.session_state:
    st.session_state.final_report = None
if "report_markdown" not in st.session_state:
    st.session_state.report_markdown = ""
if "report_json" not in st.session_state:
    st.session_state.report_json = ""
if "used_knowledge_ids" not in st.session_state:
    st.session_state.used_knowledge_ids = []
if "used_categories" not in st.session_state:
    st.session_state.used_categories = []
if "scroll_to_latest" not in st.session_state:
    st.session_state.scroll_to_latest = False
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "current_session_title" not in st.session_state:
    st.session_state.current_session_title = "未保存的新面试"
if "current_session_created_at" not in st.session_state:
    st.session_state.current_session_created_at = None
if "session_save_warning" not in st.session_state:
    st.session_state.session_save_warning = ""
if "session_load_warning" not in st.session_state:
    st.session_state.session_load_warning = ""
if "selected_target_role" not in st.session_state:
    st.session_state.selected_target_role = "后端开发"
if "selected_difficulty" not in st.session_state:
    st.session_state.selected_difficulty = "中等"
if "new_session_target_role" not in st.session_state:
    st.session_state.new_session_target_role = st.session_state.selected_target_role
if "new_session_difficulty" not in st.session_state:
    st.session_state.new_session_difficulty = st.session_state.selected_difficulty
if "edit_latest_answer_text" not in st.session_state:
    st.session_state.edit_latest_answer_text = ""
if "pending_new_session" not in st.session_state:
    st.session_state.pending_new_session = False
if "pending_new_session_role" not in st.session_state:
    st.session_state.pending_new_session_role = None
if "pending_new_session_difficulty" not in st.session_state:
    st.session_state.pending_new_session_difficulty = None
if "pending_load_session_id" not in st.session_state:
    st.session_state.pending_load_session_id = None
if "pending_delete_session_id" not in st.session_state:
    st.session_state.pending_delete_session_id = None


DEMO_DIR = Path("demo")
SAMPLE_RESUMES = {
    "AI 应用开发示例": DEMO_DIR / "sample_resume_ai_app.txt",
    "后端开发示例": DEMO_DIR / "sample_resume_backend.txt",
}


def reset_interview_state():
    st.session_state.messages = []
    st.session_state.interview_started = False
    st.session_state.rag_index = 0
    st.session_state.question_meta = []
    st.session_state.current_question_meta = None
    st.session_state.interview_records = []
    st.session_state.followup_count = 0
    st.session_state.final_report = None
    st.session_state.report_markdown = ""
    st.session_state.report_json = ""
    st.session_state.used_knowledge_ids = []
    st.session_state.used_categories = []
    st.session_state.edit_latest_answer_text = ""


def clear_report_state():
    st.session_state.final_report = None
    st.session_state.report_markdown = ""
    st.session_state.report_json = ""


def reset_all_state():
    reset_interview_state()
    st.session_state.resume_text = ""
    st.session_state.uploaded_file_names = []
    st.session_state.extracted_file_text = ""
    st.session_state.parsed_resume = None
    st.session_state.profile = None
    st.session_state.rag_items = []


def build_combined_resume_text(manual_text, uploaded_text):
    parts = []
    manual = (manual_text or "").strip()
    uploaded = (uploaded_text or "").strip()
    if manual:
        parts.append(f"===== 手动输入内容 =====\n{manual}")
    if uploaded:
        parts.append(f"===== 上传文件内容 =====\n{uploaded}")
    return "\n\n".join(parts).strip()


def infer_session_status(status=None):
    if status:
        return status
    if st.session_state.final_report:
        return "completed"
    if st.session_state.interview_started or st.session_state.interview_records:
        return "interviewing"
    if st.session_state.profile or st.session_state.parsed_resume:
        return "resume_ready"
    return "created"


def build_session_payload(status=None):
    session_id = st.session_state.current_session_id
    title = st.session_state.current_session_title
    target_role = st.session_state.selected_target_role
    difficulty = st.session_state.selected_difficulty
    if not title or title == "未保存的新面试":
        title = generate_session_title(target_role, difficulty)
    return {
        "session_id": session_id,
        "title": title,
        "created_at": st.session_state.current_session_created_at,
        "target_role": target_role,
        "difficulty": difficulty,
        "resume_text": st.session_state.resume_text,
        "uploaded_file_names": st.session_state.uploaded_file_names,
        "extracted_file_text": st.session_state.extracted_file_text,
        "parsed_resume": st.session_state.parsed_resume,
        "profile": st.session_state.profile,
        "rag_items": st.session_state.rag_items,
        "rag_index": st.session_state.rag_index,
        "messages": st.session_state.messages,
        "question_meta": st.session_state.question_meta,
        "current_question_meta": st.session_state.current_question_meta,
        "interview_records": st.session_state.interview_records,
        "followup_count": st.session_state.followup_count,
        "used_knowledge_ids": st.session_state.used_knowledge_ids,
        "used_categories": st.session_state.used_categories,
        "final_report": st.session_state.final_report,
        "report_markdown": st.session_state.report_markdown,
        "report_json": st.session_state.report_json,
        "interview_started": st.session_state.interview_started,
        "status": infer_session_status(status),
    }


def restore_session_state(session_data):
    st.session_state.current_session_id = session_data.get("session_id")
    st.session_state.current_session_title = session_data.get("title") or "未命名面试"
    st.session_state.current_session_created_at = session_data.get("created_at")
    st.session_state.selected_target_role = session_data.get("target_role") or "后端开发"
    st.session_state.selected_difficulty = session_data.get("difficulty") or "中等"
    st.session_state.resume_text = session_data.get("resume_text", "")
    st.session_state.uploaded_file_names = session_data.get("uploaded_file_names", [])
    st.session_state.extracted_file_text = session_data.get("extracted_file_text", "")
    st.session_state.parsed_resume = session_data.get("parsed_resume")
    st.session_state.profile = session_data.get("profile")
    st.session_state.rag_items = session_data.get("rag_items", [])
    st.session_state.rag_index = session_data.get("rag_index", 0)
    st.session_state.messages = session_data.get("messages", [])
    st.session_state.question_meta = session_data.get("question_meta", [])
    st.session_state.current_question_meta = session_data.get("current_question_meta")
    st.session_state.interview_records = session_data.get("interview_records", [])
    st.session_state.followup_count = session_data.get("followup_count", 0)
    st.session_state.used_knowledge_ids = session_data.get("used_knowledge_ids", [])
    st.session_state.used_categories = session_data.get("used_categories", [])
    st.session_state.final_report = session_data.get("final_report")
    st.session_state.report_markdown = session_data.get("report_markdown", "")
    st.session_state.report_json = session_data.get("report_json", "")
    st.session_state.interview_started = session_data.get("interview_started", bool(st.session_state.messages))
    st.session_state.edit_latest_answer_text = ""


def create_blank_current_session(target_role=None, difficulty=None):
    new_session = create_new_session(
        target_role=target_role or st.session_state.get("selected_target_role", "后端开发"),
        difficulty=difficulty or st.session_state.get("selected_difficulty", "中等"),
    )
    reset_all_state()
    restore_session_state(new_session)


def apply_pending_session_actions():
    if st.session_state.pending_delete_session_id:
        session_id = st.session_state.pending_delete_session_id
        st.session_state.pending_delete_session_id = None
        try:
            delete_session(session_id)
            sessions, _ = list_sessions()
            if st.session_state.current_session_id == session_id:
                if sessions:
                    session_data = load_session(sessions[0]["session_id"])
                    if session_data:
                        restore_session_state(session_data)
                    else:
                        create_blank_current_session()
                else:
                    create_blank_current_session()
            st.session_state.session_load_warning = ""
        except Exception as exc:
            st.session_state.session_load_warning = f"删除面试记录失败：{exc}"

    if st.session_state.pending_new_session:
        st.session_state.pending_new_session = False
        target_role = st.session_state.pending_new_session_role
        difficulty = st.session_state.pending_new_session_difficulty
        st.session_state.pending_new_session_role = None
        st.session_state.pending_new_session_difficulty = None
        try:
            create_blank_current_session(target_role=target_role, difficulty=difficulty)
        except Exception as exc:
            reset_all_state()
            st.session_state.current_session_id = None
            st.session_state.current_session_title = "未保存的新面试"
            st.session_state.session_save_warning = f"面试记录保存失败，但当前面试仍可继续。原因：{exc}"

    if st.session_state.pending_load_session_id:
        session_id = st.session_state.pending_load_session_id
        st.session_state.pending_load_session_id = None
        try:
            session_data = load_session(session_id)
            if session_data:
                restore_session_state(session_data)
                st.session_state.session_load_warning = ""
            else:
                st.session_state.session_load_warning = "面试记录读取失败，请选择其他记录。"
        except Exception as exc:
            st.session_state.session_load_warning = f"面试记录读取失败：{exc}"


def autosave_current_session(status=None):
    try:
        payload = build_session_payload(status=status)
        if not payload.get("session_id"):
            new_session = create_new_session(
                target_role=payload.get("target_role", ""),
                difficulty=payload.get("difficulty", ""),
                title=payload.get("title"),
            )
            payload["session_id"] = new_session["session_id"]
        saved = save_session(payload)
        st.session_state.current_session_id = saved.get("session_id")
        st.session_state.current_session_title = saved.get("title", st.session_state.current_session_title)
        st.session_state.current_session_created_at = saved.get("created_at")
        st.session_state.session_save_warning = ""
        return True
    except Exception as exc:
        st.session_state.session_save_warning = f"面试记录保存失败，但当前面试仍可继续。原因：{exc}"
        return False


def load_demo_resume(sample_name):
    sample_path = SAMPLE_RESUMES.get(sample_name)
    if not sample_path or not sample_path.exists():
        st.warning(f"未找到示例简历：{sample_name}")
        return
    st.session_state.resume_text = sample_path.read_text(encoding="utf-8")
    st.session_state.uploaded_file_names = []
    st.session_state.extracted_file_text = ""
    st.session_state.parsed_resume = None
    st.session_state.profile = None
    st.session_state.rag_items = []
    reset_interview_state()
    st.success(f"已加载{sample_name}，请点击“解析简历并生成画像”。")
    autosave_current_session()


def render_question_metadata(meta):
    if not meta:
        st.info("当前还没有题目元数据。开始面试后会显示。")
        return

    generated_by = meta.get("generated_by", "unknown")
    generated_label = "LLM 生成" if generated_by == "llm" else "备用机制" if generated_by == "rule_fallback" else generated_by
    meta_cols = st.columns(4)
    meta_cols[0].metric("题型", meta.get("type") or meta.get("question_type") or "unknown")
    meta_cols[1].metric("生成方式", generated_label)
    meta_cols[2].metric("难度", meta.get("difficulty", "未标注"))
    meta_cols[3].metric("知识点", meta.get("knowledge_id") or "无")
    if generated_by == "llm":
        st.success("LLM 生成成功")

    with st.expander("预期回答要点", expanded=False):
        points = meta.get("expected_points", [])
        if points:
            for point in points:
                st.write(f"- {point}")
        else:
            st.caption("当前题目没有提供预期回答要点。")

    with st.expander("出题依据", expanded=False):
        st.write(meta.get("reason") or "暂无出题依据。")
        if generated_by == "rule_fallback" and meta.get("fallback_reason"):
            st.warning(meta.get("fallback_reason"))

    with st.expander("原始问题元数据", expanded=False):
        st.json(meta)


def render_assistant_question_details(meta):
    if not meta:
        return
    with st.expander("问题详情", expanded=False):
        render_question_metadata(meta)


def scroll_to_latest_message():
    components.html(
        """
        <script>
        const target =
            window.parent.document.getElementById("processing-anchor") ||
            window.parent.document.getElementById("latest-message-anchor") ||
            window.parent.document.querySelector('[data-testid="stChatInput"]');
        if (target) {
            target.scrollIntoView({behavior: "smooth", block: "end"});
        }
        </script>
        """,
        height=0,
    )


def build_interview_record(question_meta, user_answer, analysis):
    generated_by = question_meta.get("generated_by", "rule_fallback")
    return {
        "question": question_meta.get("question", ""),
        "question_type": question_meta.get("type", "unknown"),
        "knowledge_id": question_meta.get("knowledge_id", ""),
        "reference_answer": question_meta.get("reference_answer", ""),
        "expected_points": question_meta.get("expected_points", []),
        "related_project_scenarios": question_meta.get("related_project_scenarios", []),
        "reason": question_meta.get("reason", ""),
        "generated_by": generated_by,
        "fallback_reason": question_meta.get("fallback_reason", "") if generated_by == "rule_fallback" else "",
        "difficulty": question_meta.get("difficulty", st.session_state.profile.get("difficulty", "") if st.session_state.profile else ""),
        "difficulty_reason": question_meta.get("difficulty_reason", ""),
        "used_knowledge_ids": list(st.session_state.used_knowledge_ids),
        "used_categories": list(st.session_state.used_categories),
        "user_answer": user_answer,
        "analysis": analysis,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def latest_user_message_index():
    for idx in range(len(st.session_state.messages) - 1, -1, -1):
        if st.session_state.messages[idx].get("role") == "user":
            return idx
    return None


def assistant_count_before(message_index):
    return len([
        message for message in st.session_state.messages[:message_index]
        if message.get("role") == "assistant"
    ])


def rebuild_question_usage():
    used_ids = []
    used_categories = []
    for meta in st.session_state.question_meta:
        knowledge_id = (meta or {}).get("knowledge_id")
        category = (meta or {}).get("category")
        if knowledge_id and knowledge_id not in used_ids:
            used_ids.append(knowledge_id)
        if category:
            used_categories.append(category)
    st.session_state.used_knowledge_ids = used_ids
    st.session_state.used_categories = used_categories


def edit_latest_answer_and_regenerate(edited_answer):
    edited_answer = (edited_answer or "").strip()
    if not edited_answer:
        st.warning("修改后的回答不能为空。")
        return False
    if not st.session_state.interview_records:
        st.warning("还没有可修改的回答。")
        return False

    user_idx = latest_user_message_index()
    if user_idx is None:
        st.warning("没有找到上一条回答。")
        return False

    answered_question_count = assistant_count_before(user_idx)
    if answered_question_count <= 0:
        st.warning("没有找到这条回答对应的问题。")
        return False

    answered_meta = None
    if answered_question_count - 1 < len(st.session_state.question_meta):
        answered_meta = st.session_state.question_meta[answered_question_count - 1]
    if not answered_meta:
        st.warning("问题信息不完整，无法重新发送。")
        return False

    st.session_state.messages[user_idx]["content"] = edited_answer
    st.session_state.messages = st.session_state.messages[:user_idx + 1]
    st.session_state.question_meta = st.session_state.question_meta[:answered_question_count]
    st.session_state.current_question_meta = answered_meta
    st.session_state.interview_records = st.session_state.interview_records[:-1]
    clear_report_state()
    st.session_state.rag_index = answered_meta.get("rag_index", st.session_state.rag_index)
    st.session_state.followup_count = answered_meta.get("followup_count", st.session_state.followup_count)
    rebuild_question_usage()

    with st.spinner("正在根据修改后的回答重新生成下一题，请稍候..."):
        analysis = analyze_answer(answered_meta, edited_answer)
        st.session_state.interview_records.append(
            build_interview_record(answered_meta, edited_answer, analysis)
        )
        next_info = get_next_question(
            profile=st.session_state.profile or {},
            history=st.session_state.messages,
            rag_items=st.session_state.rag_items,
            rag_index=st.session_state.rag_index,
            last_answer=edited_answer,
            last_question_meta=answered_meta,
            last_analysis=analysis,
            followup_count=st.session_state.followup_count,
            used_knowledge_ids=st.session_state.used_knowledge_ids,
            used_categories=st.session_state.used_categories
        )

    st.session_state.rag_index = next_info.get("rag_index", st.session_state.rag_index)
    st.session_state.followup_count = next_info.get("followup_count", st.session_state.followup_count)
    st.session_state.messages.append({"role": "assistant", "content": next_info["question"]})
    st.session_state.current_question_meta = next_info
    st.session_state.question_meta.append(next_info)
    register_question_usage(next_info)
    st.session_state.edit_latest_answer_text = ""
    autosave_current_session()
    st.session_state.scroll_to_latest = True
    return True


def render_latest_answer_editor(disabled=False, answer_text=None, key_suffix=""):
    latest_answer = answer_text
    if latest_answer is None and st.session_state.interview_records:
        latest_answer = st.session_state.interview_records[-1].get("user_answer", "")
    with st.expander("修改回答", expanded=False):
        edited_answer = st.text_area(
            "编辑并重新发送，系统会替换旧回答并重新生成下一题。",
            value=latest_answer or "",
            height=150,
            key=f"edit_latest_answer_text_{key_suffix}",
            disabled=disabled,
        )
        if disabled:
            st.info("当前正在生成下一题，请稍候。")
        elif st.button("重新发送", key=f"resend_latest_answer_{key_suffix}"):
            if edit_latest_answer_and_regenerate(edited_answer):
                st.rerun()


def register_question_usage(question_meta):
    knowledge_id = (question_meta or {}).get("knowledge_id")
    category = (question_meta or {}).get("category")
    if knowledge_id and knowledge_id not in st.session_state.used_knowledge_ids:
        st.session_state.used_knowledge_ids.append(knowledge_id)
    if category:
        st.session_state.used_categories.append(category)


apply_pending_session_actions()

with st.sidebar:
    st.header("面试记录")
    st.caption(f"当前：{st.session_state.current_session_title}")

    with st.expander("＋ 新建面试", expanded=False):
        st.selectbox(
            "目标岗位",
            ["后端开发", "前端开发", "AI应用开发", "数据分析", "软件测试"],
            key="new_session_target_role",
        )
        st.selectbox(
            "面试难度",
            ["基础", "中等", "困难"],
            key="new_session_difficulty",
        )
        if st.button("创建新面试", use_container_width=True):
            st.session_state.pending_new_session = True
            st.session_state.pending_new_session_role = st.session_state.new_session_target_role
            st.session_state.pending_new_session_difficulty = st.session_state.new_session_difficulty
            st.rerun()

    st.divider()

    try:
        sessions, session_warnings = list_sessions()
    except Exception as exc:
        sessions, session_warnings = [], [f"历史面试读取失败：{exc}"]
    if not sessions:
        st.caption("暂无历史面试。")
    for item in sessions[:12]:
        session_id = item.get("session_id", "")
        title = item.get("title") or "未命名面试"
        updated_at = item.get("updated_at", "")
        display_time = updated_at[11:16] if len(updated_at) >= 16 else updated_at
        status_label = item.get("status") or "created"
        is_current = session_id == st.session_state.current_session_id
        st.caption(display_time or "未记录时间")
        button_label = f"{title}｜{status_label}{'｜当前' if is_current else ''}"
        if st.button(button_label, key=f"load_session_{session_id}", use_container_width=True):
            st.session_state.pending_load_session_id = session_id
            st.rerun()
        with st.expander("⋯", expanded=False):
            new_title = st.text_input("重命名", value=title, key=f"rename_title_{session_id}")
            if st.button("保存名称", key=f"save_rename_{session_id}"):
                try:
                    renamed = rename_session(session_id, new_title)
                    if renamed and session_id == st.session_state.current_session_id:
                        st.session_state.current_session_title = renamed.get("title", new_title)
                    st.rerun()
                except Exception as exc:
                    st.warning(f"重命名失败：{exc}")
            if st.button("删除此面试", key=f"delete_session_{session_id}"):
                st.session_state.pending_delete_session_id = session_id
                st.rerun()

    if st.session_state.session_save_warning:
        st.warning(st.session_state.session_save_warning)
    if st.session_state.session_load_warning:
        st.warning(st.session_state.session_load_warning)
    if session_warnings:
        with st.expander("部分历史面试无法读取", expanded=False):
            for item in session_warnings:
                st.write(f"- {item}")

    with st.expander("演示辅助工具", expanded=False):
        sample_choice = st.selectbox("示例简历", list(SAMPLE_RESUMES.keys()))
        if st.button("加载示例简历"):
            load_demo_resume(sample_choice)
            st.rerun()
        if st.button("重置当前面试"):
            reset_interview_state()
            autosave_current_session()
            st.rerun()
        if st.button("清空全部记录"):
            reset_all_state()
            autosave_current_session()
            st.rerun()
        st.caption("“重置当前面试”会保留简历画像；“清空全部记录”会清空简历、画像、面试和报告。")

target_role = st.session_state.selected_target_role
difficulty = st.session_state.selected_difficulty
config = get_llm_config()
kb_stats = get_kb_stats()
assistant_count = len([m for m in st.session_state.messages if m.get("role") == "assistant"])
current_status = infer_session_status()

with st.expander("当前面试信息", expanded=False):
    info_cols = st.columns(5)
    info_cols[0].metric("目标岗位", target_role)
    info_cols[1].metric("难度", difficulty)
    info_cols[2].metric("状态", current_status)
    info_cols[3].metric("已回答", len(st.session_state.interview_records))
    info_cols[4].metric("报告", "已生成" if st.session_state.final_report else "未生成")

    detail_cols = st.columns(4)
    detail_cols[0].write(f"**当前轮次：** {assistant_count}")
    detail_cols[1].write(f"**上下文追问：** {st.session_state.followup_count}")
    detail_cols[2].write(f"**已用知识点：** {len(st.session_state.used_knowledge_ids)}")
    detail_cols[3].write(f"**RAG 条目：** {kb_stats['total_entries']}")
    if is_llm_enabled():
        st.success(f"LLM 已启用：{config['model_name']}")
    else:
        st.warning("LLM 未启用，系统将使用备用出题机制。")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1. 简历输入与解析",
    "2. RAG 知识库",
    "3. 模拟面试",
    "4. 面试记录与分析",
    "5. 评分报告",
    "6. 项目说明与运行检查"
])

with tab1:
    st.subheader("输入或上传简历")

    uploaded_files = st.file_uploader(
        "上传简历或项目材料，可多选 TXT / PDF / DOCX",
        type=["txt", "pdf", "docx"],
        accept_multiple_files=True,
        key=f"resume_upload_{st.session_state.current_session_id or 'draft'}",
    )

    if uploaded_files:
        uploaded_text, uploaded_names, upload_warnings = load_resume_files(uploaded_files)
        st.session_state.uploaded_file_names = uploaded_names
        st.session_state.extracted_file_text = uploaded_text
        st.info(f"已上传 {len(uploaded_names)} 个文件：{', '.join(uploaded_names)}")
        if uploaded_text:
            st.success("已合并解析多份材料。")
        if upload_warnings:
            st.warning("部分文件解析失败，但其他文件已成功读取。")
            with st.expander("查看文件解析提示", expanded=False):
                for warning in upload_warnings:
                    st.write(f"- {warning}")
        autosave_current_session()
    elif st.session_state.uploaded_file_names:
        st.info(
            f"当前会话已保存上传文件文本：{', '.join(st.session_state.uploaded_file_names)}。"
            "无需重新上传即可继续解析。"
        )

    manual_resume_text = st.text_area(
        "也可以直接粘贴简历文本",
        value=st.session_state.resume_text,
        height=280,
        placeholder="例如：教育背景、技术能力、项目经历、实习经历、竞赛经历……"
    )
    resume_text = build_combined_resume_text(
        manual_resume_text,
        st.session_state.extracted_file_text,
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        parse_btn = st.button("解析简历并生成画像", type="primary")
    with col2:
        save_btn = st.button("保存解析结果 JSON")
    with col3:
        clear_btn = st.button("清空当前内容")

    if clear_btn:
        reset_all_state()
        autosave_current_session()
        st.rerun()

    if parse_btn:
        if not resume_text.strip():
            st.warning("请先输入或上传简历内容。")
        else:
            st.session_state.resume_text = manual_resume_text
            with st.spinner("正在解析简历并生成用户画像……"):
                parsed_resume = parse_resume(resume_text, prefer_llm=True)
                profile = generate_profile_from_parsed_resume(
                    parsed_resume=parsed_resume,
                    target_role=target_role,
                    difficulty=difficulty
                )
                rag_items = retrieve_by_profile(profile, top_k=6)

            st.session_state.parsed_resume = parsed_resume
            st.session_state.profile = profile
            st.session_state.rag_items = rag_items
            reset_interview_state()
            st.success("简历解析完成，并已生成 RAG 推荐问题。")
            autosave_current_session()

    if save_btn:
        if not st.session_state.parsed_resume:
            st.warning("请先解析简历。")
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"parsed_resume_{timestamp}.json"
            json_text = json.dumps(st.session_state.parsed_resume, ensure_ascii=False, indent=2)
            st.download_button(
                "下载解析结果 JSON",
                data=json_text,
                file_name=filename,
                mime="application/json"
            )

    if resume_text.strip():
        with st.expander("简历基础摘要", expanded=False):
            st.json(simple_resume_summary(resume_text))

    if st.session_state.parsed_resume:
        st.markdown("### 结构化简历解析结果")
        parser_type = st.session_state.parsed_resume.get("_parser", "unknown")
        st.caption(f"解析方式：{parser_type}")
        if "_llm_error" in st.session_state.parsed_resume:
            st.warning(f"LLM 调用失败，已自动切换到本地解析。错误：{st.session_state.parsed_resume['_llm_error']}")
        st.json(st.session_state.parsed_resume)

    if st.session_state.profile:
        st.markdown("### 用户画像与面试重点")
        st.json(st.session_state.profile)

        st.markdown("### 基于简历匹配到的 RAG 基础知识问题")
        if st.session_state.rag_items:
            for item in st.session_state.rag_items:
                with st.expander(f"{item.get('id')}｜{item.get('category')}｜{item.get('question')}"):
                    st.write(f"**标签：** {', '.join(item.get('tags', []))}")
                    st.write(f"**难度：** {item.get('difficulty')}")
                    st.write(f"**参考答案：** {item.get('answer')}")
                    st.write(f"**可追问：** {'；'.join(item.get('follow_up', []))}")
        else:
            st.info("暂未匹配到 RAG 问题。可以检查简历技术栈或知识库标签。")

with tab2:
    st.subheader("RAG 知识库检索")

    stats = get_kb_stats()
    st.markdown("### 知识库统计")
    st.json(stats)

    search_query = st.text_input(
        "输入关键词检索知识库",
        placeholder="例如：Python MySQL Redis 后端开发 事务 索引"
    )

    if search_query:
        results = retrieve_by_query(search_query, top_k=8)
        st.markdown("### 检索结果")
        if not results:
            st.warning("没有检索到相关知识条目。")
        for item in results:
            with st.expander(f"匹配分 {item.get('_score', 0)}｜{item.get('id')}｜{item.get('question')}"):
                st.write(f"**方向：** {item.get('category')}")
                st.write(f"**标签：** {', '.join(item.get('tags', []))}")
                st.write(f"**难度：** {item.get('difficulty')}")
                st.write(f"**参考答案：** {item.get('answer')}")
                st.write(f"**可追问：** {'；'.join(item.get('follow_up', []))}")
                st.caption(f"来源：{item.get('source')}")

    st.markdown("### 当前简历推荐问题")
    if st.session_state.profile:
        recommended = retrieve_by_profile(st.session_state.profile, top_k=8)
        for item in recommended:
            with st.expander(f"{item.get('id')}｜{item.get('category')}｜{item.get('question')}"):
                st.write(f"**标签：** {', '.join(item.get('tags', []))}")
                st.write(f"**难度：** {item.get('difficulty')}")
                st.write(f"**参考答案：** {item.get('answer')}")
                st.write(f"**可追问：** {'；'.join(item.get('follow_up', []))}")
    else:
        st.info("请先在第 1 个页面解析简历，系统会根据简历技术栈推荐 RAG 问题。")

with tab3:
    st.subheader("文字版模拟面试")

    if st.session_state.profile:
        st.info("面试会结合简历画像、RAG 知识点和历史回答连续追问。")
        col_start, col_reset = st.columns([1, 1])
        with col_start:
            if st.button("开始面试", type="primary"):
                st.session_state.interview_started = True
                if not st.session_state.rag_items:
                    st.session_state.rag_items = prepare_rag_items_for_interview(st.session_state.profile, top_k=6)
                if not st.session_state.messages:
                    first = get_next_question(
                        profile=st.session_state.profile,
                        history=st.session_state.messages,
                        rag_items=st.session_state.rag_items,
                        rag_index=st.session_state.rag_index,
                        followup_count=st.session_state.followup_count,
                        used_knowledge_ids=st.session_state.used_knowledge_ids,
                        used_categories=st.session_state.used_categories
                    )
                    st.session_state.messages.append({"role": "assistant", "content": first["question"]})
                    st.session_state.current_question_meta = first
                    st.session_state.question_meta.append(first)
                    register_question_usage(first)
                    autosave_current_session()
        with col_reset:
            if st.button("重置面试"):
                reset_interview_state()
                autosave_current_session()
                st.rerun()
    else:
        st.warning("请先在「简历输入与解析」页面生成用户画像。")

    assistant_meta_index = 0
    latest_user_idx = latest_user_message_index()
    for msg_idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant":
                meta = None
                if assistant_meta_index < len(st.session_state.question_meta):
                    meta = st.session_state.question_meta[assistant_meta_index]
                render_assistant_question_details(meta)
                assistant_meta_index += 1
            elif (
                msg["role"] == "user"
                and msg_idx == latest_user_idx
                and st.session_state.interview_records
            ):
                render_latest_answer_editor(
                    key_suffix=f"inline_{len(st.session_state.interview_records)}"
                )

    st.markdown('<div id="latest-message-anchor"></div>', unsafe_allow_html=True)
    if st.session_state.scroll_to_latest:
        scroll_to_latest_message()
        st.session_state.scroll_to_latest = False

    if st.session_state.interview_started:
        user_answer = st.chat_input("请输入你的回答……")
        if user_answer:
            clear_report_state()
            st.session_state.messages.append({"role": "user", "content": user_answer})
            with st.chat_message("user"):
                st.write(user_answer)
                render_latest_answer_editor(
                    disabled=True,
                    answer_text=user_answer,
                    key_suffix="processing",
                )
            st.markdown('<div id="processing-anchor"></div>', unsafe_allow_html=True)
            scroll_to_latest_message()

            with st.spinner("正在分析你的回答并生成下一题，请稍候..."):
                last_meta = st.session_state.current_question_meta or {}
                analysis = analyze_answer(last_meta, user_answer)
                st.session_state.interview_records.append(
                    build_interview_record(last_meta, user_answer, analysis)
                )

                next_info = get_next_question(
                    profile=st.session_state.profile or {},
                    history=st.session_state.messages,
                    rag_items=st.session_state.rag_items,
                    rag_index=st.session_state.rag_index,
                    last_answer=user_answer,
                    last_question_meta=last_meta,
                    last_analysis=analysis,
                    followup_count=st.session_state.followup_count,
                    used_knowledge_ids=st.session_state.used_knowledge_ids,
                    used_categories=st.session_state.used_categories
                )

            st.session_state.rag_index = next_info.get("rag_index", st.session_state.rag_index)
            st.session_state.followup_count = next_info.get("followup_count", st.session_state.followup_count)
            st.session_state.messages.append({"role": "assistant", "content": next_info["question"]})
            st.session_state.current_question_meta = next_info
            st.session_state.question_meta.append(next_info)
            register_question_usage(next_info)
            autosave_current_session()
            st.session_state.scroll_to_latest = True
            st.rerun()

    with st.expander("本轮原始问题元数据", expanded=False):
        st.json(st.session_state.question_meta)

with tab4:
    st.subheader("面试记录与回答分析")

    records = st.session_state.interview_records
    summary = summarize_interview_records(records)

    st.markdown("### 面试过程摘要")
    st.json(summary)

    if not records:
        st.info("还没有面试回答记录。请先开始模拟面试。")
    else:
        for idx, record in enumerate(records, start=1):
            title = f"第 {idx} 题｜{record.get('question_type')}｜回答评分 {record.get('analysis', {}).get('overall_temp_score')}/10"
            if record.get("knowledge_id"):
                title += f"｜{record.get('knowledge_id')}"
            with st.expander(title, expanded=False):
                st.markdown("**问题：**")
                st.write(record.get("question", ""))
                st.markdown("**用户回答：**")
                st.write(record.get("user_answer", ""))
                st.markdown("**回答分析：**")
                st.json(record.get("analysis", {}))
                if record.get("reference_answer"):
                    st.markdown("**参考答案 / 依据：**")
                    st.write(record.get("reference_answer"))

        json_text = json.dumps(records, ensure_ascii=False, indent=2)
        st.download_button(
            "下载本轮面试记录 JSON",
            data=json_text,
            file_name=f"interview_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

with tab5:
    st.subheader("正式面试评分报告")
    st.info("五维度评分权重保持不变：基础知识 25%、项目理解 25%、回答逻辑 20%、表达完整性 15%、岗位匹配度 15%。")

    records = st.session_state.interview_records
    profile = st.session_state.profile or {}

    col_report, col_clear_report = st.columns([1, 1])
    with col_report:
        generate_report_btn = st.button("生成正式评分报告", type="primary")
    with col_clear_report:
        if st.button("清空评分报告"):
            clear_report_state()
            autosave_current_session()
            st.rerun()

    if generate_report_btn:
        if not records:
            st.warning("还没有面试记录。请先完成至少几轮模拟面试。")
        else:
            st.session_state.final_report = build_final_report(records, profile)
            st.session_state.report_json = json.dumps(st.session_state.final_report, ensure_ascii=False, indent=2)
            st.session_state.report_markdown = report_to_markdown(st.session_state.final_report)
            st.success("正式评分报告已生成。")
            autosave_current_session(status="completed")

    report = st.session_state.final_report

    if report:
        st.markdown("### 总体结果")
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("总分", f"{report['total_score']} / 100")
        col_b.metric("等级", report["level"])
        col_c.metric("回答数量", report["interview_summary"]["answer_count"])
        col_d.metric("目标岗位", report.get("target_role") or "未明确")

        st.markdown("### 五维度评分")
        dim_cols = st.columns(5)
        for idx, (dim, detail) in enumerate(report["dimension_details"].items()):
            score = float(detail["score"])
            dim_cols[idx % 5].metric(dim, f"{score} / 100", help=f"权重 {detail['weight']}")
        for dim, detail in report["dimension_details"].items():
            score = float(detail["score"])
            st.write(f"**{dim}**（权重 {detail['weight']}）")
            st.progress(min(100, int(score)) / 100)

        st.markdown("### 评分依据")
        for dim, detail in report["dimension_details"].items():
            with st.expander(f"{dim}｜{detail['score']} 分｜权重 {detail['weight']}"):
                for ev in detail.get("evidence", []):
                    st.write(f"- {ev}")

        with st.expander("表现较好的方面", expanded=True):
            for item in report.get("strengths", []):
                st.write(f"- {item}")

        with st.expander("主要问题", expanded=True):
            for item in report.get("main_problems", []):
                st.write(f"- {item}")

        with st.expander("后续提升建议", expanded=True):
            for item in report.get("recommendations", []):
                st.write(f"- {item}")

        st.markdown("### 报告详情")
        with st.expander("查看报告 JSON", expanded=False):
            st.json(report)

        json_text = st.session_state.report_json or json.dumps(report, ensure_ascii=False, indent=2)
        md_text = st.session_state.report_markdown or report_to_markdown(report)

        col_json, col_md = st.columns(2)
        with col_json:
            st.download_button(
                "下载评分报告 JSON",
                data=json_text,
                file_name=f"final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        with col_md:
            st.download_button(
                "下载评分报告 Markdown",
                data=md_text,
                file_name=f"final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
    else:
        summary = summarize_interview_records(records)
        st.markdown("### 当前过程摘要")
        st.json({
            "当前回答数量": summary["total_answers"],
            "平均回答评分": summary["average_temp_score"],
            "高频技术关键词": summary["frequent_keywords"],
            "常见问题": summary["common_problems"],
            "提示": "完成几轮面试后，点击“生成正式评分报告”。"
        })

with tab6:
    st.subheader("项目说明与运行检查")

    st.markdown("### 核心闭环")
    st.code(
        "简历输入/解析 → 用户画像 → RAG 检索 → 连续面试 → 项目追问 → 回答分析 → 五维度评分报告",
        language="text"
    )

    st.markdown("### LLM 配置状态")
    llm_config = get_llm_config()
    st.json({
        "USE_LLM": llm_config.get("use_llm", ""),
        "MODEL_NAME": llm_config.get("model_name", ""),
        "LLM_BASE_URL": llm_config.get("base_url", ""),
        "LLM_API_KEY": get_masked_api_key() or "未配置",
        "enabled": is_llm_enabled()
    })

    if st.button("检查 LLM 连接", type="primary"):
        result = test_llm_connection()
        if result.get("ok"):
            st.success(result.get("message"))
        else:
            st.error(result.get("message"))
        st.json(result)

    st.markdown("### 项目文件状态")
    required_files = [
        "app.py",
        "requirements.txt",
        "README.md",
        ".env.example",
        "data/knowledge_base.json",
        "data/sample_resume.txt",
        "src/llm_client.py",
        "src/resume_parser.py",
        "src/rag_retriever.py",
        "src/interviewer.py",
        "src/answer_analyzer.py",
        "src/evaluator.py",
        "docs/llm_config_guide.md",
        "docs/rag_build_guide.md",
        "docs/design_document_draft.md",
        "docs/demo_script.md",
        "docs/test_checklist.md",
        "docs/final_submission_checklist.md",
        "demo/sample_resume_ai_app.txt",
        "demo/sample_resume_backend.txt",
        "demo/sample_answers_ai_app.md",
        "demo/demo_walkthrough.md",
        "scripts/self_check.py",
    ]
    root = Path(".")
    check_rows = []
    for rel in required_files:
        check_rows.append({
            "file": rel,
            "exists": (root / rel).exists()
        })
    st.dataframe(check_rows, use_container_width=True)

    st.markdown("### 提交前检查清单")
    checklist = [
        "项目能通过 streamlit run app.py 正常启动",
        "可以解析简历并生成用户画像",
        "RAG 知识库能显示条目总数并完成检索",
        "侧边栏可以加载示例简历",
        "模拟面试能连续进行并触发追问",
        "当前题目能展示生成方式、难度、知识点和预期回答要点",
        "面试记录与分析页面有记录",
        "评分报告能生成总分、五维度评分和建议",
        "LLM 连接检查成功",
        "USE_LLM=false 时备用出题机制可用",
        ".env 未上传到 GitHub",
        "README、demo walkthrough、设计文档和最终提交清单已准备",
        "演示视频控制在 8 分钟内"
    ]
    for item in checklist:
        st.write(f"- [ ] {item}")

    st.markdown("### 推荐命令")
    st.code(
        ".venv\\Scripts\\activate\n"
        "python scripts/self_check.py\n"
        "streamlit run app.py",
        language="bash"
    )

    st.markdown("### 文档位置")
    st.write("- LLM 配置教程：`docs/llm_config_guide.md`")
    st.write("- RAG 构建说明：`docs/rag_build_guide.md`")
    st.write("- 项目设计文档初稿：`docs/design_document_draft.md`")
    st.write("- 演示视频脚本：`docs/demo_script.md`")
    st.write("- 测试清单：`docs/test_checklist.md`")
    st.write("- 最终提交清单：`docs/final_submission_checklist.md`")
    st.write("- 演示流程：`demo/demo_walkthrough.md`")
    st.write("- 示例回答：`demo/sample_answers_ai_app.md`")


    st.markdown("### 最终提交建议")
    st.write("1. 运行 self_check.py 并确保通过。")
    st.write("2. 检查 LLM 连接，确认简历可以优先使用 LLM 解析。")
    st.write("3. 完成一次完整面试流程，生成评分报告。")
    st.write("4. 按 docs/demo_script.md 录制不超过 8 分钟演示视频。")
    st.write("5. 上传 GitHub，并提交项目设计文档与视频。")
