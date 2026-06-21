"""Offline scoring calibration checks.

This script is deterministic and does not call an external LLM.

Run from project root:
    python scripts/scoring_calibration_check.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["USE_LLM"] = "false"

from src.answer_analyzer import analyze_answer, extract_keywords  # noqa: E402
from src.evaluator import build_final_report  # noqa: E402


QUESTION_SET = [
    {
        "question": "请介绍你的项目背景、个人职责、技术难点和验证结果。",
        "type": "project",
        "expected_points": ["项目背景", "个人职责", "技术难点", "解决方案", "项目结果"],
    },
    {
        "question": "如何用 EXPLAIN 分析 MySQL 慢查询？",
        "type": "rag_basic",
        "knowledge_id": "calibration_mysql_explain",
        "category": "MySQL",
        "tags": ["MySQL", "EXPLAIN", "索引优化"],
        "expected_points": ["慢查询日志与 SQL 定位", "EXPLAIN 关键字段", "索引和扫描行数判断", "优化后验证"],
        "misconceptions": ["只要使用索引，查询就一定快", "EXPLAIN 的 rows 就是真实扫描行数"],
        "critical_errors": ["执行计划完全等同于真实运行结果"],
    },
    {
        "question": "你会如何设计接口测试和回归测试？",
        "type": "rag_basic",
        "knowledge_id": "calibration_testing",
        "category": "软件测试",
        "tags": ["pytest", "接口测试", "回归测试", "日志分析"],
        "expected_points": ["测试数据准备", "fixture 前置和清理", "响应断言", "回归范围和日志分析"],
    },
    {
        "question": "请继续追问项目中的异常场景和测试方法。",
        "type": "project_followup",
        "expected_points": ["异常场景", "测试方法", "日志分析", "回归验证"],
    },
]


ANSWERS = {
    "low": [
        "做过一个项目，用了数据库，主要就是实现功能。",
        "只要用了索引查询就一定快，EXPLAIN 的 rows 就是真实扫描行数，所以看一下 key 就够了。",
        "接口测试就是请求一下接口，看状态码是 200 就行。",
        "异常场景没怎么测，功能能跑就可以。",
    ],
    "medium": [
        "项目是一个面试训练系统，我负责部分接口和报告页面，实现了简历解析、题目展示和报告导出。难点是 LLM 超时和 JSON 格式不稳定，最后加了 fallback 和错误提示。",
        "我会先看慢查询日志定位 SQL，再用 EXPLAIN 看 type、key、rows、Extra 等字段，判断是否走索引和是否有 filesort。优化后还要对比执行时间。",
        "接口测试会准备测试数据，用 pytest 调接口，断言状态码和核心字段；缺陷修复后会做回归测试，也会看日志确认异常消失。",
        "异常场景会测空输入、超时、格式错误和接口失败，并用日志定位问题，再补充回归用例。",
    ],
    "high": [
        "项目背景是帮助计算机学生按简历进行模拟面试。我负责面试流程、RAG 证据展示、评分报告和导出模块。技术难点包括 LLM 超时、结构化 JSON 失败、知识点重复和报告截图排版。我用本地规则 fallback 保证闭环，用 used_knowledge_ids 避免重复，用自检脚本验证知识库、图片和文档。结果是无 API Key 时仍能完成面试和报告，导出 JSON、Markdown 和 PNG 可复现。",
        "我会先从慢查询日志确认具体 SQL、参数和频率，再用 EXPLAIN 看 type、possible_keys、key、rows、filtered、Extra，判断是否全表扫描、回表、filesort 或索引选择性差。rows 是估算值，不等于真实扫描行数，所以还要结合实际耗时、数据分布和优化前后压测验证。优化手段包括联合索引顺序、覆盖索引、改写 where/order by、避免隐式转换。",
        "接口测试会先定义正常、异常、权限和边界场景，用 pytest + fixture 准备隔离数据并清理，必要时 Mock 外部依赖。断言不仅看状态码，还看响应 schema、业务字段、错误码和数据库副作用。缺陷修复后先复现原缺陷，再按影响范围做回归，并结合日志确认异常链路不再出现。",
        "异常场景包括 LLM 超时、返回非法 JSON、RAG 召回为空、网络失败和用户回答过短。我会准备测试数据，检查 fallback 是否触发、日志是否记录、报告置信度是否降低，并把相关用例接入 CI/CD 回归。",
    ],
}


def build_records(answer_level: str):
    records = []
    for meta, answer in zip(QUESTION_SET, ANSWERS[answer_level]):
        analysis = analyze_answer(meta, answer)
        records.append({
            "question": meta["question"],
            "question_type": meta["type"],
            "knowledge_id": meta.get("knowledge_id", ""),
            "display_topic": (meta.get("tags") or [meta["type"]])[0],
            "display_category": meta.get("category", ""),
            "expected_points": meta.get("expected_points", []),
            "user_answer": answer,
            "analysis": analysis,
        })
    return records


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    profile = {
        "target_role": "软件测试",
        "difficulty": "中等",
        "detected_skills": ["pytest", "接口测试", "回归测试", "日志分析", "RAG", "fallback"],
        "project_names": ["AI 模拟面试平台"],
    }
    reports = {}
    for level in ["low", "medium", "high"]:
        reports[level] = build_final_report(build_records(level), profile)

    low = reports["low"]["total_score"]
    medium = reports["medium"]["total_score"]
    high = reports["high"]["total_score"]
    assert_true(high > medium > low, f"score order failed: low={low}, medium={medium}, high={high}")
    assert_true(high - low >= 12, f"score separation too small: low={low}, high={high}")
    assert_true(high < 100, f"high-quality answer should not automatically be 100: {high}")

    heading_answer = "首先。其次。最后。总结。"
    heading_analysis = analyze_answer(QUESTION_SET[1], heading_answer)
    assert_true(heading_analysis["logic_score"] < 10, "headings-only answer created logic 100")

    repeated = "首先 MySQL 索引很重要。" * 120
    repeated_analysis = analyze_answer(QUESTION_SET[1], repeated)
    assert_true(repeated_analysis["length_score"] <= 8, "repetitive long answer gained unlimited completeness")

    misconception_analysis = analyze_answer(QUESTION_SET[1], ANSWERS["low"][1])
    assert_true(misconception_analysis["matched_misconceptions"], "explicit misconception was not detected")
    assert_true(misconception_analysis["technical_score"] <= 7, "misconception did not reduce technical score")

    no_project_report = build_final_report(build_records("medium")[1:3], profile)
    assert_true(no_project_report["project_evidence_sufficient"] is False, "missing project evidence flag not set")
    assert_true(no_project_report["project_evidence_confidence"] == "low", "missing project confidence should be low")

    testing_keywords = extract_keywords("我会用 pytest 做接口测试，准备异常场景，结合日志分析并做回归测试。")
    assert_true("pytest" in testing_keywords and "接口测试" in testing_keywords and "回归测试" in testing_keywords, "software testing vocabulary not recognized")

    weak_analysis = analyze_answer(QUESTION_SET[1], "不知道。")
    medium_analysis = analyze_answer(QUESTION_SET[1], ANSWERS["medium"][1])
    strong_analysis = analyze_answer(QUESTION_SET[1], ANSWERS["high"][1])
    assert_true(
        strong_analysis["coverage_ratio"] >= medium_analysis["coverage_ratio"] >= weak_analysis["coverage_ratio"],
        "coverage should improve from weak to medium to strong answers",
    )
    assert_true(weak_analysis["suggestions"], "weak answer should receive actionable suggestions")
    assert_true(strong_analysis["missing_points"] != QUESTION_SET[1]["expected_points"], "strong answer should not miss every expected point")
    empty_analysis = analyze_answer(QUESTION_SET[1], "")
    assert_true(empty_analysis["answer_length"] == 0 and empty_analysis["coverage_ratio"] == 0, "empty answer analysis should be conservative")
    assert_true("reference_answer" not in strong_analysis, "analysis result should not expose a full reference answer")

    print("Calibration scores:")
    print(f"  low={low}")
    print(f"  medium={medium}")
    print(f"  high={high}")
    print("All scoring calibration checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
