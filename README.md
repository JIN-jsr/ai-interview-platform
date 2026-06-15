# AI 模拟面试与能力提升平台

本项目是利兹科技月 AI 模拟面试软件开发赛的 Day 3 MVP 版本。

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

Day 3：

- 扩展 `data/knowledge_base.json` 至 80 条有效知识条目
- 覆盖 Python、Java、数据结构与算法、数据库与缓存、计算机网络、操作系统、软件工程与 AI 应用等方向
- 新增 RAG 检索模块 `src/rag_retriever.py`
- 支持基于关键词的本地知识库检索
- 支持根据简历用户画像自动推荐基础知识问题
- 新增 RAG 知识库检查页面
- 将 RAG 基础知识问题接入模拟面试流程

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
│   └── evaluator.py
└── outputs/
    ├── logs/
    └── reports/
```

## 本地运行方法

```bash
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## RAG 知识库说明

知识库文件位于：

```text
data/knowledge_base.json
```

每条知识包含：

- id
- category
- tags
- difficulty
- question
- answer
- follow_up
- source

当前 Day 3 使用本地关键词检索。检索流程为：

```text
简历解析结果 / 用户画像
↓
提取目标岗位、技能、项目关键词
↓
与知识库条目的 category、tags、question、answer 匹配
↓
按分数排序并做类别多样化
↓
返回相关基础知识问题
```

## LLM API Key 配置说明

当前版本支持 OpenAI-compatible API 格式。以阿里百炼 DashScope 兼容模式为例：

```text
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-plus
USE_LLM=true
```

如果不配置 API，系统仍然可以运行，会自动使用本地规则解析简历和本地 RAG 检索。

注意：不要把真实 `.env` 文件提交到 GitHub。

## Day 3 测试方式

1. 运行系统；
2. 在第 1 个页面粘贴或上传简历；
3. 点击“解析简历并生成画像”；
4. 查看系统匹配出的 RAG 基础知识问题；
5. 打开“RAG 知识库”页面，搜索 `Python MySQL Redis 后端`；
6. 打开“模拟面试”页面，开始面试；
7. 检查面试中是否出现与知识库相关的基础知识问题。

## Git 提交建议

```bash
git add .
git commit -m "Day 3 add RAG knowledge base and retrieval"
git push
```
