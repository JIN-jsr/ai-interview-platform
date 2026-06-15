# AI 模拟面试与能力提升平台

本项目是利兹科技月 AI 模拟面试软件开发赛的 Day 6 版本。

## 项目简介

本系统面向计算机相关专业学生，提供简历驱动的 AI 模拟技术面试训练。系统支持简历输入或上传，自动生成用户画像与面试重点，并结合 RAG 知识库进行基础知识考察、项目经历深挖、连续追问和五维度评分反馈。

## 已完成核心闭环

```text
简历输入/解析
↓
用户画像与面试重点生成
↓
RAG 知识库检索
↓
连续文字模拟面试
↓
项目经历深挖
↓
基于回答内容的追问
↓
回答记录与分析
↓
五维度评分报告
```

## 功能清单

- TXT / PDF / DOCX 简历上传
- 直接粘贴简历文本
- 结构化简历解析 JSON
- 用户画像与面试重点
- 80 条 RAG 知识库
- RAG 检索测试页面
- 连续模拟面试
- 项目经历深挖
- 基于回答关键词的追问
- 回答分析与面试记录
- 正式五维度评分报告
- JSON / Markdown 报告下载
- LLM 配置状态与连接测试
- 项目自检脚本

## 技术栈

- Python
- Streamlit
- requests
- python-dotenv
- pdfplumber
- python-docx
- JSON

## 项目结构

```text
ai_interview_platform/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── data/
│   ├── knowledge_base.json
│   └── sample_resume.txt
├── src/
│   ├── llm_client.py
│   ├── prompts.py
│   ├── resume_file_loader.py
│   ├── resume_parser.py
│   ├── profile_generator.py
│   ├── rag_retriever.py
│   ├── interviewer.py
│   ├── answer_analyzer.py
│   └── evaluator.py
├── scripts/
│   └── self_check.py
├── docs/
│   ├── llm_config_guide.md
│   ├── rag_build_guide.md
│   ├── design_document_draft.md
│   ├── demo_script.md
│   ├── test_checklist.md
│   └── day6_notes.md
└── outputs/
    ├── logs/
    └── reports/
```

## 本地运行方法

### 1. 创建并激活虚拟环境

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行项目

```bash
streamlit run app.py
```

## LLM 配置

复制配置模板：

```bash
copy .env.example .env
```

编辑 `.env`：

```text
LLM_API_KEY=你的真实APIKey
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen3.7-plus
USE_LLM=true
```

然后重启项目，在“项目说明与自检”页面点击“测试 LLM 连接”。

详细教程见：

```text
docs/llm_config_guide.md
```

## RAG 知识库说明

知识库文件：

```text
data/knowledge_base.json
```

当前包含 80 条有效知识条目，覆盖 Python、Java、数据结构与算法、数据库、网络、操作系统、软件工程和 AI 应用等方向。

详细说明见：

```text
docs/rag_build_guide.md
```

## 自检脚本

在项目根目录运行：

```bash
python scripts/self_check.py
```

通过后会显示：

```text
=== Self check passed ===
```

## 提交前材料

- GitHub 仓库地址
- 项目设计文档
- 不超过 8 分钟演示视频

文档初稿和视频脚本见：

```text
docs/design_document_draft.md
docs/demo_script.md
docs/test_checklist.md
```

## Git 提交建议

```bash
git add .
git commit -m "Day 6 polish docs and LLM configuration support"
git push
```
