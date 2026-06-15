# AI 模拟面试与能力提升平台

本项目是利兹科技月 AI 模拟面试与能力提升软件开发赛的最终提交版本。

## 项目简介

本系统面向计算机相关专业学生，提供简历驱动的 AI 模拟技术面试训练。用户可以上传或粘贴简历，系统自动解析教育背景、技术栈、项目经历和目标岗位，生成用户画像与面试重点，并结合 RAG 知识库进行基础知识考察、项目经历深挖、连续追问和五维度评分反馈。

## 核心闭环

```text
简历输入/解析
↓
用户画像与面试重点生成
↓
RAG 知识库检索
↓
连续文字模拟面试
↓
项目经历深挖与上下文追问
↓
回答记录与分析
↓
五维度评分报告
```

## 已完成功能

- 支持 TXT / PDF / DOCX 简历上传
- 支持直接粘贴简历文本
- 支持 LLM 结构化简历解析，并提供本地规则解析 fallback
- 自动生成用户画像、面试重点和岗位匹配方向
- 内置 80 条计算机基础 RAG 知识库
- 支持 RAG 检索测试与基于简历的知识点匹配
- 支持连续文字模拟面试
- 支持项目经历深挖和基于回答内容的追问
- 支持面试记录、回答分析和临时评分
- 支持正式五维度评分报告
- 支持 JSON / Markdown 报告下载
- 支持 LLM 连接测试和项目自检脚本

## 评分维度

系统评分维度与赛题要求保持一致：

| 维度 | 权重 |
|---|---:|
| 基础知识掌握程度 | 25% |
| 项目理解深度 | 25% |
| 回答逻辑性 | 20% |
| 表达完整性 | 15% |
| 岗位匹配度 | 15% |

## 技术栈

- Python
- Streamlit
- requests
- python-dotenv
- pdfplumber
- python-docx
- JSON
- OpenAI-compatible LLM API

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
│   ├── Project_Design_Document.docx
│   ├── final_design_document.md
│   ├── llm_config_guide.md
│   ├── rag_build_guide.md
│   ├── demo_script.md
│   ├── test_checklist.md
│   └── day7_final_notes.md
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

### 3. 配置 LLM

复制配置模板：

```bash
copy .env.example .env
```

编辑 `.env`：

```text
LLM_API_KEY=你的真实APIKey
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen3.7-max
USE_LLM=true
```

如果 `qwen3.7-max` 不可用，可以改为 `qwen3.7-plus` 或 `qwen-plus`。

### 4. 启动项目

```bash
streamlit run app.py
```

### 5. 运行自检

```bash
python scripts/self_check.py
```

通过后应显示：

```text
=== Self check passed ===
```

## 提交材料

建议提交：

1. GitHub 仓库地址
2. 项目设计文档：`docs/Project_Design_Document.docx`
3. 不超过 8 分钟演示视频

## 安全说明

`.env` 文件保存真实 API Key，已经被 `.gitignore` 忽略。请不要将 `.env` 上传到 GitHub。仓库中只保留 `.env.example` 作为配置模板。
