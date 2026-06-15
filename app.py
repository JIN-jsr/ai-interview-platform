import json
from datetime import datetime

import streamlit as st

from src.llm_client import get_llm_config, is_llm_enabled
from src.profile_generator import generate_profile_from_parsed_resume
from src.resume_file_loader import read_uploaded_resume
from src.resume_parser import parse_resume, simple_resume_summary

st.set_page_config(
    page_title="AI Mock Interview Platform",
    page_icon="🎙️",
    layout="wide"
)

st.title("AI 模拟面试与能力提升平台")
st.caption("Day 2 MVP：支持 TXT/PDF/DOCX 简历读取，结构化简历解析，用户画像与面试重点生成")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "parsed_resume" not in st.session_state:
    st.session_state.parsed_resume = None
if "profile" not in st.session_state:
    st.session_state.profile = None
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

with st.sidebar:
    st.header("设置")
    target_role = st.selectbox(
        "目标岗位",
        ["后端开发", "前端开发", "AI应用开发", "数据分析", "软件测试"]
    )
    difficulty = st.selectbox(
        "面试难度",
        ["基础", "中等", "困难"]
    )

    st.divider()
    st.subheader("LLM 状态")
    config = get_llm_config()
    if is_llm_enabled():
        st.success("LLM 已启用")
        st.write(f"Model: {config['model_name']}")
    else:
        st.warning("LLM 未启用，将使用本地规则解析")
        st.caption("配置 .env 后可启用大模型结构化解析")

    st.divider()
    st.write("当前版本：Day 2 简历解析模块")
    st.write("下一步：扩展 RAG 知识库并实现检索提问")

tab1, tab2, tab3 = st.tabs(["1. 简历输入与解析", "2. 模拟面试", "3. 评分报告"])

with tab1:
    st.subheader("输入或上传简历")

    uploaded_file = st.file_uploader(
        "上传简历文件，可选 TXT / PDF / DOCX",
        type=["txt", "pdf", "docx"]
    )

    uploaded_text = ""
    if uploaded_file is not None:
        try:
            uploaded_text = read_uploaded_resume(uploaded_file)
            if uploaded_text:
                st.success(f"已读取文件：{uploaded_file.name}")
            else:
                st.warning("文件已上传，但没有读取到有效文本。")
        except Exception as exc:
            st.error(f"读取文件失败：{exc}")

    default_text = uploaded_text or st.session_state.resume_text

    resume_text = st.text_area(
        "也可以直接粘贴简历文本",
        value=default_text,
        height=280,
        placeholder="例如：教育背景、技术能力、项目经历、实习经历、竞赛经历……"
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        parse_btn = st.button("解析简历并生成画像", type="primary")
    with col2:
        save_btn = st.button("保存解析结果 JSON")
    with col3:
        clear_btn = st.button("清空当前内容")

    if clear_btn:
        st.session_state.messages = []
        st.session_state.resume_text = ""
        st.session_state.parsed_resume = None
        st.session_state.profile = None
        st.session_state.interview_started = False
        st.rerun()

    if parse_btn:
        if not resume_text.strip():
            st.warning("请先输入或上传简历内容。")
        else:
            st.session_state.resume_text = resume_text
            with st.spinner("正在解析简历并生成用户画像……"):
                parsed_resume = parse_resume(resume_text, prefer_llm=True)
                profile = generate_profile_from_parsed_resume(
                    parsed_resume=parsed_resume,
                    target_role=target_role,
                    difficulty=difficulty
                )

            st.session_state.parsed_resume = parsed_resume
            st.session_state.profile = profile
            st.success("简历解析完成。")

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
        st.caption(f"Parser: {parser_type}")
        if "_llm_error" in st.session_state.parsed_resume:
            st.warning(f"LLM 调用失败，已自动切换到本地解析。错误：{st.session_state.parsed_resume['_llm_error']}")
        st.json(st.session_state.parsed_resume)

    if st.session_state.profile:
        st.markdown("### 用户画像与面试重点")
        st.json(st.session_state.profile)

with tab2:
    st.subheader("文字版模拟面试")

    if st.session_state.profile:
        st.info("已检测到用户画像，可以开始面试。")
        if st.button("开始面试", type="primary"):
            st.session_state.interview_started = True
            if not st.session_state.messages:
                first_question = (
                    "你好，我是今天的 AI 技术面试官。请你先用 1 分钟做一个简短的自我介绍，"
                    "重点说明你的技术栈、项目经历以及目标岗位。"
                )
                st.session_state.messages.append({"role": "assistant", "content": first_question})
    else:
        st.warning("请先在「简历输入与解析」页面生成用户画像。")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if st.session_state.interview_started:
        user_answer = st.chat_input("请输入你的回答……")
        if user_answer:
            st.session_state.messages.append({"role": "user", "content": user_answer})

            question_count = len([m for m in st.session_state.messages if m["role"] == "assistant"])
            profile = st.session_state.profile or {}
            projects = profile.get("project_names", [])
            skills = profile.get("detected_skills", [])

            if question_count == 1:
                project_hint = projects[0] if projects else "你简历中最重要的一个项目"
                next_question = f"请详细介绍一下「{project_hint}」，包括项目背景、你的职责和使用的核心技术。"
            elif question_count == 2:
                next_question = "这个项目中你遇到的最大技术难点是什么？你是如何解决的？"
            elif question_count == 3:
                skill_hint = skills[0] if skills else "你熟悉的一项技术"
                next_question = f"接下来进入基础知识考察。请你解释一下 {skill_hint} 的一个核心概念，并说明它在项目中的应用。"
            else:
                next_question = "Day 2 版本暂时到这里。Day 3 将接入更完整的 RAG 知识库检索和基础知识提问。"

            st.session_state.messages.append({"role": "assistant", "content": next_question})
            st.rerun()

with tab3:
    st.subheader("面试评分报告")
    st.info("Day 2 版本暂时展示报告区域。第 5 天会完成自动评分与反馈。")

    demo_report = {
        "基础知识掌握程度": "待面试结束后生成",
        "项目理解深度": "待面试结束后生成",
        "回答逻辑性": "待面试结束后生成",
        "表达完整性": "待面试结束后生成",
        "岗位匹配度": "待面试结束后生成"
    }
    st.json(demo_report)
