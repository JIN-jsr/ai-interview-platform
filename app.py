import json
import math
from datetime import datetime
import streamlit.components.v1 as components

import streamlit as st

from src.answer_analyzer import analyze_answer, summarize_interview_records
from src.evaluator import build_final_report, report_to_markdown
from src.interviewer import get_next_question, prepare_rag_items_for_interview
from pathlib import Path

from src.llm_client import get_llm_config, get_masked_api_key, is_llm_enabled, test_llm_connection
from src.profile_generator import generate_profile_from_parsed_resume
from src.product_features import (
    analyze_growth_reports,
    detect_role_mismatch,
    format_report_time,
    generate_resume_optimization_suggestions,
)
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

USE_REFINED_UI = True


def inject_refined_bw_styles():
    st.markdown(
        """
        <style>
        :root {
            --ui-black: #111827;
            --ui-text: #1f2937;
            --ui-muted: #6b7280;
            --ui-border: #e5e7eb;
            --ui-border-strong: #d1d5db;
            --ui-soft: #f9fafb;
            --ui-white: #ffffff;
            --ui-shadow: 0 8px 28px rgba(15, 23, 42, 0.05);
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        .stButton > button {
            min-height: 52px;
            border-radius: 15px;
            border: 1px solid var(--ui-border-strong);
            background: var(--ui-white);
            color: var(--ui-black);
            font-size: 17px;
            font-weight: 650;
            box-shadow: none;
        }
        .stButton > button:hover {
            border-color: var(--ui-black);
            color: var(--ui-black);
            background: var(--ui-soft);
        }
        .stButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"] {
            background: var(--ui-black);
            color: var(--ui-white);
            border-color: var(--ui-black);
        }
        .stButton > button[kind="primary"]:hover,
        .stButton > button[data-testid="baseButton-primary"]:hover {
            background: #1f2937;
            color: var(--ui-white);
            border-color: #1f2937;
        }
        .home-hero {
            min-height: auto !important;
            padding-top: 28vh !important;
            margin-bottom: 0 !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            text-align: center !important;
        }
        .home-title {
            font-size: clamp(52px, 5.5vw, 78px) !important;
            font-weight: 850 !important;
            letter-spacing: -0.045em !important;
            line-height: 1.08 !important;
            color: var(--ui-black) !important;
            margin: 0 0 18px !important;
            white-space: nowrap !important;
        }
        .home-subtitle {
            font-size: clamp(22px, 2vw, 30px) !important;
            font-weight: 400 !important;
            color: var(--ui-muted) !important;
            line-height: 1.6 !important;
            margin: 0 auto 20px !important;
            max-width: 980px !important;
        }
        .home-actions {
            height: 0;
            margin: 0;
            padding: 0;
        }
        .home-actions + div[data-testid="stHorizontalBlock"] {
            max-width: 600px !important;
            margin: 0 auto !important;
        }
        .home-actions + div[data-testid="stHorizontalBlock"] .stButton > button {
            min-height: 56px !important;
            min-width: 220px !important;
            font-size: 20px !important;
            font-weight: 650 !important;
            border-radius: 16px !important;
        }
        .intro-lead {
            color: var(--ui-muted);
            font-size: 18px;
            line-height: 1.7;
            max-width: 960px;
            margin: 0 0 1.5rem;
        }
        .intro-card {
            background: var(--ui-white);
            border: 1px solid var(--ui-border);
            border-radius: 18px;
            padding: 24px;
            box-shadow: var(--ui-shadow);
            height: 100%;
            margin-bottom: 1rem;
        }
        .intro-card h3 {
            color: var(--ui-black);
            font-size: 22px;
            font-weight: 750;
            margin: 0 0 14px;
        }
        .intro-card p,
        .intro-card li {
            color: #374151;
            font-size: 16px;
            line-height: 1.75;
        }
        .intro-card ul {
            margin: 0;
            padding-left: 1.2rem;
        }
        .process-flow {
            display: flex;
            flex-wrap: wrap;
            gap: 10px 14px;
            align-items: center;
            margin-top: 6px;
            border: 1px solid var(--ui-border);
            border-radius: 14px;
            background: var(--ui-soft);
            padding: 18px 20px;
            color: var(--ui-black);
            font-weight: 650;
            line-height: 1.7;
        }
        .process-step {
            white-space: nowrap;
        }
        div[data-testid="stPopover"] {
            position: fixed;
            right: 28px;
            top: 92px;
            z-index: 999;
        }
        div[data-testid="stPopover"] > button {
            min-height: 42px;
            border-radius: 999px;
            background: var(--ui-black);
            color: var(--ui-white);
            border-color: var(--ui-black);
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.16);
        }
        .status-card {
            background: var(--ui-white);
            border: 1px solid var(--ui-border);
            border-radius: 14px;
            padding: 12px 14px;
            box-shadow: var(--ui-shadow);
            min-height: 76px;
        }
        .status-label {
            color: var(--ui-muted);
            font-size: 13px;
            margin-bottom: 6px;
        }
        .status-value {
            color: var(--ui-black);
            font-size: 18px;
            font-weight: 700;
            line-height: 1.35;
        }
        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--ui-black);
            margin-right: 6px;
        }
        .status-muted {
            color: var(--ui-muted);
            font-size: 14px;
            line-height: 1.7;
        }
        @media (max-width: 900px) {
            .home-hero {
                padding-top: 22vh !important;
            }
            .home-title {
                white-space: normal !important;
            }
            div[data-testid="stPopover"] {
                right: 16px;
                top: 74px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if USE_REFINED_UI:
    inject_refined_bw_styles()

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
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "role_mismatch_warning" not in st.session_state:
    st.session_state.role_mismatch_warning = ""
if "resume_optimization_suggestions" not in st.session_state:
    st.session_state.resume_optimization_suggestions = []
if "resume_withdraw_confirmed" not in st.session_state:
    st.session_state.resume_withdraw_confirmed = False
if "demo_answer_template" not in st.session_state:
    st.session_state.demo_answer_template = ""


DEMO_DIR = Path("demo")
SAMPLE_RESUMES = {
    "AI 应用开发示例": DEMO_DIR / "sample_resume_ai_app.txt",
    "后端开发示例": DEMO_DIR / "sample_resume_backend.txt",
    "数据分析示例": DEMO_DIR / "sample_resume_data_analysis.txt",
}
SAMPLE_ANSWER_TEMPLATES = {
    "AI 应用开发示例": DEMO_DIR / "sample_answers_ai_app.md",
    "后端开发示例": DEMO_DIR / "sample_answers_backend.md",
    "数据分析示例": DEMO_DIR / "sample_answers_data_analysis.md",
}

STATUS_LABELS = {
    "created": "已创建",
    "resume_ready": "简历已解析",
    "interviewing": "面试进行中",
    "completed": "报告已生成",
    "in_progress": "面试进行中",
}


def get_status_label(status):
    return STATUS_LABELS.get(str(status or "").strip(), "已创建")


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
    st.session_state.role_mismatch_warning = ""
    st.session_state.resume_optimization_suggestions = []
    st.session_state.resume_withdraw_confirmed = False
    st.session_state.demo_answer_template = ""


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
        "role_mismatch_warning": st.session_state.role_mismatch_warning,
        "resume_optimization_suggestions": st.session_state.resume_optimization_suggestions,
        "demo_answer_template": st.session_state.demo_answer_template,
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
    st.session_state.role_mismatch_warning = session_data.get("role_mismatch_warning", "")
    st.session_state.resume_optimization_suggestions = session_data.get("resume_optimization_suggestions", [])
    st.session_state.demo_answer_template = session_data.get("demo_answer_template", "")
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

def go_to_page(page):
    st.session_state.current_page = page
    st.rerun()


def render_home_page():
    if not USE_REFINED_UI:
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] {display: none;}
            [data-testid="collapsedControl"] {display: none;}
            .block-container {max-width: 1180px; padding-top: 0;}
            .home-hero {
                min-height: 58vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
            }
            .home-title {
                font-size: clamp(56px, 7vw, 80px);
                font-weight: 900;
                line-height: 1.08;
                color: #101828;
                margin: 0 0 28px 0;
                letter-spacing: 0;
            }
            .home-subtitle {
                font-size: clamp(22px, 2.4vw, 28px);
                line-height: 1.55;
                color: #667085;
                margin: 0 0 52px 0;
                max-width: 920px;
            }
            div[data-testid="stHorizontalBlock"]:has(.home-button-spacer) {
                max-width: 720px;
                margin: 0 auto;
            }
            .stButton > button {
                min-height: 64px;
                min-width: 220px;
                font-size: 22px;
                font-weight: 700;
                border-radius: 18px;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] {display: none;}
            [data-testid="collapsedControl"] {display: none;}
            .block-container {max-width: 1180px; padding-top: 0;}
            .stButton > button {
                min-height: 56px !important;
                min-width: 220px !important;
                font-size: 20px !important;
                font-weight: 650 !important;
                border-radius: 16px !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <div class="home-hero">
          <h1 class="home-title">AI模拟面试与能力提升平台</h1>
          <p class="home-subtitle">
            简历驱动、RAG 知识库、LLM 连续追问与五维度评分报告的一体化训练工具
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<span class="home-actions"></span>', unsafe_allow_html=True)
    col_left, col_intro, col_gap, col_interview, col_right = st.columns([1, 1.45, 0.36, 1.45, 1])
    with col_intro:
        if st.button("系统介绍", type="secondary", use_container_width=True):
            go_to_page("intro")
    with col_interview:
        if st.button("模拟面试", type="primary", use_container_width=True):
            go_to_page("interview")


def render_intro_page():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
        .block-container {max-width: 1080px; padding-top: 3rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    nav_home, nav_interview, nav_space = st.columns([1, 1, 4])
    with nav_home:
        if st.button("返回主页", use_container_width=True):
            go_to_page("home")
    with nav_interview:
        if st.button("进入模拟面试", type="primary", use_container_width=True):
            go_to_page("interview")

    st.title("系统介绍")
    if not USE_REFINED_UI:
        st.write(
            "本系统面向计算机相关专业学生和求职者，围绕简历内容生成候选人画像，"
            "结合本地知识库与可选大模型能力，完成从模拟面试到评分反馈的闭环训练。"
        )
        st.code("简历输入 -> 用户画像 -> RAG 检索 -> LLM 连续追问 -> 回答分析 -> 五维度评分报告", language="text")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### 核心能力")
            st.write("- 简历解析与多文件材料合并")
            st.write("- 岗位画像和面试重点生成")
            st.write("- RAG 知识库检索与岗位导向选题")
            st.write("- LLM 动态出题与上下文连续追问")
            st.write("- 回答覆盖度分析和评分报告")
        with col_b:
            st.markdown("### 技术特点")
            st.write("- LLM + RAG 协同，问题基于知识库和候选人画像")
            st.write("- 规则备用机制，接口不可用时仍可完成面试")
            st.write("- 难度控制、岗位导向和问题元数据可解释")
            st.write("- 本地 JSON 面试历史，支持独立会话恢复")
            st.write("- 五维度评分：基础、项目、逻辑、表达、岗位匹配")
        st.markdown("### 适合用户")
        st.write("适合准备技术面试、课程展示、竞赛演示或希望系统化复盘项目表达的学生与求职者。")
        st.markdown("### 评分报告说明")
        st.write("评分报告从基础知识、项目理解、回答逻辑、表达完整性和岗位匹配五个维度给出结构化反馈，便于后续针对性提升。")
        return

    st.markdown(
        """
        <p class="intro-lead">
        本系统面向计算机相关专业学生与求职者，围绕简历内容生成候选人画像，
        结合本地知识库与大模型能力，完成从模拟面试到评分反馈的闭环训练。
        </p>
        <div class="intro-card">
          <h3>训练流程</h3>
          <div class="process-flow">
            <span class="process-step">简历输入</span>
            <span>→</span>
            <span class="process-step">用户画像</span>
            <span>→</span>
            <span class="process-step">RAG 检索</span>
            <span>→</span>
            <span class="process-step">LLM 生成追问</span>
            <span>→</span>
            <span class="process-step">回答分析</span>
            <span>→</span>
            <span class="process-step">五维度评分报告</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            """
            <div class="intro-card">
              <h3>核心能力</h3>
              <ul>
                <li>简历解析与多文件材料合并</li>
                <li>岗位画像和面试画像生成</li>
                <li>RAG 知识库检索与岗位导向选题</li>
                <li>LLM 动态出题与上下文连续追问</li>
                <li>回答覆盖度分析和评分报告</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            """
            <div class="intro-card">
              <h3>技术特点</h3>
              <ul>
                <li>LLM + RAG 协同，问题基于知识库和候选人画像</li>
                <li>策略降级机制，接口不可用时仍可完成面试</li>
                <li>难度控制、岗位导向和问题元数据可解释</li>
                <li>本地 JSON 面试历史，支持独立会话恢复</li>
                <li>五维度评分：基础、项目、逻辑、表达、岗位匹配</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown(
            """
            <div class="intro-card">
              <h3>适合用户</h3>
              <p>适合准备技术面试、课程展示、竞赛演示或希望系统化复盘项目表达的学生与求职者。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_d:
        st.markdown(
            """
            <div class="intro-card">
              <h3>评分报告说明</h3>
              <p>评分报告从基础知识、项目理解、回答逻辑、表达完整性和岗位匹配五个维度给出结构化反馈，便于后续针对性提升。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_realtime_status(target_role, difficulty, current_status, assistant_count, kb_stats):
    with st.expander("实时面试状态", expanded=False):
        info_cols = st.columns(5)
        info_cols[0].metric("当前岗位", target_role)
        info_cols[1].metric("面试难度", difficulty)
        info_cols[2].metric("当前状态", current_status)
        info_cols[3].metric("已回答题数", len(st.session_state.interview_records))
        info_cols[4].metric("报告状态", "已生成" if st.session_state.final_report else "未生成")
        detail_cols = st.columns(4)
        detail_cols[0].write(f"**当前轮次：** {assistant_count}")
        detail_cols[1].write(f"**上下文追问：** {st.session_state.followup_count}")
        detail_cols[2].write(f"**已用知识点：** {len(st.session_state.used_knowledge_ids)}")
        detail_cols[3].write(f"**RAG 条目：** {kb_stats['total_entries']}")


def render_radar_chart(dimension_details):
    labels = list(dimension_details.keys())
    scores = [float(dimension_details[label].get("score", 0)) for label in labels]
    if not labels:
        return

    center_x, center_y = 240, 210
    radius = 135
    points = []
    axis_lines = []
    label_nodes = []
    for idx, (label, score) in enumerate(zip(labels, scores)):
        angle = -math.pi / 2 + idx * 2 * math.pi / len(labels)
        outer_x = center_x + radius * math.cos(angle)
        outer_y = center_y + radius * math.sin(angle)
        value_radius = radius * max(0, min(score, 100)) / 100
        value_x = center_x + value_radius * math.cos(angle)
        value_y = center_y + value_radius * math.sin(angle)
        label_x = center_x + (radius + 42) * math.cos(angle)
        label_y = center_y + (radius + 28) * math.sin(angle)
        points.append(f"{value_x:.1f},{value_y:.1f}")
        axis_lines.append(
            f'<line x1="{center_x}" y1="{center_y}" x2="{outer_x:.1f}" y2="{outer_y:.1f}" '
            'stroke="#d0d5dd" stroke-width="1" />'
        )
        label_nodes.append(
            f'<text x="{label_x:.1f}" y="{label_y:.1f}" text-anchor="middle" '
            'font-size="13" fill="#344054">'
            f"{label} {score:.0f}</text>"
        )

    grid_polygons = []
    for pct in [20, 40, 60, 80, 100]:
        grid_points = []
        for idx in range(len(labels)):
            angle = -math.pi / 2 + idx * 2 * math.pi / len(labels)
            grid_radius = radius * pct / 100
            grid_points.append(
                f"{center_x + grid_radius * math.cos(angle):.1f},{center_y + grid_radius * math.sin(angle):.1f}"
            )
        grid_polygons.append(
            f'<polygon points="{" ".join(grid_points)}" fill="none" stroke="#eaecf0" stroke-width="1" />'
        )

    svg = f"""
    <div style="display:flex; justify-content:center; margin: 0.5rem 0 1rem;">
      <svg viewBox="0 0 480 430" width="100%" style="max-width: 620px;">
        {''.join(grid_polygons)}
        {''.join(axis_lines)}
        <polygon points="{' '.join(points)}" fill="rgba(46, 144, 250, 0.28)" stroke="#2e90fa" stroke-width="3" />
        {''.join(label_nodes)}
      </svg>
    </div>
    """
    st.markdown(svg, unsafe_allow_html=True)


def render_bullet_card(title, items):
    with st.container(border=True):
        st.markdown(f"#### {title}")
        for item in items:
            st.write(f"- {item}")


def render_rag_page():
    if st.button("返回模拟面试"):
        go_to_page("interview")
    st.title("RAG知识库")
    st.subheader("知识库检索")

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
        st.info("请先进入模拟面试并解析简历，系统会根据简历技术栈推荐 RAG 问题。")



def render_self_check_page():
    if st.button("返回模拟面试"):
        go_to_page("interview")
    st.title("项目说明与运行检查")

    st.markdown("### 核心闭环")
    st.code(
        "简历输入/解析 → 用户画像 → RAG 检索 → 连续面试 → 项目追问 → 回答分析 → 五维度评分报告",
        language="text"
    )

    st.markdown("### LLM 配置状态")
    llm_config = get_llm_config()
    st.json({
        "是否启用LLM": llm_config.get("use_llm", ""),
        "模型名称": llm_config.get("model_name", ""),
        "接口地址": llm_config.get("base_url", ""),
        "API密钥": get_masked_api_key() or "未配置",
        "连接状态": "已启用" if is_llm_enabled() else "未启用"
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


def withdraw_resume_state():
    st.session_state.resume_text = ""
    st.session_state.uploaded_file_names = []
    st.session_state.extracted_file_text = ""
    st.session_state.parsed_resume = None
    st.session_state.profile = None
    st.session_state.rag_items = []
    st.session_state.role_mismatch_warning = ""
    st.session_state.resume_optimization_suggestions = []
    st.session_state.resume_withdraw_confirmed = False
    reset_interview_state()
    autosave_current_session(status="created")


def start_demo_session(target_role, difficulty, sample_key):
    sample_path = SAMPLE_RESUMES.get(sample_key)
    if not sample_path or not sample_path.exists():
        st.warning(f"未找到演示简历：{sample_key}")
        return
    answer_path = SAMPLE_ANSWER_TEMPLATES.get(sample_key)
    title = f"演示面试｜{target_role}｜{difficulty}"
    new_session = create_new_session(target_role=target_role, difficulty=difficulty, title=title)
    restore_session_state(new_session)
    st.session_state.selected_target_role = target_role
    st.session_state.selected_difficulty = difficulty
    st.session_state.resume_text = sample_path.read_text(encoding="utf-8")
    st.session_state.demo_answer_template = answer_path.read_text(encoding="utf-8") if answer_path and answer_path.exists() else ""
    reset_interview_state()
    autosave_current_session(status="created")
    st.success("已创建新的演示面试，不会覆盖原有记录。请点击“解析简历并生成画像”。")


def render_floating_status_panel(target_role, difficulty, current_status, assistant_count, kb_stats):
    answered_count = len(st.session_state.interview_records)
    expected_count = 8
    report_status = "已生成" if st.session_state.final_report else "未生成"
    trigger = f"● {current_status}  {answered_count} / {expected_count}"
    with st.popover(trigger, use_container_width=False):
        st.markdown("#### 实时面试状态")
        core_cols = st.columns(4)
        core_items = [
            ("目标岗位", target_role or "未选择"),
            ("面试难度", difficulty or "未选择"),
            ("当前状态", current_status),
            ("报告状态", report_status),
        ]
        for col, (label, value) in zip(core_cols, core_items):
            with col:
                st.markdown(
                    f"""
                    <div class="status-card">
                      <div class="status-label">{label}</div>
                      <div class="status-value"><span class="status-dot"></span>{value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("##### 进度")
        progress = min(1.0, answered_count / expected_count)
        st.progress(progress)
        progress_cols = st.columns(4)
        progress_cols[0].metric("已回答", answered_count)
        progress_cols[1].metric("当前轮次", assistant_count)
        progress_cols[2].metric("上下文追问", st.session_state.followup_count)
        progress_cols[3].metric("已用知识点", len(st.session_state.used_knowledge_ids))

        st.markdown("##### 系统信息")
        st.markdown(
            f"""
            <div class="status-muted">
            RAG 条目：{kb_stats.get('total_entries', 0)}<br>
            LLM 状态：{'已启用' if is_llm_enabled() else '未启用'}<br>
            备用出题机制：可用
            </div>
            """,
            unsafe_allow_html=True,
        )


def _completed_report_options():
    try:
        sessions, _ = list_sessions()
    except Exception:
        return []
    options = []
    for item in sessions:
        session = load_session(item.get("session_id", ""))
        if not session or not session.get("final_report"):
            continue
        report = session.get("final_report", {})
        label = (
            f"{format_report_time(report.get('generated_at') or session.get('updated_at'))}｜"
            f"{report.get('target_role') or session.get('target_role')}｜"
            f"{report.get('difficulty') or session.get('difficulty')}｜"
            f"{report.get('total_score')}｜{report.get('level')}"
        )
        options.append({"label": label, "session": session, "report": report})
    return options


def render_growth_curve_page():
    if st.button("返回模拟面试"):
        go_to_page("interview")
    st.title("能力成长曲线")
    st.write("选择真实有效的已完成面试报告，生成总分与五维度能力趋势。")

    options = _completed_report_options()
    if len(options) < 2:
        st.info("请至少完成两次生成报告的面试后，再查看能力成长曲线。")
        return

    label_to_option = {item["label"]: item for item in options}
    selected_labels = st.multiselect(
        "选择纳入分析的历史报告",
        options=[item["label"] for item in options],
        default=[item["label"] for item in options[: min(3, len(options))]],
    )

    if st.button("生成成长曲线", type="primary"):
        if len(selected_labels) < 2:
            st.warning("请至少选择两条已生成报告的面试记录。")
            return
        selected_reports = [label_to_option[label]["report"] for label in selected_labels]
        selected_reports = sorted(selected_reports, key=lambda report: report.get("generated_at", ""))

        score_rows = [
            {
                "时间": format_report_time(report.get("generated_at")),
                "总分": float(report.get("total_score", 0) or 0)
            }
            for report in selected_reports
        ]
        st.markdown("### 总分趋势图")
        st.line_chart(score_rows, x="时间", y="总分")

        dimension_rows = []
        for report in selected_reports:
            row = {"时间": format_report_time(report.get("generated_at"))}
            for dim, score in report.get("dimension_scores", {}).items():
                row[dim] = float(score or 0)
            dimension_rows.append(row)
        st.markdown("### 五维度能力趋势图")
        st.line_chart(dimension_rows, x="时间")

        analysis = analyze_growth_reports(selected_reports)
        st.markdown("### 成长总结")
        st.write(analysis.get("summary"))
        st.markdown("### 后续提升建议")
        for item in analysis.get("recommendations", []):
            st.write(f"- {item}")


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

    with st.expander("RAG 出题依据", expanded=False):
        knowledge_id = meta.get("knowledge_id")
        if knowledge_id:
            st.write(f"**知识点 ID：** {knowledge_id}")
            st.write(f"**知识类别：** {meta.get('category') or '未标注'}")
            tags = meta.get("tags", [])
            if tags:
                st.write(f"**相关标签：** {'、'.join(str(tag) for tag in tags)}")
            points = meta.get("expected_points", [])
            if points:
                st.markdown("**考察要点：**")
                for point in points:
                    st.write(f"- {point}")
            if meta.get("reference_answer"):
                st.markdown("**参考依据：**")
                st.write(meta.get("reference_answer"))
            scenarios = meta.get("related_project_scenarios", [])
            if scenarios:
                st.markdown("**可关联项目场景：**")
                for scenario in scenarios[:3]:
                    st.write(f"- {scenario}")
        else:
            st.caption("本题主要基于候选人简历与上下文生成。")

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

if st.session_state.current_page == "home":
    render_home_page()
    st.stop()
if st.session_state.current_page == "intro":
    render_intro_page()
    st.stop()

with st.sidebar:
    if st.button("返回主页", use_container_width=True):
        go_to_page("home")
    st.divider()

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
        status_label = get_status_label(item.get("status"))
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

    st.divider()
    st.subheader("更多功能")
    if st.button("RAG知识库", use_container_width=True):
        go_to_page("rag")
    if st.button("项目说明与运行检查", use_container_width=True):
        go_to_page("self_check")
    if st.button("能力成长曲线", use_container_width=True):
        go_to_page("growth")
    with st.expander("演示模式", expanded=False):
        st.caption("一键演示会创建新的演示面试，不会覆盖当前记录。")
        if st.button("一键加载后端开发演示", use_container_width=True):
            start_demo_session("后端开发", "中等", "后端开发示例")
            st.rerun()
        if st.button("一键加载 AI 应用开发演示", use_container_width=True):
            start_demo_session("AI应用开发", "中等", "AI 应用开发示例")
            st.rerun()
        if st.button("一键加载数据分析演示", use_container_width=True):
            start_demo_session("数据分析", "困难", "数据分析示例")
            st.rerun()
        sample_choice = st.selectbox("示例简历", list(SAMPLE_RESUMES.keys()))
        if st.button("加载示例简历"):
            load_demo_resume(sample_choice)
            st.rerun()
        if st.button("一键清空演示数据"):
            reset_all_state()
            autosave_current_session(status="created")
            st.rerun()
        if st.session_state.demo_answer_template:
            with st.expander("演示回答模板", expanded=False):
                st.markdown(st.session_state.demo_answer_template)
        if st.button("重置当前面试"):
            reset_interview_state()
            autosave_current_session()
            st.rerun()
        if st.button("清空全部记录"):
            reset_all_state()
            autosave_current_session()
            st.rerun()
        st.caption("“重置当前面试”会保留简历画像；“清空全部记录”会清空简历、画像、面试和报告。")

    st.divider()
    st.subheader("系统状态")
    sidebar_config = get_llm_config()
    st.write(f"**LLM：** {'已启用' if is_llm_enabled() else '未启用'}")
    st.write(f"**模型：** {sidebar_config.get('model_name') or '未配置'}")
    st.write("**备用出题：** 可用")

target_role = st.session_state.selected_target_role
difficulty = st.session_state.selected_difficulty
config = get_llm_config()
kb_stats = get_kb_stats()
assistant_count = len([m for m in st.session_state.messages if m.get("role") == "assistant"])
current_status = get_status_label(infer_session_status())

if st.session_state.current_page == "rag":
    render_rag_page()
    st.stop()
if st.session_state.current_page == "self_check":
    render_self_check_page()
    st.stop()
if st.session_state.current_page == "growth":
    render_growth_curve_page()
    st.stop()

st.header("模拟面试工作台")
render_floating_status_panel(target_role, difficulty, current_status, assistant_count, kb_stats)

tab1, tab2, tab3, tab4 = st.tabs([
    "1. 简历输入与解析",
    "2. 模拟面试",
    "3. 面试记录与分析",
    "4. 评分报告"
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
        parse_btn = st.button("解析简历并生成画像", type="primary", use_container_width=True)
    with col2:
        save_btn = st.button("保存解析结果 JSON", use_container_width=True)
    with col3:
        clear_btn = st.button("清空当前内容", use_container_width=True)

    if clear_btn:
        reset_all_state()
        autosave_current_session()
        st.rerun()

    has_resume_state = bool(
        st.session_state.resume_text
        or st.session_state.extracted_file_text
        or st.session_state.uploaded_file_names
        or st.session_state.parsed_resume
        or st.session_state.profile
    )
    if has_resume_state:
        st.markdown("### 简历操作")
        needs_confirm = bool(st.session_state.interview_started or st.session_state.interview_records or st.session_state.messages)
        if needs_confirm:
            st.warning("撤回简历将清空当前面试问题、回答记录和评分报告。")
            st.checkbox("我确认继续撤回当前简历", key="resume_withdraw_confirmed")
        if st.button("重新上传 / 修改简历", use_container_width=True):
            if needs_confirm and not st.session_state.resume_withdraw_confirmed:
                st.warning("请先勾选确认后再撤回当前简历。")
            else:
                withdraw_resume_state()
                st.success("当前简历与面试状态已清空，可以重新上传或粘贴简历。")
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
                mismatch = detect_role_mismatch(parsed_resume, profile, target_role)
                role_mismatch_warning = mismatch.get("warning", "")
                resume_suggestions = generate_resume_optimization_suggestions(
                    parsed_resume=parsed_resume,
                    profile=profile,
                    target_role=target_role,
                    mismatch_warning=role_mismatch_warning,
                )
                profile["role_mismatch_warning"] = role_mismatch_warning
                profile["resume_optimization_suggestions"] = resume_suggestions
                rag_items = retrieve_by_profile(profile, top_k=6)

            st.session_state.parsed_resume = parsed_resume
            st.session_state.profile = profile
            st.session_state.rag_items = rag_items
            st.session_state.role_mismatch_warning = role_mismatch_warning
            st.session_state.resume_optimization_suggestions = resume_suggestions
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
        if st.session_state.role_mismatch_warning:
            st.warning(st.session_state.role_mismatch_warning)
        st.json(st.session_state.profile)

        if st.session_state.resume_optimization_suggestions:
            with st.expander("简历优化建议", expanded=True):
                for item in st.session_state.resume_optimization_suggestions:
                    st.write(f"- {item}")

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

with tab3:
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

with tab4:
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
            report_profile = dict(profile)
            report_profile["role_mismatch_warning"] = st.session_state.role_mismatch_warning
            report_profile["resume_optimization_suggestions"] = st.session_state.resume_optimization_suggestions
            st.session_state.final_report = build_final_report(records, report_profile)
            st.session_state.report_json = json.dumps(st.session_state.final_report, ensure_ascii=False, indent=2)
            st.session_state.report_markdown = report_to_markdown(st.session_state.final_report)
            st.success("正式评分报告已生成。")
            autosave_current_session(status="completed")

    report = st.session_state.final_report

    if report:
        st.markdown("### 总体结果")
        col_a, col_b, col_c, col_d, col_e = st.columns(5)
        col_a.metric("总分", f"{report['total_score']} / 100")
        col_b.metric("等级", report["level"])
        col_c.metric("目标岗位", report.get("target_role") or "未明确")
        col_d.metric("难度", report.get("difficulty") or "未明确")
        col_e.metric("回答数量", report["interview_summary"]["answer_count"])

        st.markdown("### 五维度能力雷达图")
        render_radar_chart(report.get("dimension_details", {}))
        st.caption("雷达图用于页面展示，JSON 和 Markdown 下载仍保留结构化评分数据。")

        st.markdown("### 维度得分详情")
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

        card_a, card_b, card_c = st.columns(3)
        with card_a:
            render_bullet_card("表现亮点", report.get("strengths", []))
        with card_b:
            render_bullet_card("主要问题", report.get("main_problems", []))
        with card_c:
            render_bullet_card("后续提升建议", report.get("recommendations", []))

        st.markdown("### 简历与岗位匹配建议")
        if report.get("role_mismatch_warning"):
            st.warning(report.get("role_mismatch_warning"))
        resume_suggestions = report.get("resume_optimization_suggestions", [])
        if resume_suggestions:
            for item in resume_suggestions[:5]:
                st.write(f"- {item}")
        else:
            st.write("本次未发现明显简历与岗位方向冲突，建议继续强化与目标岗位相关的项目表达。")

        st.markdown("### 错题与薄弱知识点总结")
        for item in report.get("weak_points_summary", []):
            st.write(f"- {item}")

        st.markdown("### 学习建议推荐")
        for item in report.get("learning_recommendations", []):
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
