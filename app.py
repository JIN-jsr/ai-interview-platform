import json
from datetime import datetime

import streamlit as st

from src.answer_analyzer import analyze_answer, summarize_interview_records
from src.evaluator import build_final_report, report_to_markdown
from src.interviewer import get_next_question, prepare_rag_items_for_interview
from src.llm_client import get_llm_config, is_llm_enabled
from src.profile_generator import generate_profile_from_parsed_resume
from src.rag_retriever import get_kb_stats, retrieve_by_profile, retrieve_by_query
from src.resume_file_loader import read_uploaded_resume
from src.resume_parser import parse_resume, simple_resume_summary

st.set_page_config(
    page_title="AI Mock Interview Platform",
    page_icon="🎙️",
    layout="wide"
)

st.title("AI 模拟面试与能力提升平台")
st.caption("Day 5 MVP：正式五维度评分反馈报告")

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
        st.caption("Day 4 暂时不依赖 LLM，提交前再配置即可")

    st.divider()
    st.subheader("RAG 知识库")
    kb_stats = get_kb_stats()
    st.write(f"知识条目数：{kb_stats['total_entries']}")

    st.divider()
    st.subheader("面试进度")
    assistant_count = len([m for m in st.session_state.messages if m.get("role") == "assistant"])
    st.write(f"已提出问题：{assistant_count}")
    st.write(f"已记录回答：{len(st.session_state.interview_records)}")
    st.write(f"上下文追问次数：{st.session_state.followup_count}")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. 简历输入与解析",
    "2. RAG 知识库",
    "3. 模拟面试",
    "4. 面试记录与分析",
    "5. 评分报告"
])

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
        st.session_state.rag_items = []
        st.session_state.rag_index = 0
        st.session_state.question_meta = []
        st.session_state.current_question_meta = None
        st.session_state.interview_records = []
        st.session_state.followup_count = 0
        st.session_state.final_report = None
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
                rag_items = retrieve_by_profile(profile, top_k=6)

            st.session_state.parsed_resume = parsed_resume
            st.session_state.profile = profile
            st.session_state.rag_items = rag_items
            st.session_state.rag_index = 0
            st.session_state.messages = []
            st.session_state.question_meta = []
            st.session_state.current_question_meta = None
            st.session_state.interview_records = []
            st.session_state.followup_count = 0
            st.session_state.final_report = None
            st.success("简历解析完成，并已生成 RAG 推荐问题。")

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
    st.subheader("RAG 知识库检索与检查")

    stats = get_kb_stats()
    st.markdown("### 知识库统计")
    st.json(stats)

    search_query = st.text_input(
        "输入关键词测试检索效果",
        placeholder="例如：Python MySQL Redis 后端开发 事务 索引"
    )

    if search_query:
        results = retrieve_by_query(search_query, top_k=8)
        st.markdown("### 检索结果")
        if not results:
            st.warning("没有检索到相关知识条目。")
        for item in results:
            with st.expander(f"Score {item.get('_score', 0)}｜{item.get('id')}｜{item.get('question')}"):
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
        st.info("Day 4 面试会记录上下文，并根据用户回答进行追问。")
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
                        followup_count=st.session_state.followup_count
                    )
                    st.session_state.messages.append({"role": "assistant", "content": first["question"]})
                    st.session_state.current_question_meta = first
                    st.session_state.question_meta.append(first)
        with col_reset:
            if st.button("重置面试"):
                st.session_state.messages = []
                st.session_state.interview_started = False
                st.session_state.rag_index = 0
                st.session_state.question_meta = []
                st.session_state.current_question_meta = None
                st.session_state.interview_records = []
                st.session_state.followup_count = 0
                st.session_state.final_report = None
                st.rerun()
    else:
        st.warning("请先在「简历输入与解析」页面生成用户画像。")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if st.session_state.interview_started:
        user_answer = st.chat_input("请输入你的回答……")
        if user_answer:
            st.session_state.messages.append({"role": "user", "content": user_answer})

            last_meta = st.session_state.current_question_meta or {}
            analysis = analyze_answer(last_meta, user_answer)

            st.session_state.interview_records.append({
                "question": last_meta.get("question", ""),
                "question_type": last_meta.get("type", "unknown"),
                "knowledge_id": last_meta.get("knowledge_id", ""),
                "reference_answer": last_meta.get("reference_answer", ""),
                "user_answer": user_answer,
                "analysis": analysis,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            next_info = get_next_question(
                profile=st.session_state.profile or {},
                history=st.session_state.messages,
                rag_items=st.session_state.rag_items,
                rag_index=st.session_state.rag_index,
                last_answer=user_answer,
                last_question_meta=last_meta,
                last_analysis=analysis,
                followup_count=st.session_state.followup_count
            )

            st.session_state.rag_index = next_info.get("rag_index", st.session_state.rag_index)
            st.session_state.followup_count = next_info.get("followup_count", st.session_state.followup_count)
            st.session_state.messages.append({"role": "assistant", "content": next_info["question"]})
            st.session_state.current_question_meta = next_info
            st.session_state.question_meta.append(next_info)
            st.rerun()

    with st.expander("本轮面试问题元数据（用于证明流程、RAG 与上下文追问）", expanded=False):
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
            title = f"第 {idx} 题｜{record.get('question_type')}｜临时评分 {record.get('analysis', {}).get('overall_temp_score')}/10"
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
    st.info("Day 5 已加入正式五维度评分：基础知识 25%、项目理解 25%、回答逻辑 20%、表达完整性 15%、岗位匹配度 15%。")

    records = st.session_state.interview_records
    profile = st.session_state.profile or {}

    col_report, col_clear_report = st.columns([1, 1])
    with col_report:
        generate_report_btn = st.button("生成正式评分报告", type="primary")
    with col_clear_report:
        if st.button("清空评分报告"):
            st.session_state.final_report = None
            st.rerun()

    if generate_report_btn:
        if not records:
            st.warning("还没有面试记录。请先完成至少几轮模拟面试。")
        else:
            st.session_state.final_report = build_final_report(records, profile)
            st.success("正式评分报告已生成。")

    report = st.session_state.final_report

    if report:
        st.markdown("### 总体结果")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("总分", f"{report['total_score']} / 100")
        col_b.metric("等级", report["level"])
        col_c.metric("回答数量", report["interview_summary"]["answer_count"])

        st.markdown("### 五维度评分")
        for dim, detail in report["dimension_details"].items():
            score = float(detail["score"])
            st.write(f"**{dim}**（权重 {detail['weight']}）：{score} / 100")
            st.progress(min(100, int(score)) / 100)

        st.markdown("### 评分依据")
        for dim, detail in report["dimension_details"].items():
            with st.expander(f"{dim}｜{detail['score']} 分｜权重 {detail['weight']}"):
                for ev in detail.get("evidence", []):
                    st.write(f"- {ev}")

        st.markdown("### 表现较好的方面")
        for item in report.get("strengths", []):
            st.write(f"- {item}")

        st.markdown("### 主要问题")
        for item in report.get("main_problems", []):
            st.write(f"- {item}")

        st.markdown("### 后续提升建议")
        for item in report.get("recommendations", []):
            st.write(f"- {item}")

        st.markdown("### 报告原始 JSON")
        with st.expander("查看报告 JSON", expanded=False):
            st.json(report)

        json_text = json.dumps(report, ensure_ascii=False, indent=2)
        md_text = report_to_markdown(report)

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
            "临时平均分": summary["average_temp_score"],
            "高频技术关键词": summary["frequent_keywords"],
            "常见问题": summary["common_problems"],
            "提示": "完成几轮面试后，点击“生成正式评分报告”。"
        })
