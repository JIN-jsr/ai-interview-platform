# RAG 知识库构建说明

## 1. 知识库位置

```text
data/knowledge_base.json
```

知识库数量会随版本更新。运行以下命令可查看当前有效条目数量：

```bash
python scripts/self_check.py
```

## 2. 实际 JSON 字段

当前知识库条目包含以下字段：

| 字段 | 说明 |
|---|---|
| `id` | 知识点唯一标识 |
| `category` | 分类，例如 MySQL、Redis、AI / RAG / LLM 应用 |
| `tags` | 技术标签，用于检索和展示 |
| `difficulty` | 难度，当前为 `easy`、`medium`、`hard` |
| `question_type` | 题型，例如 `concept`、`principle`、`scenario` |
| `question` | 面试问题 |
| `answer` | 参考答案 |
| `expected_points` | 期望回答要点 |
| `bad_answer_signals` | 常见薄弱回答信号 |
| `follow_up` | 可追问方向 |
| `related_project_scenarios` | 可关联项目场景 |
| `source` | 来源说明 |

示例：

```json
{
  "id": "mysql_index_001",
  "category": "MySQL",
  "tags": ["MySQL", "索引", "慢查询"],
  "difficulty": "medium",
  "question_type": "principle",
  "question": "MySQL 索引为什么能提升查询性能？",
  "answer": "索引通过额外的数据结构减少扫描范围，常见 B+ 树索引适合范围查询和排序，但会增加写入维护成本。",
  "expected_points": ["减少扫描范围", "B+树结构", "范围查询", "写入成本"],
  "bad_answer_signals": ["只说索引越多越好", "不能解释失效场景"],
  "follow_up": ["什么情况下索引可能失效？"],
  "related_project_scenarios": ["接口慢查询优化", "列表分页查询"],
  "source": "课程资料、官方文档与公开学习资料整理"
}
```

## 3. 构建流程

```text
资料来源整理
→ 知识点筛选
→ 内容清洗与去重
→ 分类与标签
→ 难度标注
→ 问题设计
→ 参考答案
→ expected_points
→ 追问方向
→ JSON 校验
→ Top-K 检索测试
→ 人工相关性检查
```

资料来源应优先选择课程资料、官方文档、经典教材和稳定公开资料。不要把未核验的私人经验或真实候选人回答直接写入知识库。

## 4. 实际检索逻辑

当前版本使用本地可解释关键词检索，不依赖向量数据库或外部 embedding 服务。检索因素包括：

- 简历解析后的技能关键词
- 目标岗位
- 面试难度
- 知识点 `category`
- 技术 `tags`
- `question` 与 `answer` 文本
- 岗位偏好词，例如后端岗位优先 MySQL、Redis、API、网络、操作系统、部署等方向
- 最近已经使用过的 `knowledge_id`
- 分类多样性

系统会尽量避免短时间重复使用同一个知识点，并在 UI 中展示 RAG 出题依据。

## 5. 为什么采用本地 JSON + 关键词检索

- 本地可复现，不需要数据库服务。
- 演示稳定，不依赖额外网络请求。
- 便于人工检查知识点、答案和期望要点。
- 适合比赛现场解释“为什么问这道题”。
- 对隐私更友好，简历和回答主要保留在本地。

## 6. 后续可扩展方向

后续可在保持当前 JSON 结构的基础上，引入 Embedding、Chroma 或 FAISS 做语义召回，再保留当前关键词检索作为 fallback。扩展时应继续保留 `id`、`expected_points`、`answer` 和 `follow_up`，保证评分和追问仍可解释。
