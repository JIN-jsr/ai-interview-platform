import re
from typing import Any, Dict, List


TECH_KEYWORDS = [
    "Python", "Java", "C++", "JavaScript", "Flask", "Django", "FastAPI", "Spring Boot",
    "MySQL", "Redis", "MongoDB", "SQLite", "PostgreSQL", "索引", "事务", "缓存",
    "HTTP", "HTTPS", "TCP", "UDP", "进程", "线程", "锁", "数据库", "接口",
    "机器学习", "深度学习", "PyTorch", "TensorFlow", "RAG", "API", "Git", "Docker",
    "LLM", "大模型API", "Prompt Engineering", "Embedding", "向量数据库",
    "Chroma", "LangChain", "Function Calling", "Agent", "Rerank", "Token 管理",
    "Go", "Gin", "RabbitMQ", "Kafka", "RESTful API", "接口设计", "微服务", "高并发",
    "分布式锁", "幂等性", "限流", "熔断", "降级", "监控告警", "异步任务", "消息队列",
    "本地消息表", "Lua", "Lua 脚本", "布隆过滤器", "数据库事务", "索引优化", "缓存一致性",
    "Kubernetes", "Milvus", "FAISS", "大语言模型", "大模型 API", "上下文管理", "上下文压缩",
    "结构化输出", "模型评估", "AI 工程化", "模型调用", "检索增强生成", "TypeScript",
    "Vue", "React", "Element Plus", "前端工程化", "组件化", "状态管理", "响应式布局",
    "测试用例设计", "等价类划分", "边界值分析", "判定表", "场景法", "错误推测",
    "冒烟测试", "回归测试", "接口测试", "自动化测试", "pytest", "Selenium",
    "Playwright", "Mock", "测试隔离", "fixture", "参数化", "Flaky Test",
    "性能测试", "压力测试", "负载测试", "稳定性测试", "TP95", "TP99",
    "吞吐量", "并发用户", "缺陷生命周期", "严重程度", "优先级", "缺陷管理",
    "日志分析", "异常场景", "测试数据准备", "发布准入", "安全测试", "可测试性",
    "LLM 输出测试", "Prompt 鲁棒性", "RAG 相关性测试", "JSON 合法性", "fallback 测试"
]

LOGIC_MARKERS = [
    "首先", "其次", "然后", "最后", "因为", "所以", "例如", "比如",
    "一方面", "另一方面", "因此", "总结", "结果", "目标", "问题", "方案"
]

SEMANTIC_GROUPS = [
    {"索引", "index", "b+树", "b树", "查询效率", "加速查询"},
    {"执行计划", "explain", "慢查询", "扫描行数", "type", "extra"},
    {"查询条件", "where", "过滤条件", "排序字段", "order by", "group by", "范围查询"},
    {"索引选择性", "选择性", "区分度", "基数", "cardinality"},
    {"事务", "transaction", "acid", "原子性", "一致性", "隔离性", "持久性"},
    {"缓存", "cache", "redis", "命中率", "过期时间", "淘汰策略"},
    {"接口", "api", "restful", "http", "请求", "响应"},
    {"接口设计", "restful api", "api设计", "路由", "参数校验", "响应结构"},
    {"消息队列", "rabbitmq", "kafka", "异步任务", "本地消息表", "削峰", "解耦"},
    {"高并发", "限流", "熔断", "降级", "幂等性", "分布式锁", "布隆过滤器"},
    {"微服务", "服务治理", "服务拆分", "监控告警", "可观测性", "恢复"},
    {"go", "gin", "fastapi", "spring boot", "flask", "后端框架"},
    {"网络", "tcp", "udp", "http", "https", "三次握手", "四次挥手"},
    {"操作系统", "进程", "线程", "锁", "内存", "调度"},
    {"部署", "docker", "linux", "nginx", "上线", "发布", "环境变量"},
    {"复杂度", "时间复杂度", "空间复杂度", "o(", "big-o"},
    {"异常", "错误处理", "try", "except", "日志", "回滚"},
    {"rag", "检索增强", "检索增强生成", "知识库", "召回", "生成", "grounding"},
    {"llm", "大模型", "大语言模型", "大模型api", "模型api", "api调用", "qwen", "openai"},
    {"prompt engineering", "prompt", "提示词", "提示工程", "system prompt", "user prompt"},
    {"embedding", "向量", "向量表示", "语义向量", "语义检索", "相似度"},
    {"向量数据库", "vector database", "chroma", "faiss", "milvus", "collection"},
    {"langchain", "chain", "retriever", "loader", "document", "chunk"},
    {"function calling", "函数调用", "工具调用", "tool call", "参数 schema"},
    {"agent", "智能体", "规划", "工具使用", "多步推理"},
    {"rerank", "reranker", "重排", "二次排序", "相关性排序"},
    {"token", "token 管理", "上下文窗口", "截断", "分块", "chunk", "成本控制"},
    {"上下文管理", "上下文压缩", "结构化输出", "json输出", "schema", "模型评估"},
    {"前端", "vue", "react", "typescript", "组件化", "状态管理", "响应式布局"},
    {"技术栈", "技术能力", "python", "go", "java", "flask", "fastapi", "gin", "mysql", "redis", "rabbitmq", "vue", "typescript"},
    {"测试", "测试用例", "等价类", "边界值", "判定表", "场景法", "错误推测"},
    {"接口测试", "api测试", "postman", "pytest", "requests", "mock", "fixture", "参数化"},
    {"自动化测试", "selenium", "playwright", "cypress", "e2e", "回归测试", "冒烟测试"},
    {"性能测试", "压力测试", "负载测试", "稳定性测试", "tp95", "tp99", "吞吐量", "并发用户"},
    {"缺陷", "缺陷管理", "严重程度", "优先级", "缺陷生命周期", "日志分析", "异常场景"},
    {"llm 输出测试", "prompt 鲁棒性", "rag 相关性测试", "json 合法性", "fallback 测试", "多轮上下文测试"},
    {"项目经历", "项目", "系统", "平台", "模块", "秒杀", "ai模拟面试", "ai 模拟面试", "校园二手交易", "交易平台"},
    {"目标岗位", "岗位匹配", "后端开发", "ai应用开发", "ai 应用开发", "求职方向", "适合"},
    {"个人职责", "我负责", "我设计", "我实现", "我主导", "我的方案", "核心开发", "负责模块", "个人贡献"},
    {"技术难点", "难点", "挑战", "瓶颈", "问题", "故障", "异常", "一致性", "高并发"},
    {"解决方案", "解决思路", "方案", "设计", "架构", "优化", "原子扣减", "异步落库", "本地消息表", "补偿机制", "限流", "降级", "lua"},
    {"项目结果", "上线后", "测试结果", "压测", "qps", "rt", "tps", "提升", "降低", "控制在", "毫秒级", "稳定"},
]

INTRO_DEFAULT_POINTS = ["技术栈", "项目经历", "技术难点", "解决方案", "项目结果或岗位匹配"]
PROJECT_DEFAULT_POINTS = ["项目背景", "个人职责", "技术栈", "技术难点", "解决方案", "项目结果"]

PROJECT_POINT_ALIASES = {
    "项目背景": {"项目背景", "背景", "面向", "目标", "解决什么问题", "业务场景", "用户"},
    "个人职责": {"个人职责", "我负责", "负责", "我设计", "我实现", "我主导", "核心开发", "负责模块"},
    "项目结果": {"项目结果", "项目成果", "上线", "上线后", "完成", "提升", "降低", "稳定", "qps", "rt", "tps"},
    "项目结果或岗位匹配": {"项目结果", "项目成果", "岗位匹配", "目标岗位", "适合", "提升", "稳定", "qps", "rt", "tps"},
}


def normalize_text(text: str) -> str:
    return str(text or "").lower().replace("＋", "+").replace("＃", "#")


def contains_keyword(text: str, keyword: str) -> bool:
    normalized_text = normalize_text(text)
    normalized_keyword = normalize_text(keyword).strip()
    if not normalized_keyword:
        return False
    if re.search(r"[\u4e00-\u9fff]", normalized_keyword):
        return normalized_keyword.replace(" ", "") in normalized_text.replace(" ", "")
    if re.fullmatch(r"[a-z0-9+#.]+", normalized_keyword):
        return re.search(rf"(?<![a-z0-9+#.]){re.escape(normalized_keyword)}(?![a-z0-9+#.])", normalized_text) is not None
    return normalized_keyword.replace(" ", "") in normalized_text.replace(" ", "")


def extract_keywords(text: str) -> List[str]:
    found = []
    for kw in TECH_KEYWORDS:
        if contains_keyword(text, kw):
            found.append(kw)
    return sorted(set(found))


def split_reference_points(reference_answer: str, tags: List[str]) -> List[str]:
    """Extract lightweight reference points from reference answer and tags."""
    points = []

    for tag in tags or []:
        if tag and len(str(tag).strip()) >= 2:
            points.append(str(tag).strip())

    if reference_answer:
        parts = re.split(r"[，。；;、,.\s]+", reference_answer)
        for part in parts:
            part = part.strip()
            if len(part) >= 2 and len(part) <= 12:
                points.append(part)

    seen = set()
    result = []
    for p in points:
        key = normalize_text(p)
        if key not in seen:
            result.append(p)
            seen.add(key)
    return result[:12]


def tokenize_for_match(text: str) -> List[str]:
    normalized = normalize_text(text)
    english_tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]*", normalized)
    chinese_tokens = re.findall(r"[\u4e00-\u9fff]{2,}", normalized)
    known_terms = []
    for group in SEMANTIC_GROUPS:
        for term in group:
            term_norm = normalize_text(term)
            if term_norm and term_norm in normalized:
                known_terms.append(term_norm)
    return sorted(set(english_tokens + chinese_tokens + known_terms))


def expand_semantic_terms(text: str) -> set:
    normalized = normalize_text(text)
    expanded = set(tokenize_for_match(normalized))
    for group in SEMANTIC_GROUPS:
        normalized_group = {normalize_text(term) for term in group}
        if any(term and term in normalized for term in normalized_group):
            expanded.update(normalized_group)
    for label, aliases in PROJECT_POINT_ALIASES.items():
        normalized_aliases = {normalize_text(term) for term in aliases}
        if normalize_text(label) in normalized or any(term and term in normalized for term in normalized_aliases):
            expanded.update(normalized_aliases)
            expanded.add(normalize_text(label))
    return expanded


def point_is_covered(point: str, answer: str) -> bool:
    point_norm = normalize_text(point)
    answer_norm = normalize_text(answer)
    if not point_norm:
        return False
    if point_norm in answer_norm:
        return True

    point_terms = expand_semantic_terms(point_norm)
    answer_terms = expand_semantic_terms(answer_norm)
    if point_terms & answer_terms:
        return True

    point_tokens = [token for token in tokenize_for_match(point_norm) if len(token) >= 2]
    if not point_tokens:
        return False

    matched_count = sum(1 for token in point_tokens if token in answer_norm or token in answer_terms)
    return matched_count / max(1, len(point_tokens)) >= 0.5


def build_reference_points(question_meta: Dict[str, Any]) -> List[str]:
    question_type = question_meta.get("type") or question_meta.get("question_type")
    expected_points = question_meta.get("expected_points", [])
    if isinstance(expected_points, str):
        expected_points = [expected_points]
    if isinstance(expected_points, list):
        points = [str(point).strip() for point in expected_points if str(point).strip()]
        if points:
            return points[:12]

    if question_type == "intro":
        return INTRO_DEFAULT_POINTS
    if question_type in {"project", "project_followup"}:
        return PROJECT_DEFAULT_POINTS

    reference_answer = question_meta.get("reference_answer", "")
    tags = question_meta.get("tags", [])
    return split_reference_points(reference_answer, tags)


def calculate_coverage(answer: str, reference_points: List[str]) -> Dict[str, Any]:
    lower_answer = normalize_text(answer)
    covered = []
    missing = []

    for point in reference_points:
        if point_is_covered(point, lower_answer):
            covered.append(point)
        else:
            missing.append(point)

    if not reference_points:
        ratio = 0.0
    else:
        ratio = len(covered) / len(reference_points)

    return {
        "covered_points": covered,
        "missing_points": missing[:6],
        "coverage_ratio": round(ratio, 2)
    }


def _collect_optional_points(question_meta: Dict[str, Any], keys: List[str]) -> List[str]:
    values = []
    for key in keys:
        raw = question_meta.get(key, [])
        if isinstance(raw, str):
            raw = [raw]
        if isinstance(raw, list):
            values.extend(str(item).strip() for item in raw if str(item).strip())
    return list(dict.fromkeys(values))


def detect_misconceptions(question_meta: Dict[str, Any], answer: str) -> Dict[str, Any]:
    misconception_points = _collect_optional_points(
        question_meta,
        ["common_mistakes", "misconceptions", "negative_signals", "bad_answer_signals"],
    )
    critical_points = _collect_optional_points(question_meta, ["critical_errors"])
    matched_misconceptions = [
        item for item in misconception_points
        if len(item) >= 4 and point_is_covered(item, answer)
    ]
    matched_critical = [
        item for item in critical_points
        if len(item) >= 4 and point_is_covered(item, answer)
    ]
    return {
        "matched_misconceptions": matched_misconceptions[:5],
        "matched_critical_errors": matched_critical[:5],
        "misconception_count": len(matched_misconceptions),
        "critical_error_count": len(matched_critical),
    }


def repetition_ratio(answer: str) -> float:
    tokens = tokenize_for_match(answer)
    if len(tokens) < 12:
        return 0.0
    unique_count = len(set(tokens))
    return round(1 - unique_count / max(1, len(tokens)), 2)


def analyze_answer(question_meta: Dict[str, Any], user_answer: str) -> Dict[str, Any]:
    """Analyze one user answer with simple, explainable rules.

    The result supports continuous follow-up and the final scoring report.
    """
    answer = user_answer.strip()
    answer_len = len(answer)
    keywords = extract_keywords(answer)

    reference_points = build_reference_points(question_meta)
    coverage = calculate_coverage(answer, reference_points)
    misconception_result = detect_misconceptions(question_meta, answer)
    question_type = question_meta.get("type") or question_meta.get("question_type")
    if question_type in {"intro", "project", "project_followup"} and answer_len < 50:
        coverage["coverage_ratio"] = min(coverage["coverage_ratio"], 0.4)

    logic_count = sum(1 for marker in LOGIC_MARKERS if marker in answer)
    has_example = any(marker in answer for marker in ["例如", "比如", "项目中", "实际", "场景"])
    has_result = any(marker in answer for marker in ["结果", "提升", "降低", "完成", "实现", "优化"])

    repeat_ratio = repetition_ratio(answer)
    length_score = min(10, max(2, answer_len // 18))
    if answer_len > 900 and repeat_ratio > 0.45:
        length_score = min(length_score, 7)
    elif answer_len > 1400:
        length_score = min(length_score, 8)

    logic_score = min(9, 4 + min(logic_count, 3) * 1.2 + (1 if has_example else 0) + (1 if has_result else 0))
    if coverage["coverage_ratio"] < 0.35:
        logic_score = min(logic_score, 7)
    if answer_len < 80 and logic_count >= 3:
        logic_score = min(logic_score, 7)

    technical_score = min(10, 3 + min(len(keywords), 5) + int(coverage["coverage_ratio"] * 4))
    if misconception_result["matched_misconceptions"]:
        technical_score = max(2, technical_score - min(3, misconception_result["misconception_count"]))
    if misconception_result["matched_critical_errors"]:
        technical_score = max(1, technical_score - 4)

    if answer_len < 30:
        overall = min(5, (length_score + logic_score + technical_score) // 3)
    else:
        overall = round(length_score * 0.3 + logic_score * 0.3 + technical_score * 0.4, 1)

    problems = []
    suggestions = []

    if answer_len < 50:
        problems.append("回答偏短，信息量不足")
        suggestions.append("补充背景、具体做法和结果，避免只给概念定义")
    if logic_count == 0:
        problems.append("回答结构不够明显")
        suggestions.append("可以使用“背景—问题—方案—结果”的结构回答")
    if question_meta.get("type") == "rag_basic" and coverage["coverage_ratio"] < 0.35:
        problems.append("基础知识关键点覆盖不足")
        suggestions.append("围绕定义、原理、应用场景和优缺点补充回答")
    if question_meta.get("type") == "project" and not has_result:
        problems.append("项目回答缺少结果或效果描述")
        suggestions.append("补充项目成果、性能提升、用户价值或个人贡献")
    if misconception_result["matched_misconceptions"]:
        problems.append("回答中出现了常见误区或风险表述")
        suggestions.append("复盘该知识点的适用边界，避免把经验性结论说成绝对结论")
    if misconception_result["matched_critical_errors"]:
        problems.append("回答中出现了严重技术性错误")
        suggestions.append("优先纠正该技术判断，再补充正确原理和验证方式")
    if answer_len > 900 and repeat_ratio > 0.45:
        problems.append("回答存在明显重复，信息密度偏低")
        suggestions.append("减少重复表述，保留结论、依据、例子和边界条件")

    needs_followup = (
        answer_len < 70
        or coverage["coverage_ratio"] < 0.35
        or question_meta.get("type") in {"project", "rag_basic"}
    )

    return {
        "answer_length": answer_len,
        "detected_keywords": keywords,
        "covered_points": coverage["covered_points"],
        "missing_points": coverage["missing_points"],
        "coverage_ratio": coverage["coverage_ratio"],
        "length_score": length_score,
        "logic_score": logic_score,
        "technical_score": technical_score,
        "overall_temp_score": overall,
        "repetition_ratio": repeat_ratio,
        "matched_misconceptions": misconception_result["matched_misconceptions"],
        "matched_critical_errors": misconception_result["matched_critical_errors"],
        "problems": problems,
        "suggestions": suggestions,
        "needs_followup": needs_followup
    }


def summarize_interview_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not records:
        return {
            "total_answers": 0,
            "average_temp_score": 0,
            "frequent_keywords": [],
            "common_problems": []
        }

    scores = []
    keyword_counter = {}
    problem_counter = {}

    for record in records:
        analysis = record.get("analysis", {})
        score = analysis.get("overall_temp_score")
        if isinstance(score, (int, float)):
            scores.append(score)

        for kw in analysis.get("detected_keywords", []):
            keyword_counter[kw] = keyword_counter.get(kw, 0) + 1

        for problem in analysis.get("problems", []):
            problem_counter[problem] = problem_counter.get(problem, 0) + 1

    frequent_keywords = sorted(keyword_counter.items(), key=lambda x: x[1], reverse=True)[:8]
    common_problems = sorted(problem_counter.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_answers": len(records),
        "average_temp_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "frequent_keywords": frequent_keywords,
        "common_problems": common_problems
    }
