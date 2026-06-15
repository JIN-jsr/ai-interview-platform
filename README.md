# AI 模拟面试与能力提升平台

本项目是利兹科技月 AI 模拟面试软件开发赛的 Day 2 MVP 版本。

## 当前已完成

Day 1：

- Streamlit 前端页面
- 简历文本输入框
- 基础用户画像展示
- 模拟面试聊天区域
- 评分报告展示区域
- 基础项目目录结构

Day 2：

- 支持 TXT / PDF / DOCX 简历上传
- 支持直接粘贴简历文本
- 新增结构化简历解析模块
- 支持大语言模型解析，未配置 API 时自动使用本地规则解析
- 解析结果统一输出为 JSON
- 根据解析结果生成用户画像和面试重点
- 支持下载解析结果 JSON

## 技术栈

- Python
- Streamlit
- requests
- python-dotenv
- pdfplumber
- python-docx
- JSON

后续会加入：

- 更完整的 RAG 知识库
- 向量检索或关键词检索增强
- 连续面试流程控制
- 自动评分反馈
- 面试记录保存

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
│   └── evaluator.py
└── outputs/
    ├── logs/
    └── reports/
```

## 本地运行方法

1. 创建并进入虚拟环境：

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 运行项目：

```bash
streamlit run app.py
```

## LLM API Key 配置说明

当前版本支持 OpenAI-compatible API 格式。以阿里百炼 DashScope 兼容模式为例：

1. 复制 `.env.example` 为 `.env`

```bash
copy .env.example .env
```

2. 在 `.env` 中填写：

```text
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-plus
USE_LLM=true
```

如果不配置 API，系统仍然可以运行，会自动使用本地规则解析简历。

注意：不要把真实 `.env` 文件提交到 GitHub。

## Day 2 测试方式

运行系统后，可以：

1. 复制 `data/sample_resume.txt` 中的内容到页面文本框；
2. 或上传 TXT / PDF / DOCX 简历；
3. 点击“解析简历并生成画像”；
4. 检查页面是否输出“结构化简历解析结果”和“用户画像与面试重点”。

## Git 提交建议

```bash
git add .
git commit -m "Day 2 add structured resume parsing"
git push
```
