# AI 模拟面试与能力提升平台

## 1. 项目简介

本项目是一个基于 Streamlit 的本地 Web 应用，面向计算机相关专业学生和求职者，提供从简历解析、岗位画像、RAG 知识点检索、AI 模拟面试、回答分析到评分报告生成的一体化训练流程。

系统当前以本地运行和比赛演示为主要使用方式，云端部署不是必须条件。如需上线部署，可在后续根据实际服务器、密钥管理和隐私合规要求扩展。

## 2. 项目背景与目标

本项目用于“2026 年利兹科技月 AI 模拟面试与能力提升软件开发赛题”。赛题要求系统能够理解简历内容，围绕目标岗位开展模拟面试，并给出能力诊断与提升建议。

项目目标是构建一个稳定、可解释、可演示的闭环系统：

简历输入/上传 -> 简历解析 -> 候选人画像 -> RAG 知识检索 -> LLM + RAG 协同出题 -> 连续追问 -> 回答分析 -> 五维度评分报告 -> 能力成长复盘。

## 3. 核心功能

- 支持 TXT / PDF / DOCX 简历上传，也支持直接粘贴简历文本。
- 支持结构化简历解析和本地规则 fallback。
- 支持目标岗位选择与面试难度选择。
- 支持候选人画像、面试重点和简历-岗位匹配提醒。
- 支持 RAG 知识库检索和岗位导向选题。
- 支持 LLM 生成自然面试问题，并保留规则出题 fallback。
- 支持连续项目追问和基础知识追问。
- 支持每道题的 RAG 出题依据、期望要点和参考答案展示。
- 支持回答覆盖度、关键词、逻辑性和完整性分析。
- 支持五维度评分报告、弱点总结、学习建议和简历优化建议。
- 支持 LLM 对报告文字进行润色，LLM 不可用时自动使用本地规则。
- 支持评分报告 Markdown、JSON、完整长图 PNG 和摘要海报 PNG 导出。
- 支持不完整面试报告提醒。
- 支持面试历史、报告下载、演示模式和能力成长曲线。

## 4. 系统亮点

- 形成完整闭环：从简历到面试再到评分报告，不停留在单点功能。
- RAG 与 LLM 分工清晰：RAG 提供知识依据，LLM 负责自然表达和上下文追问。
- fallback 机制完整：LLM 不可用、超时或返回异常时，系统仍可完成演示。
- 报告可解释：评分基于回答记录、题目类型、覆盖率和岗位匹配证据。
- 适合比赛展示：支持本地运行、样例数据、演示模式和 Markdown / JSON 报告下载。

## 5. 技术栈

- Python
- Streamlit
- JSON 本地知识库
- OpenAI-compatible LLM API
- 阿里云百炼 / DashScope 兼容模型接口
- pdfplumber，用于 PDF 简历读取
- python-docx，用于 DOCX 简历读取
- python-dotenv，用于本地环境变量配置
- requests，用于 LLM API 调用
- Pillow，用于评分报告 PNG 图片导出

## 6. 系统功能流程

```text
用户输入或上传简历
  -> 简历文本读取
  -> 结构化简历解析
  -> 候选人画像与岗位匹配分析
  -> RAG 知识点检索
  -> LLM + RAG 生成面试题
  -> 用户回答
  -> 回答分析与追问
  -> 生成五维度评分报告
  -> 下载报告 / 查看成长曲线
```

## 7. 项目目录结构

```text
ai_interview_platform_day1/
├─ app.py
├─ start_app.bat
├─ requirements.txt
├─ README.md
├─ .env.example
├─ data/
│  ├─ knowledge_base.json
│  └─ sample_resume.txt
├─ demo/
│  ├─ sample_resume_ai_app.txt
│  ├─ sample_resume_backend.txt
│  ├─ sample_resume_frontend.txt
│  ├─ sample_resume_data_analysis.txt
│  ├─ sample_resume_testing.txt
│  ├─ demo_answers.md
│  ├─ sample_answers_backend.md
│  ├─ sample_answers_frontend.md
│  ├─ sample_answers_ai_app.md
│  ├─ sample_answers_data_analysis.md
│  ├─ sample_answers_testing.md
│  ├─ README.md
│  └─ demo_walkthrough.md
├─ src/
│  ├─ llm_client.py
│  ├─ llm_interviewer.py
│  ├─ llm_feedback_polisher.py
│  ├─ resume_file_loader.py
│  ├─ resume_parser.py
│  ├─ profile_generator.py
│  ├─ rag_retriever.py
│  ├─ rag_display.py
│  ├─ interviewer.py
│  ├─ answer_analyzer.py
│  ├─ evaluator.py
│  ├─ product_features.py
│  └─ session_manager.py
├─ scripts/
│  └─ self_check.py
├─ docs/
│  ├─ PROJECT_CONTEXT.md
│  ├─ OPTIMIZATION_PLAN.md
│  └─ Project_Design_Document.md
└─ outputs/
   ├─ sessions/
   └─ reports/
```

## 8. 本地运行方式

建议使用虚拟环境运行：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

如果已经创建过虚拟环境，日常运行可使用：

```bash
.venv\Scripts\activate
streamlit run app.py
```

Windows 一键启动：

```text
双击 start_app.bat
```

如果启动时出现 `No Python at ...WindowsApps...`，通常表示本地 `.venv` 绑定的 Python 路径已经失效。可以删除并重建虚拟环境后重新安装依赖。

运行自检：

```bash
python scripts/self_check.py
```

## 9. LLM API 配置说明

复制配置模板：

```bash
copy .env.example .env
```

复制 `.env.example` 为 `.env`，并在 `.env` 中填写自己的 API 配置：

```env
USE_LLM=true
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen3.7-plus
```

备用模式测试：

```env
USE_LLM=false
```

注意：不要把真实 API Key 写入 README、截图、提交记录或 `.env.example`。`.env` 文件应只保存在本地。

## 10. RAG 知识库说明

知识库文件位于：

```text
data/knowledge_base.json
```

每条知识点包含 ID、分类、标签、难度、题型、参考问题、参考答案、期望回答要点、追问方向和项目场景。系统会根据候选人画像、目标岗位、难度和最近使用过的知识点进行检索与排序。

为了避免历史数据断裂，部分旧知识点 ID 会保留内部兼容字段，同时在 UI 和报告中使用 `display_id`、`display_category`、`display_topic` 展示更友好的名称。

## 11. 评分反馈体系

最终报告采用五维度评分，权重保持固定：

| 维度 | 权重 |
|---|---:|
| 基础知识掌握程度 | 25% |
| 项目理解深度 | 25% |
| 回答逻辑性 | 20% |
| 表达完整性 | 15% |
| 岗位匹配度 | 15% |

LLM 只用于润色报告文字，不负责随意修改分数、权重或题目数量。若 LLM 不可用，系统会使用本地规则生成报告。

## 12. 演示模式说明

项目提供演示样例简历和回答材料，便于比赛录屏或现场演示。演示数据均为虚构内容，不应使用真实个人简历或真实面试记录上传到公开仓库。

`demo/` 目录中的示例简历均为虚构内容，可用于演示模式和视频录制。当前提供后端开发、前端开发、AI 应用开发、数据分析和软件测试五类岗位样例，并配套通用回答模板与岗位回答模板。

推荐演示流程：

1. 启动应用。
2. 选择目标岗位和难度。
3. 加载样例简历或粘贴简历文本。
4. 解析简历并查看候选人画像。
5. 查看 RAG 推荐问题和出题依据。
6. 进行 3-8 轮模拟面试。
7. 生成评分报告并下载 Markdown / JSON。
8. 展示能力成长曲线。

## 13. 能力成长曲线说明

系统会基于本地历史面试报告生成能力成长曲线，比较多次面试中的总分和五维度变化，并给出后续提升建议。若 LLM 可用，系统会对成长分析文字进行润色；若 LLM 超时或关闭，则使用本地规则分析。

## 14. 安全与隐私说明

- 本项目默认本地运行，数据主要保存在本机。
- `.env` 不应提交到 GitHub。
- 真实简历、真实面试历史和包含个人隐私的报告不应上传到公开仓库。
- API Key 应通过环境变量配置，不应硬编码在源码中。
- 当前系统适合作为比赛和学习项目，不宣称具备生产级安全合规能力。

## 15. AI 辅助开发说明

本项目在开发过程中使用 AI 辅助进行功能设计、代码优化、文档整理和测试思路梳理。核心实现仍围绕明确的软件工程目标展开：保持闭环稳定、保留 fallback、避免硬编码密钥、使用结构化数据支撑评分与报告。

## 16. 常见问题

**不配置 LLM 可以运行吗？**

可以。设置 `USE_LLM=false` 后，系统会使用本地规则完成简历解析 fallback、出题 fallback、回答分析和报告生成。

**为什么不挂 VPN 时可能超时？**

LLM API 请求需要访问对应服务端点。如果本地网络到 `dashscope.aliyuncs.com` 连接不稳定，可能出现 timeout。可以检查网络、地区端点、代理设置和 timeout 配置。

**报告分数是 LLM 打的吗？**

不是。分数由本地规则根据回答记录计算，LLM 只负责润色文字反馈。

**可以部署到云端吗？**

可以作为后续扩展，但当前提交以本地运行和演示视频为主，不默认包含云部署方案。

## 17. 提交说明

提交 GitHub 前请确认：

- 已运行 `python scripts/self_check.py`。
- `.env` 未提交。
- `.env.example` 不包含真实密钥。
- `outputs/sessions/`、`outputs/reports/` 中不包含真实个人数据。
- README、设计文档、演示材料与当前功能一致。
- 演示数据均为虚构样例。

推荐提交命令：

```bash
python scripts/self_check.py
git status
git add .
git status
git commit -m "Finalize submission package"
git push
```

可选标签：

```bash
git tag final-submission-checkpoint
git push origin final-submission-checkpoint
```

如果 GitHub 推送因网络失败，请切换网络后重试。不要提交 `.env`、`.venv/`、真实简历或本地面试历史。
