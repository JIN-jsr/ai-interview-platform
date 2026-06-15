# AI 模拟面试与能力提升平台

本项目是利兹科技月 AI 模拟面试软件开发赛的 Day 1 MVP 框架。

## 当前已完成

- Streamlit 前端页面
- 简历文本输入框
- 基础用户画像展示
- 模拟面试聊天区域
- 评分报告展示区域
- 基础项目目录结构
- `.env.example` API Key 配置模板
- `requirements.txt` 依赖文件
- 简单知识库示例文件

## 技术栈

- Python
- Streamlit
- JSON
- python-dotenv

后续会加入：

- 大语言模型 API 调用
- RAG 知识库检索
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

macOS / Linux 使用：

```bash
source .venv/bin/activate
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 运行项目：

```bash
streamlit run app.py
```

4. 在浏览器中打开 Streamlit 自动给出的本地地址。

## API Key 配置说明

当前 Day 1 版本还没有真正调用大语言模型 API。

后续接入 API 时，请复制 `.env.example` 为 `.env`：

```bash
copy .env.example .env
```

然后在 `.env` 中填写自己的 API Key。

注意：不要把真实 `.env` 文件提交到 GitHub。

## Day 1 测试方式

运行系统后，可以复制 `data/sample_resume.txt` 中的内容到页面文本框，点击“生成用户画像 / 面试重点”，再进入“模拟面试”页面点击“开始面试”。
