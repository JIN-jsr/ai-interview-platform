# AI 模拟面试与能力提升平台项目设计文档

## 1. 项目背景与目标

本项目面向“AI 模拟面试与能力提升”软件开发赛题，目标是为计算机相关专业学生提供一个本地可运行、过程可解释、结果可复盘的模拟面试训练平台。系统以简历为入口，结合目标岗位、RAG 知识库和 LLM 生成能力，完成模拟面试、回答分析、五维度评分和后续学习建议。

## 2. 需求分析

系统需要支持简历输入、岗位选择、难度选择、知识点检索、连续面试、回答分析、评分报告、报告导出、历史记录和演示数据。考虑比赛演示环境的不确定性，所有关键 LLM 能力都必须有本地规则 fallback，确保无密钥、网络超时或模型不可用时仍能跑通完整流程。

## 3. 系统总体架构

![系统架构图](assets/system_architecture.png)

图 1 系统架构图。该图用于展示整体流程，文字说明和下方流程是架构解释的主要依据。

```text
简历输入
→ 简历解析
→ 候选人画像
→ RAG 检索
→ 尝试调用 LLM
  ├─ 成功：使用 LLM + RAG 动态问题
  └─ 失败：使用本地规则备用问题
→ 连续模拟面试
→ 回答分析
→ 五维度评分
→ 报告与多格式导出
→ 历史记录与能力成长曲线
```

fallback 是 LLM 失败时的备用路径，不会与成功的 LLM 出题同时生效。

## 4. 技术栈与运行环境

| 类别 | 技术 |
|---|---|
| Web 框架 | Streamlit |
| 开发语言 | Python |
| 知识库 | 本地 JSON |
| LLM 接口 | OpenAI-compatible Chat Completions API |
| 简历读取 | pdfplumber、python-docx、TXT |
| 配置管理 | python-dotenv |
| 网络请求 | requests |
| 图片导出 | Pillow |
| 推荐运行环境 | Windows 本地虚拟环境 |

已在本地验证的运行环境包括 Python 3.12.13 与 Streamlit 1.58.0。不同机器可按 `requirements.txt` 重新安装依赖。

## 5. 核心功能模块

| 功能 | 主要文件 | 说明 |
|---|---|---|
| 主界面与流程编排 | `app.py` | Streamlit 页面、会话状态、导航与下载 |
| 简历文件读取 | `src/resume_file_loader.py` | TXT / PDF / DOCX 文本读取 |
| 简历解析 | `src/resume_parser.py` | LLM 解析与本地启发式 fallback |
| 候选人画像 | `src/profile_generator.py` | 技能、项目、面试重点与薄弱项 |
| 岗位匹配与产品功能 | `src/product_features.py` | 岗位关键词、错配提醒、成长分析 |
| RAG 检索 | `src/rag_retriever.py` | 本地可解释关键词检索 |
| RAG 展示映射 | `src/rag_display.py` | 面向 UI 的知识点展示名称 |
| LLM 面试官 | `src/llm_interviewer.py` | LLM + RAG 题目生成 |
| 面试流程 | `src/interviewer.py` | 追问、fallback、题目元数据 |
| 回答分析 | `src/answer_analyzer.py` | 覆盖率、关键词、逻辑与临时评分 |
| 最终评分报告 | `src/evaluator.py` | 五维度评分、报告 JSON / Markdown |
| PNG 报告导出 | `src/report_image_exporter.py` | 完整长图与摘要海报 |
| 历史会话 | `src/session_manager.py` | 本地面试记录保存与切换 |

## 6. 简历解析与候选人画像

![简历输入与上传](assets/resume_analysis_01_input.png)

图 2 简历文件上传、手动输入与解析入口。系统支持手动输入和 TXT / PDF / DOCX 文件上传，并支持多文件材料合并。

![结构化候选人画像](assets/resume_analysis_02_candidate_profile.png)

图 3 结构化候选人画像、面试重点与潜在薄弱项。画像结果用于后续 RAG 检索和面试重点控制。

![岗位匹配提醒](assets/resume_analysis_03_role_match.png)

图 4 简历方向判断、岗位匹配提醒与针对性优化建议。

简历解析优先尝试 LLM；若 LLM 未启用、超时或返回异常，系统会切换到本地规则解析。岗位匹配模块根据简历目标方向、技能关键词和项目描述判断是否与当前选择岗位存在偏差，并给出温和提醒和简历优化建议。

## 7. RAG 知识库设计

知识库位于 `data/knowledge_base.json`，采用本地 JSON 结构。条目包含 `id`、`category`、`tags`、`difficulty`、`question_type`、`question`、`answer`、`expected_points`、`follow_up`、`related_project_scenarios`、`bad_answer_signals` 和 `source`。

构建流程：

```text
资料来源整理
→ 知识点筛选
→ 内容清洗与去重
→ 分类、标签与难度标注
→ 问题与参考答案设计
→ expected_points 与追问方向设计
→ JSON 校验
→ Top-K 检索测试
→ 人工相关性检查
```

![RAG 出题依据](assets/rag_evidence.png)

图 5 RAG 出题依据展示。该截图展示的是可解释的检索依据、知识点和期望要点，不是隐藏推理链。

当前检索采用本地关键词匹配与岗位导向排序，没有声称使用向量数据库。这样做的优势是可复现、无需额外服务、可解释性强、适合离线和比赛演示。

## 8. LLM、RAG 与规则 fallback 协同机制

RAG 决定“问什么”，LLM 决定“怎么问”。系统会把候选人画像、最近对话、RAG 条目和 fallback 模板题提供给 LLM，让其生成自然中文问题，并要求保留 `knowledge_id`、`expected_points`、`reference_answer` 和 `reason` 等元数据。

若 LLM 调用失败、返回格式异常、未启用或生成了近期重复知识点，系统使用本地规则备用题目，并记录 `generated_by=rule_fallback` 和清晰的 fallback 原因。若 LLM 成功，则 `generated_by=llm`，并移除 fallback 警告。

## 9. 连续面试与回答分析

![模拟面试工作区](assets/interview_workspace.png)

图 6 模拟面试工作区。该截图用于展示当前问题、问题详情、出题依据和实时面试状态，不要求必须出现回答输入框。

回答分析会记录每轮问题、回答、题型、知识点、生成方式和分析结果。分析内容包括关键词、覆盖率、缺失要点、表达逻辑、完整性和临时评分。用户可以修改并重新提交最近一次回答，系统会回滚对应记录并重新生成后续问题。

## 10. 五维度评分与报告设计

最终报告采用固定五维度评分：

| 维度 | 权重 |
|---|---:|
| 基础知识掌握程度 | 25% |
| 项目理解深度 | 25% |
| 回答逻辑性 | 20% |
| 表达完整性 | 15% |
| 岗位匹配度 | 15% |

![评分报告仪表盘](assets/final_report_dashboard.png)

图 7 评分报告仪表盘。该图展示页面中的总分、等级、五维能力、题型分布、回答稳定性和岗位能力覆盖。

LLM 只参与文字润色，不改变评分权重、题目数量或分数。报告支持 JSON、Markdown、完整长图 PNG 和摘要海报 PNG 导出。摘要海报示例见 `assets/report_summary_poster.png`，完整长图示例见 `assets/report_full_long.png`。

## 11. 历史记录与能力成长曲线

系统将本地面试会话保存到 `outputs/sessions/`，支持历史切换、重命名、删除和报告复盘。能力成长曲线会比较多次报告中的总分和五维度变化。

![能力成长曲线](assets/ability_growth_curve.png)

图 8 能力成长曲线，用于展示历史报告对比、总分变化和维度发展趋势。

## 12. 用户界面与交互设计

界面采用黑白灰简洁风格，包含首页、系统介绍、模拟面试工作台、RAG 知识库、自检页和能力成长曲线。侧边栏提供历史面试、演示模式和更多功能入口。报告页使用卡片、雷达图、指标区和导出按钮组织信息，避免把原始 JSON 作为主界面重点。

## 13. 安全、隐私与 API Key 管理

系统默认本地运行，API Key 通过 `.env` 管理，`.env` 已在 `.gitignore` 中忽略。真实简历、真实面试记录和真实报告不应提交到公开仓库。`.env.example` 只保留占位变量。当前项目适合比赛和教学演示，不宣称具备生产级隐私合规能力。

## 14. 系统测试与运行结果

| 测试项目 | 测试环境 | 测试输入 | 预期结果 | 实际结果 | 结论 |
|---|---|---|---|---|---|
| 自检脚本 | Windows / Python 3.12.13 | `python scripts/self_check.py` | 无 ERROR | 已通过 | 通过 |
| 依赖导入 | 本地虚拟环境 | requirements.txt | 依赖可导入 | 已通过 | 通过 |
| 知识库校验 | 本地 JSON | `data/knowledge_base.json` | JSON 有效且字段完整 | 已通过 | 通过 |
| 无密钥模式 | `USE_LLM=false` | 虚构简历 | fallback 可跑通 | 待作者完成实测 | 待确认 |
| 有效 API 模式 | `USE_LLM=true` | 虚构简历与有效 Key | LLM 出题与润色可用 | 待作者完成实测 | 待确认 |
| 报告导出 | 本地页面 | 完成面试记录 | Markdown / JSON / PNG 可下载 | 待作者完成实测 | 待确认 |
| 全新下载复现 | GitHub ZIP | 新虚拟环境 | 可安装并运行 | 待作者完成实测 | 待确认 |

## 15. AI 辅助开发与人工审查

| 工作范围 | AI 辅助内容 | 人工修改与验证 |
|---|---|---|
| 需求拆解 | 梳理比赛需求与闭环流程 | 人工确认功能范围 |
| 模块脚手架 | 拆分简历、RAG、面试、评分模块 | 人工运行和迭代 |
| Prompt 设计 | 设计结构化输出约束 | 人工检查 JSON 字段 |
| fallback 保留 | 检查 LLM 失败路径 | 人工测试 `USE_LLM=false` |
| Streamlit 状态 | 排查会话切换和按钮状态 | 人工交互验证 |
| RAG 展示 | 修正展示名称和岗位相关性 | 人工检查页面文案 |
| 报告排版 | 迭代仪表盘和 PNG 导出 | 人工查看截图 |
| 文档审查 | 对齐 README、设计文档和清单 | 人工最终确认 |

## 16. 创新点、局限性与后续展望

创新点：

- 将简历画像、RAG 检索、LLM 出题和评分报告串成完整训练闭环。
- 保留 RAG 证据和题目元数据，使问题可追溯。
- 通过规则 fallback 保证演示稳定性。
- 报告同时提供评分、弱点、学习建议和能力成长分析。

局限性：

- 当前检索仍以本地关键词匹配为主，未接入真正向量数据库。
- 当前系统主要面向本地演示，未完成生产级权限、审计和云部署。
- 评分规则仍是启发式方法，后续可结合更多样本校准。

后续可继续扩展知识库质量，引入 Embedding 与向量检索，增加更多岗位模板，完善语音面试、报告排版和云端部署能力。
