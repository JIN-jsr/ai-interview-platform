# AI 模拟面试与能力提升平台

本项目是利兹科技月 AI 模拟面试软件开发赛的 Day 4 MVP 版本。

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
- 新增 RAG 检索模块
- 支持根据简历用户画像自动推荐基础知识问题
- 将 RAG 基础知识问题接入模拟面试流程

Day 4：

- 新增 `src/answer_analyzer.py` 回答分析模块
- 支持记录每一轮问题、用户回答、问题类型、知识点 ID 和参考答案
- 支持根据用户回答中的技术关键词进行项目追问
- 支持根据 RAG 回答缺失点进行基础知识追问
- 新增“面试记录与分析”页面
- 支持下载面试记录 JSON
- 页面侧边栏显示面试进度、回答数量和上下文追问次数

## 技术栈

- Python
- Streamlit
- requests
- python-dotenv
- pdfplumber
- python-docx
- JSON

## 本地运行方法

```bash
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Day 4 测试方式

1. 运行系统；
2. 在第 1 个页面粘贴或上传简历；
3. 点击“解析简历并生成画像”；
4. 打开“模拟面试”页面，点击“开始面试”；
5. 在项目问题中故意提到 `Redis`、`MySQL`、`缓存`、`API` 等关键词；
6. 检查系统是否围绕这些关键词继续追问；
7. 在 RAG 基础题中故意回答得简短一些；
8. 检查系统是否根据缺失点进行追问；
9. 打开“面试记录与分析”页面，查看每轮回答分析；
10. 下载面试记录 JSON。

## 当前说明

Day 4 暂时不依赖 LLM API，主要完成连续面试流程、上下文记忆和可解释回答分析。提交前建议启用 LLM，以增强简历解析、自然追问和最终反馈质量。

## Git 提交建议

```bash
git add .
git commit -m "Day 4 add contextual follow-up and answer analysis"
git push
```
