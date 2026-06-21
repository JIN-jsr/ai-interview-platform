# RAG 知识库构建说明

## 1. 知识库位置与当前规模

知识库文件：

```text
data/knowledge_base.json
```

当前有效条目数以 `python scripts/self_check.py` 和 [RAG 覆盖审计](rag_coverage_audit.md) 为准。本轮优化采取小规模、质量导向扩展：从 300 条增加到 330 条，每个目标岗位补充 6 条工程化、项目深挖或误区识别相关条目。

## 2. 五岗位覆盖

系统当前支持五个目标岗位：

- 后端开发
- 前端开发
- AI应用开发
- 数据分析
- 软件测试

岗位能力词库统一维护在 `src/product_features.py` 的 `ROLE_KEYWORDS` 中，RAG 检索、简历优化建议和报告中的岗位能力覆盖共用该来源，避免多处词库不一致。

本轮重点补强：

- 软件测试：pytest、接口测试、异常场景、日志分析、回归测试、Flaky Test、性能测试、LLM 输出测试。
- 前端开发：组件化、状态管理、跨域、性能优化、浏览器机制、安全和 E2E 测试。
- AI应用开发：RAG、结构化输出、JSON 校验、Token 成本、模型超时、fallback、Function Calling 和 API Key 管理。
- 数据分析：指标口径、数据清洗、A/B 测试、漏斗留存、相关与因果、报表对账。
- 后端开发：接口设计、MySQL 排查、缓存穿透、消息队列、高并发保护、发布与回滚。

## 3. JSON 字段

核心字段保持向后兼容：

| 字段 | 说明 |
|---|---|
| `id` | 知识点唯一标识 |
| `category` | 分类，例如 MySQL、Redis、AI / RAG / LLM 应用 |
| `tags` | 技术标签，用于检索、展示和评分 |
| `difficulty` | `easy`、`medium`、`hard` |
| `question_type` | `concept`、`principle`、`scenario`、`debugging`、`tradeoff`、`system_design`、`project` 等 |
| `question` | 面试问题 |
| `answer` | 参考答案 |
| `expected_points` | 评分优先使用的期望回答要点 |
| `bad_answer_signals` | 常见薄弱回答信号 |
| `follow_up` | 可追问方向 |
| `related_project_scenarios` | 可关联项目场景 |
| `source` | 来源说明 |

本轮新增可选字段：

| 字段 | 说明 |
|---|---|
| `common_mistakes` | 常见错误说法 |
| `misconceptions` | 常见误区 |
| `critical_errors` | 严重技术性错误 |
| `negative_signals` | 负向信号，保留兼容 |
| `evidence_requirements` | 希望候选人提供的证据 |
| `verification_questions` | 可用于追问验证的问题 |

旧条目不要求补齐这些可选字段，代码使用 `dict.get(...)` 安全读取。

## 4. 构建流程

```text
资料来源整理
→ 知识点筛选
→ 内容清洗与去重
→ 分类、标签与难度标注
→ 问题与参考答案设计
→ expected_points 与追问方向设计
→ 误区、关键错误和证据要求补充
→ JSON 校验
→ Top-K 检索测试
→ 人工相关性检查
→ 离线评分校准
```

资料来源应优先选择课程资料、官方文档、经典教材和稳定公开资料。不要把未核验的私人经验、真实候选人回答或真实简历内容直接写入知识库。

## 5. 实际检索逻辑

当前版本使用本地可解释关键词检索，没有接入外部向量数据库、embedding 服务、BM25 引擎或 rerank 模型。检索因素包括：

- 简历解析后的技能关键词；
- 目标岗位能力词；
- 面试难度；
- `category`、`tags`、`question`、`answer` 和 `expected_points`；
- 岗位导向排序；
- 最近已使用的 `knowledge_id`；
- 最近分类分布与主题多样性。

系统会尽量避免短时间重复使用同一个知识点，并限制单一分类连续主导面试。

## 6. 项目深挖与问题调度

正常 8 题左右的完整面试中，调度目标是：

- 1 道自我介绍或开场题；
- 3-4 道 RAG 知识或工程场景题；
- 有项目信息时至少 2 道真实项目深挖题；
- 至少 1 道上下文追问；
- 最后可补综合岗位匹配题。

如果接近面试结束时项目深挖或追问不足，`src/interviewer.py` 会优先补齐覆盖。若简历中项目证据不足，系统不编造项目经历，报告会降低项目证据置信度。

## 7. 误区与错误检测

`src/answer_analyzer.py` 会优先根据 `expected_points` 计算覆盖率，同时读取 `common_mistakes`、`misconceptions`、`critical_errors` 等可选字段。候选人明确说出严重误区时，会影响技术分和问题提示，但不会因为未提到可选高级点而过度扣分。

示例：

- MySQL：只要使用索引，查询就一定快。
- RAG：只要加入知识库就不会产生幻觉。
- 缓存穿透：布隆过滤器能保证零误判。
- 自动化测试：自动化测试可以完全替代人工测试。

## 8. 展示 ID 与用户友好表达

内部 `knowledge_id` 保留在 JSON 和会话记录中用于追溯。UI 和报告优先展示 `display_topic`、`display_category` 和友好的题型名称，避免把原始 ID 作为用户可见的薄弱点标题。

## 9. 为什么使用本地可解释检索

- 易于本地复现；
- 不依赖外部数据库或网络服务；
- 演示稳定；
- 检索证据透明；
- 方便人工校验；
- 更适合公开仓库和比赛演示中的隐私控制。

未来可以在保持当前 JSON 结构的基础上引入 embedding、向量检索或重排序模型，但应继续保留当前本地检索作为 fallback 或对照基线。

## 10. 验证方法

提交前建议运行：

```bash
python scripts/self_check.py
python scripts/scoring_calibration_check.py
```

其中 `self_check.py` 会检查知识库 JSON、重复 ID、expected_points、误区元数据、岗位词库、图片资源和文档链接；`scoring_calibration_check.py` 会验证低/中/高质量回答分数单调、格式化虚高限制、长文重复限制、误区扣分和软件测试词汇识别。
