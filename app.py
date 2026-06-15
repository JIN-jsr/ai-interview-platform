import streamlit as st
from src.resume_parser import simple_resume_summary
from src.profile_generator import generate_basic_profile

st.set_page_config(
    page_title="AI Mock Interview Platform",
    page_icon="🎙️",
    layout="wide"
)

st.title("AI 模拟面试与能力提升平台")
st.caption("Day 1 MVP 页面：简历输入、画像展示、面试对话框、评分报告区域")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
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
    st.write("当前版本：Day 1 项目框架")
    st.write("下一步：接入 LLM、简历解析、RAG 知识库")

tab1, tab2, tab3 = st.tabs(["1. 简历输入", "2. 模拟面试", "3. 评分报告"])

with tab1:
    st.subheader("输入或粘贴简历")
    resume_text = st.text_area(
        "请粘贴你的简历文本",
        height=260,
        placeholder="例如：教育背景、技术能力、项目经历、实习经历、竞赛经历……"
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        parse_btn = st.button("生成用户画像 / 面试重点", type="primary")
    with col2:
        clear_btn = st.button("清空当前内容")

    if clear_btn:
        st.session_state.messages = []
        st.session_state.resume_text = ""
        st.session_state.profile = None
        st.session_state.interview_started = False
        st.rerun()

    if parse_btn:
        if not resume_text.strip():
            st.warning("请先输入简历内容。")
        else:
            st.session_state.resume_text = resume_text
            summary = simple_resume_summary(resume_text)
            st.session_state.profile = generate_basic_profile(
                resume_text=resume_text,
                target_role=target_role,
                difficulty=difficulty
            )
            st.success("已生成基础用户画像。")

            st.markdown("### 简历基础摘要")
            st.json(summary)

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
        st.warning("请先在「简历输入」页面生成用户画像。")

    chat_box = st.container()
    with chat_box:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    if st.session_state.interview_started:
        user_answer = st.chat_input("请输入你的回答……")
        if user_answer:
            st.session_state.messages.append({"role": "user", "content": user_answer})

            # Day 1 placeholder interviewer logic
            question_count = len([m for m in st.session_state.messages if m["role"] == "assistant"])
            if question_count == 1:
                next_question = "你简历中最重要的一个项目是什么？请说明项目背景、你的职责和使用的核心技术。"
            elif question_count == 2:
                next_question = "这个项目中你遇到的最大技术难点是什么？你是如何解决的？"
            elif question_count == 3:
                next_question = "接下来会进入基础知识考察。请你解释一下数据库索引的作用，以及它可能带来的缺点。"
            else:
                next_question = "Day 1 版本暂时到这里。后续版本将接入 RAG 知识库和自动评分模块。"

            st.session_state.messages.append({"role": "assistant", "content": next_question})
            st.rerun()

with tab3:
    st.subheader("面试评分报告")
    st.info("Day 1 版本暂时展示报告区域。第 5 天会完成自动评分与反馈。")

    demo_report = {
        "基础知识掌握程度": "待面试结束后生成",
        "项目理解深度": "待面试结束后生成",
        "回答逻辑性": "待面试结束后生成",
        "表达完整性": "待面试结束后生成",
        "岗位匹配度": "待面试结束后生成"
    }
    st.json(demo_report)
