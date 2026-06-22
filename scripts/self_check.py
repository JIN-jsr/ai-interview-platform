"""Final submission self-check script.

Run from project root:
    python scripts/self_check.py
"""

from __future__ import annotations

import importlib.util
import json
import py_compile
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_FILES = [
    "app.py",
    "requirements.txt",
    "README.md",
    ".gitignore",
    ".env.example",
    "start_app.bat",
    "data/knowledge_base.json",
    "docs/Project_Design_Document.md",
    "docs/Project_Design_Document.pdf",
    "docs/assets/README.md",
    "docs/rag_coverage_audit.md",
]

OPTIONAL_FILES = [
    "docs/final_submission_checklist.md",
    "docs/demo_script.md",
    "docs/llm_config_guide.md",
    "docs/rag_build_guide.md",
    "docs/test_checklist.md",
    "demo/README.md",
]

REQUIRED_FOLDERS = [
    "src",
    "data",
    "docs",
    "docs/assets",
    "demo",
    "scripts",
]

PYTHON_FILES = [
    "app.py",
    "src/llm_client.py",
    "src/llm_interviewer.py",
    "src/llm_feedback_polisher.py",
    "src/resume_parser.py",
    "src/resume_file_loader.py",
    "src/profile_generator.py",
    "src/rag_retriever.py",
    "src/rag_display.py",
    "src/report_image_exporter.py",
    "src/interviewer.py",
    "src/answer_analyzer.py",
    "src/evaluator.py",
    "src/session_manager.py",
    "src/product_features.py",
]

EXPECTED_ASSETS = [
    "docs/assets/homepage.png",
    "docs/assets/resume_analysis_01_input.png",
    "docs/assets/resume_analysis_02_candidate_profile.png",
    "docs/assets/resume_analysis_03_role_match.png",
    "docs/assets/rag_evidence.png",
    "docs/assets/interview_workspace.png",
    "docs/assets/answer_analysis_export.png",
    "docs/assets/answer_analysis_summary.png",
    "docs/assets/final_report_dashboard.png",
    "docs/assets/ability_growth_curve.png",
    "docs/assets/report_full_long.png",
    "docs/assets/report_summary_poster.png",
    "docs/assets/system_architecture.png",
    "docs/assets/sidebar_navigation_01.png",
    "docs/assets/sidebar_navigation_02.png",
]

EXPECTED_WEIGHTS = {
    "基础知识掌握程度": 0.25,
    "项目理解深度": 0.25,
    "回答逻辑性": 0.20,
    "表达完整性": 0.15,
    "岗位匹配度": 0.15,
}

TARGET_ROLES = ["后端开发", "前端开发", "AI应用开发", "数据分析", "软件测试"]

DEMO_RESUMES = {
    "后端开发": "demo/sample_resume_backend.txt",
    "前端开发": "demo/sample_resume_frontend.txt",
    "AI应用开发": "demo/sample_resume_ai_app.txt",
    "数据分析": "demo/sample_resume_data_analysis.txt",
    "软件测试": "demo/sample_resume_testing.txt",
}

DEMO_ANSWER_FILES = [
    "demo/sample_answers_ai_app.md",
    "demo/sample_answers_backend.md",
    "demo/sample_answers_data_analysis.md",
    "demo/sample_answers_frontend.md",
    "demo/sample_answers_testing.md",
]

REQUIRED_GITIGNORE_PATTERNS = [
    ".env",
    ".venv/",
    "__pycache__/",
    "*.pyc",
    ".pytest_cache/",
    ".streamlit/secrets.toml",
    "outputs/sessions/",
    "outputs/reports/",
    "outputs/report_images/",
    "!docs/assets/",
    "!docs/assets/*.png",
]

OUTPUT_DIRS = [
    "outputs/sessions",
    "outputs/reports",
    "outputs/report_images",
]

IMPORT_CHECKS = {
    "streamlit": "streamlit",
    "python-dotenv": "dotenv",
    "requests": "requests",
    "pdfplumber": "pdfplumber",
    "python-docx": "docx",
    "Pillow": "PIL",
}

STALE_PATTERNS = [
    "demo/demo_answers.md",
    "data/sample_resume.txt",
    "sample_resume.txt",
    "docs/PROJECT_CONTEXT.md",
    "docs/OPTIMIZATION_PLAN.md",
    "PROJECT_CONTEXT",
    "OPTIMIZATION_PLAN",
    "80 条",
    "80 entries",
    "fallback debug",
    "raw metadata",
    "raw json",
    "sidebar_navigation.png",
    "workspace_navigation_composite.png",
    "resume_analysis_flow.png",
    "Project_Design_Document.docx",
    "DOCX 作为正式排版",
    "DOCX/PDF 元数据",
    ".venv\\S cripts",
    ".venv\\a ctivate",
    "Scripts\\a ctivate",
]

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"api[_-]?key\s*=\s*['\"][^'\"]{12,}['\"]", re.I),
]

TEXT_EXTENSIONS = {".md", ".py", ".bat", ".txt", ".json", ".toml", ".yml", ".yaml"}


class Reporter:
    def __init__(self) -> None:
        self.ok = 0
        self.warn = 0
        self.error = 0

    def _print(self, prefix: str, message: str) -> None:
        print(f"[{prefix}] {message}")

    def ok_msg(self, message: str) -> None:
        self.ok += 1
        self._print("OK", message)

    def warn_msg(self, message: str) -> None:
        self.warn += 1
        self._print("WARN", message)

    def error_msg(self, message: str) -> None:
        self.error += 1
        self._print("ERROR", message)


def rel_exists(rel_path: str) -> bool:
    return (ROOT / rel_path).exists()


def read_text_safe(rel_path: str) -> str:
    path = ROOT / rel_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def iter_project_text_files():
    skip_parts = {".git", ".venv", "__pycache__", ".pytest_cache", "outputs"}
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip_parts for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_EXTENSIONS:
            yield path


def run_git(args: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return None


def check_required_files(reporter: Reporter) -> None:
    for rel in REQUIRED_FILES:
        if rel_exists(rel):
            reporter.ok_msg(f"必需文件存在：{rel}")
        else:
            reporter.error_msg(f"缺少必需文件：{rel}")

    for rel in OPTIONAL_FILES:
        if rel_exists(rel):
            reporter.ok_msg(f"文档文件存在：{rel}")
        else:
            reporter.warn_msg(f"文档文件缺失：{rel}")


def check_required_folders(reporter: Reporter) -> None:
    for rel in REQUIRED_FOLDERS:
        path = ROOT / rel
        if path.is_dir():
            reporter.ok_msg(f"必需目录存在：{rel}/")
        else:
            reporter.error_msg(f"缺少必需目录：{rel}/")


def check_python_version(reporter: Reporter) -> None:
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        reporter.ok_msg(f"Python 版本可用：{version.major}.{version.minor}.{version.micro}")
    else:
        reporter.warn_msg(
            f"当前 Python 版本为 {version.major}.{version.minor}.{version.micro}，建议使用 Python 3.10+。"
        )


def check_python_compile(reporter: Reporter) -> None:
    cache_dir = Path(tempfile.gettempdir()) / "ai_interview_self_check_pycache"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        cache_dir = None
    for rel in PYTHON_FILES:
        path = ROOT / rel
        if not path.exists():
            reporter.warn_msg(f"跳过编译检查，文件不存在：{rel}")
            continue
        try:
            cfile = None
            if cache_dir:
                safe_name = rel.replace("\\", "_").replace("/", "_") + ".pyc"
                cfile = str(cache_dir / safe_name)
            py_compile.compile(str(path), cfile=cfile, doraise=True)
            reporter.ok_msg(f"Python 语法正常：{rel}")
        except PermissionError as exc:
            reporter.warn_msg(f"编译缓存写入受限，建议重启后再试：{rel}，{exc}")
        except Exception as exc:
            reporter.error_msg(f"Python 语法检查失败：{rel}，{exc}")


def normalize_kb_items(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "knowledge_base", "data"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def check_knowledge_base(reporter: Reporter) -> None:
    kb_path = ROOT / "data" / "knowledge_base.json"
    if not kb_path.exists():
        reporter.error_msg("知识库缺失：data/knowledge_base.json")
        return

    try:
        data = json.loads(kb_path.read_text(encoding="utf-8"))
    except Exception as exc:
        reporter.error_msg(f"知识库不是有效 JSON：{exc}")
        return

    items = normalize_kb_items(data)
    if not items:
        reporter.error_msg("知识库为空或结构不符合预期。")
        return

    reporter.ok_msg(f"知识库可读取，条目数：{len(items)}")
    required_fields = {"id", "category", "question", "answer", "expected_points"}
    invalid = []
    categories = set()
    for item in items:
        if isinstance(item, dict):
            categories.add(str(item.get("category", "")).strip())
            missing = required_fields - set(item.keys())
            if missing:
                invalid.append((item.get("id", "unknown"), sorted(missing)))
        else:
            invalid.append(("non-dict-item", ["item must be object"]))

    if invalid:
        reporter.error_msg(f"知识库存在字段不完整条目，示例：{invalid[:3]}")
    else:
        reporter.ok_msg("知识库核心字段完整：id/category/question/answer/expected_points")

    clean_categories = sorted(c for c in categories if c)
    if clean_categories:
        reporter.ok_msg("知识库分类：" + "、".join(clean_categories[:20]))
    else:
        reporter.warn_msg("知识库没有明显分类字段。")

    ids = [str(item.get("id", "")).strip() for item in items if isinstance(item, dict)]
    duplicate_ids = [item_id for item_id, count in __import__("collections").Counter(ids).items() if item_id and count > 1]
    if duplicate_ids:
        reporter.error_msg(f"知识库存在重复 ID：{duplicate_ids[:10]}")
    else:
        reporter.ok_msg("知识库 ID 未发现重复。")

    empty_expected = [item.get("id", "unknown") for item in items if not item.get("expected_points")]
    if empty_expected:
        reporter.warn_msg(f"存在 expected_points 为空的知识点：{empty_expected[:10]}")
    else:
        reporter.ok_msg("知识库 expected_points 均非空。")

    optional_list_fields = [
        "common_mistakes",
        "misconceptions",
        "critical_errors",
        "negative_signals",
        "evidence_requirements",
        "verification_questions",
    ]
    malformed_meta = []
    meta_count = 0
    project_like = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        blob = json.dumps(item, ensure_ascii=False)
        if "项目" in blob or item.get("question_type") == "project":
            project_like += 1
        if any(item.get(field) for field in optional_list_fields):
            meta_count += 1
        for field in optional_list_fields:
            if field in item and item.get(field) not in (None, "") and not isinstance(item.get(field), list):
                malformed_meta.append((item.get("id", "unknown"), field))
    if malformed_meta:
        reporter.error_msg(f"知识库可选误区/证据字段类型异常：{malformed_meta[:10]}")
    else:
        reporter.ok_msg(f"误区/关键错误等可选元数据类型正常，覆盖条目数：{meta_count}")
    if project_like:
        reporter.ok_msg(f"知识库包含项目深挖相关条目：{project_like}")
    else:
        reporter.warn_msg("知识库未发现项目深挖相关条目。")


def check_role_capability_dictionaries(reporter: Reporter) -> None:
    try:
        from src.product_features import ROLE_KEYWORDS
    except Exception as exc:
        reporter.error_msg(f"无法读取岗位能力词库：{exc}")
        return
    for role in TARGET_ROLES:
        values = ROLE_KEYWORDS.get(role, [])
        if not values:
            reporter.error_msg(f"岗位能力词库为空：{role}")
        elif role == "软件测试" and len(values) < 25:
            reporter.warn_msg(f"软件测试岗位词库偏少：{len(values)}")
        else:
            reporter.ok_msg(f"岗位能力词库可用：{role}，关键词 {len(values)} 个")


def check_scoring_weights(reporter: Reporter) -> None:
    try:
        from src.evaluator import VALID_CONFIDENCE_VALUES, WEIGHTS
    except Exception as exc:
        reporter.error_msg(f"无法导入评分模块：{exc}")
        return
    if WEIGHTS == EXPECTED_WEIGHTS:
        reporter.ok_msg("五维评分权重保持不变。")
    else:
        reporter.error_msg(f"五维评分权重被修改：{WEIGHTS}")
    total = round(sum(WEIGHTS.values()), 6)
    if total == 1:
        reporter.ok_msg("五维评分权重总和为 1。")
    else:
        reporter.error_msg(f"五维评分权重总和异常：{total}")
    if {"high", "medium", "low"}.issubset(set(VALID_CONFIDENCE_VALUES)):
        reporter.ok_msg("评分置信度枚举值可用：high/medium/low。")
    else:
        reporter.warn_msg("评分置信度枚举值不完整。")


def check_answer_analysis_contract(reporter: Reporter) -> None:
    try:
        from src.answer_analyzer import analyze_answer, summarize_interview_records
    except Exception as exc:
        reporter.error_msg(f"无法导入回答分析模块：{exc}")
        return

    meta = {
        "question": "如何用 EXPLAIN 分析 MySQL 慢查询？",
        "type": "rag_basic",
        "expected_points": ["慢查询日志与 SQL 定位", "EXPLAIN 关键字段", "索引和扫描行数判断", "优化后验证"],
        "misconceptions": ["只要使用索引，查询就一定快"],
    }
    answer = "我会先看慢查询日志定位 SQL，再用 EXPLAIN 看 type、key、rows 和 Extra，判断索引和扫描行数，优化后对比耗时。"
    try:
        analysis = analyze_answer(meta, answer)
        json.dumps(analysis, ensure_ascii=False)
    except Exception as exc:
        reporter.error_msg(f"回答分析结果不可 JSON 序列化：{exc}")
        return

    required_keys = {"covered_points", "missing_points", "coverage_ratio", "problems", "suggestions", "needs_followup"}
    missing = sorted(required_keys - set(analysis.keys()))
    if missing:
        reporter.error_msg(f"回答分析缺少关键字段：{missing}")
    else:
        reporter.ok_msg("回答分析字段结构可用于即时反馈和最终报告。")

    old_record_summary = summarize_interview_records([{"question": "旧记录", "user_answer": "旧回答"}])
    if old_record_summary.get("total_answers") == 1:
        reporter.ok_msg("旧历史记录缺少 analysis 字段时可安全汇总。")
    else:
        reporter.error_msg("旧历史记录缺少 analysis 字段时汇总异常。")


def check_demo_package(reporter: Reporter) -> None:
    demo_dir = ROOT / "demo"
    if not demo_dir.is_dir():
        reporter.error_msg("缺少 demo/ 目录。")
        return

    for role, rel in DEMO_RESUMES.items():
        path = ROOT / rel
        if not path.exists():
            reporter.warn_msg(f"缺少 {role} 示例简历：{rel}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        normalized_text = "".join(text.split())
        normalized_role = "".join(role.split())
        if normalized_role.replace("开发", "") in normalized_text or normalized_role in normalized_text:
            reporter.ok_msg(f"{role} 示例简历存在并包含岗位信息：{rel}")
        else:
            reporter.warn_msg(f"{role} 示例简历存在，但岗位信息不明显：{rel}")
        if any(real_marker in text for real_marker in ("身份证", "手机号", "真实姓名", "家庭住址")):
            reporter.warn_msg(f"{rel} 可能包含真实个人信息，请人工确认。")

    for rel in DEMO_ANSWER_FILES:
        if rel_exists(rel):
            reporter.ok_msg(f"演示回答材料存在：{rel}")
        else:
            reporter.warn_msg(f"演示回答材料缺失：{rel}")


def check_assets(reporter: Reporter) -> None:
    try:
        from PIL import Image
    except Exception as exc:
        reporter.warn_msg(f"无法导入 Pillow，跳过图片尺寸校验：{exc}")
        return

    for rel in EXPECTED_ASSETS:
        path = ROOT / rel
        if not path.exists():
            reporter.error_msg(f"缺少文档图片：{rel}")
            continue
        try:
            with Image.open(path) as img:
                width, height = img.size
                img.verify()
            if width < 500 or height < 300:
                reporter.warn_msg(f"图片尺寸偏小：{rel}，{width} x {height}")
            else:
                reporter.ok_msg(f"图片可读取：{rel}，{width} x {height}")
        except Exception as exc:
            reporter.error_msg(f"图片无法读取：{rel}，{exc}")

    reference_sources = ["README.md", "docs/Project_Design_Document.md", "docs/assets/README.md"]
    required_doc_assets = {
        "docs/assets/answer_analysis_export.png": "答后即时分析合并截图",
        "docs/assets/answer_analysis_summary.png": "总体回答分析截图",
        "docs/assets/final_report_dashboard.png": "最终五维评分报告截图",
    }
    for asset, label in required_doc_assets.items():
        ignored = is_ignored(asset)
        if ignored is True:
            reporter.error_msg(f"{label} 被 .gitignore 忽略：{asset}")
        elif ignored is False:
            reporter.ok_msg(f"{label} 可被 Git 跟踪：{asset}")
        else:
            reporter.warn_msg(f"无法确认 {label} Git 状态：{asset}")

        filename = Path(asset).name
        referenced_by = [rel for rel in reference_sources if filename in read_text_safe(rel)]
        if referenced_by:
            reporter.ok_msg(f"{label} 已被文档引用：" + "、".join(referenced_by))
        else:
            reporter.error_msg(f"{label} 未被 README 或设计文档引用：{filename}")


def check_final_pdf(reporter: Reporter) -> None:
    pdf_path = ROOT / "docs" / "Project_Design_Document.pdf"
    if not pdf_path.exists():
        reporter.error_msg("缺少正式 PDF：docs/Project_Design_Document.pdf")
        return

    try:
        header = pdf_path.read_bytes()[:4]
    except Exception as exc:
        reporter.error_msg(f"正式 PDF 无法读取：{exc}")
        return

    if header == b"%PDF":
        reporter.ok_msg("正式 PDF 文件头有效：docs/Project_Design_Document.pdf")
    else:
        reporter.error_msg("正式 PDF 文件头不是 %PDF，请重新从桌面最终版复制。")
        return

    size = pdf_path.stat().st_size
    if size > 100_000:
        reporter.ok_msg(f"正式 PDF 文件大小正常：{size} bytes")
    else:
        reporter.warn_msg(f"正式 PDF 文件偏小，请人工确认：{size} bytes")

    try:
        import pdfplumber
    except Exception as exc:
        reporter.warn_msg(f"无法导入 pdfplumber，跳过页数校验：{exc}")
        return

    try:
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
            if page_count == 12:
                reporter.ok_msg("正式 PDF 页数符合最终版：12 页。")
            else:
                reporter.warn_msg(f"正式 PDF 页数为 {page_count} 页，请确认是否为最终版。")
            if pdf.pages:
                width = round(float(pdf.pages[0].width), 1)
                height = round(float(pdf.pages[0].height), 1)
                if 590 <= width <= 600 and 835 <= height <= 850:
                    reporter.ok_msg(f"正式 PDF 页面尺寸接近 A4：{width} x {height}")
                else:
                    reporter.warn_msg(f"正式 PDF 首页尺寸不是常见 A4：{width} x {height}")
    except Exception as exc:
        reporter.error_msg(f"正式 PDF 无法由 pdfplumber 打开：{exc}")


def parse_gitignore_patterns() -> set[str]:
    text = read_text_safe(".gitignore")
    patterns = set()
    for line in text.splitlines():
        clean = line.strip()
        if clean and not clean.startswith("#"):
            patterns.add(clean)
    return patterns


def pattern_is_covered(patterns: set[str], required: str) -> bool:
    if required in patterns:
        return True
    if required.endswith("/") and required.rstrip("/") in patterns:
        return True
    if required == "outputs/sessions/" and "outputs/sessions/*" in patterns:
        return True
    if required == "outputs/reports/" and "outputs/reports/*" in patterns:
        return True
    if required == "outputs/report_images/" and "outputs/report_images/*" in patterns:
        return True
    return False


def is_ignored(rel: str) -> bool | None:
    result = run_git(["check-ignore", rel])
    if result is None:
        return None
    return result.returncode == 0


def check_gitignore_and_security(reporter: Reporter) -> None:
    patterns = parse_gitignore_patterns()
    if not patterns:
        reporter.error_msg(".gitignore 缺失或为空。")
        return

    for required in REQUIRED_GITIGNORE_PATTERNS:
        if pattern_is_covered(patterns, required):
            reporter.ok_msg(f".gitignore 已覆盖：{required}")
        else:
            reporter.warn_msg(f".gitignore 建议补充：{required}")

    for rel in [".env", ".venv", *OUTPUT_DIRS]:
        path = ROOT / rel
        if not path.exists():
            reporter.ok_msg(f"本地未发现敏感/输出路径：{rel}")
            continue
        ignored = is_ignored(rel)
        if ignored is True or pattern_is_covered(patterns, rel + "/" if path.is_dir() else rel):
            reporter.warn_msg(f"本地存在但已被忽略：{rel}。提交前不要手动 git add -f。")
        elif ignored is None:
            reporter.warn_msg(f"无法调用 git check-ignore，请人工确认不会提交：{rel}")
        else:
            reporter.error_msg(f"本地存在且未被 .gitignore 覆盖：{rel}")

    for rel in EXPECTED_ASSETS[:2]:
        ignored = is_ignored(rel)
        if ignored is True:
            reporter.error_msg(f"文档图片仍被 .gitignore 忽略：{rel}")
        elif ignored is False:
            reporter.ok_msg(f"文档图片可被 Git 跟踪：{rel}")
        else:
            reporter.warn_msg(f"无法确认文档图片 Git 状态：{rel}")

    env_example = read_text_safe(".env.example")
    if "your_api_key_here" in env_example and "sk-" not in env_example:
        reporter.ok_msg(".env.example 使用占位密钥，未发现明显真实 API Key。")
    else:
        reporter.warn_msg(".env.example 请确认只包含占位密钥。")


def check_output_dirs(reporter: Reporter) -> None:
    for rel in OUTPUT_DIRS:
        path = ROOT / rel
        if not path.exists():
            reporter.ok_msg(f"输出目录不存在，提交安全：{rel}")
            continue
        visible_files = [
            item.relative_to(ROOT).as_posix()
            for item in path.rglob("*")
            if item.is_file() and item.name != ".gitkeep"
        ]
        if visible_files:
            reporter.warn_msg(f"{rel} 中存在运行生成文件，提交前确认未 git add：{visible_files[:5]}")
        else:
            reporter.ok_msg(f"{rel} 仅包含空目录占位或为空。")


def check_git_tracked_outputs(reporter: Reporter) -> None:
    result = run_git(["ls-files", "outputs"])
    if result is None:
        reporter.warn_msg("未找到 git，跳过输出文件跟踪检查。")
        return
    tracked = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    unsafe = [
        rel for rel in tracked if rel not in {"outputs/logs/.gitkeep", "outputs/reports/.gitkeep", "outputs/report_images/.gitkeep"}
    ]
    if unsafe:
        reporter.error_msg(f"outputs 中存在已跟踪的运行产物，请从 Git 中移除：{unsafe[:10]}")
    else:
        reporter.ok_msg("outputs 中未发现已跟踪的运行产物。")


def parse_requirements() -> set[str]:
    req_text = read_text_safe("requirements.txt")
    packages = set()
    for line in req_text.splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#"):
            continue
        for splitter in (">=", "==", "<=", "~=", ">", "<"):
            if splitter in clean:
                clean = clean.split(splitter, 1)[0]
                break
        packages.add(clean.strip())
    return packages


def check_imports(reporter: Reporter) -> None:
    requirements = parse_requirements()
    for req_name, module_name in IMPORT_CHECKS.items():
        if req_name not in requirements:
            continue
        if importlib.util.find_spec(module_name):
            reporter.ok_msg(f"依赖可导入：{module_name}")
        else:
            reporter.warn_msg(f"缺少依赖：{module_name}。请运行 pip install -r requirements.txt")


def check_markdown_links(reporter: Reporter) -> None:
    link_re = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    failures = []
    for path in [p for p in iter_project_text_files() if p.suffix.lower() == ".md"]:
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in link_re.finditer(text):
            target = match.group(1).strip().strip("<>")
            target = target.split("#", 1)[0].strip()
            if not target or target.startswith(("#", "http://", "https://", "mailto:", "app://")):
                continue
            if target.startswith("data:"):
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                failures.append((path.relative_to(ROOT).as_posix(), target, "指向项目外部"))
                continue
            if not resolved.exists():
                failures.append((path.relative_to(ROOT).as_posix(), target, "文件不存在"))

    if failures:
        for source, target, reason in failures[:10]:
            reporter.error_msg(f"Markdown 链接失效：{source} -> {target}（{reason}）")
    else:
        reporter.ok_msg("Markdown 相对链接和图片引用未发现失效项。")


def check_stale_references(reporter: Reporter) -> None:
    hits = []
    negative_markers = ("不存在", "旧", "失效引用", "未引用", "remove", "obsolete")
    for path in iter_project_text_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel == "scripts/self_check.py":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in STALE_PATTERNS:
            for line in text.splitlines():
                if pattern not in line:
                    continue
                if pattern == "answer_analysis.png" and any(marker in line for marker in negative_markers):
                    continue
                hits.append((rel, pattern))
                break
    if hits:
        for rel, pattern in hits[:10]:
            reporter.warn_msg(f"发现可能过期引用：{rel} -> {pattern}")
    else:
        reporter.ok_msg("未发现已删除文件或旧版本说明的明显引用。")


def check_documentation_consistency(reporter: Reporter) -> None:
    docs = {
        "README.md": read_text_safe("README.md"),
        "docs/Project_Design_Document.md": read_text_safe("docs/Project_Design_Document.md"),
        "docs/demo_script.md": read_text_safe("docs/demo_script.md"),
        "docs/test_checklist.md": read_text_safe("docs/test_checklist.md"),
        "docs/final_submission_checklist.md": read_text_safe("docs/final_submission_checklist.md"),
    }
    combined = "\n".join(docs.values())

    required_phrases = [
        "单题训练反馈",
        "完整面试结束后",
        "只优化反馈文字表达",
        "不修改覆盖率",
        "不包含完整参考答案",
        "answer_analysis_export.png",
    ]
    for phrase in required_phrases:
        if phrase in combined:
            reporter.ok_msg(f"文档边界说明存在：{phrase}")
        else:
            reporter.warn_msg(f"文档建议补充边界说明：{phrase}")

    forbidden_claims = [
        "LLM 直接评分",
        "LLM 计算分数",
        "导出完整参考答案",
        "逐题得分",
        "本题得分",
    ]
    hits = [claim for claim in forbidden_claims if claim in combined]
    if hits:
        reporter.warn_msg("文档中存在可能误导的表述，请人工确认：" + "、".join(hits))
    else:
        reporter.ok_msg("文档未发现 LLM 改分或导出完整参考答案的误导表述。")


    boundary_pairs = [
        ("单题即时分析", "当前回答"),
        ("总体回答分析", "跨题"),
        ("最终五维报告", "综合能力评价"),
    ]
    for left, right in boundary_pairs:
        if left in combined and right in combined:
            reporter.ok_msg(f"三层反馈边界表述存在：{left} / {right}")
        else:
            reporter.warn_msg(f"三层反馈边界建议补充：{left} / {right}")

    if "总体回答分析" in combined and "不直接修改最终五维评分" in combined:
        reporter.ok_msg("总体回答分析已说明不直接修改最终五维评分。")
    else:
        reporter.warn_msg("建议明确总体回答分析不直接修改最终五维评分。")
    active_old_image = re.search(r"!\[[^\]]*\]\([^)]*answer_analysis\.png\)", combined)
    if active_old_image:
        reporter.error_msg("文档仍存在旧截图 answer_analysis.png 的活跃图片引用。")
    else:
        reporter.ok_msg("文档未发现旧截图 answer_analysis.png 的活跃图片引用。")


def check_secret_like_text(reporter: Reporter) -> None:
    hits = []
    for path in iter_project_text_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel == ".env.example":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                hits.append(rel)
                break
    if hits:
        reporter.error_msg(f"发现疑似密钥文本，请人工清理：{hits[:10]}")
    else:
        reporter.ok_msg("未在可提交文本中发现明显 API Key 形态。")


def print_summary(reporter: Reporter) -> None:
    print("============================================")
    print("自检完成")
    print(f"OK: {reporter.ok}")
    print(f"WARN: {reporter.warn}")
    print(f"ERROR: {reporter.error}")
    print("============================================")
    if reporter.error == 0:
        print("项目基础结构正常，可以继续录制演示视频或提交 GitHub。")
    else:
        print("存在需要修复的问题，请根据上方提示处理。")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    reporter = Reporter()
    print("=== AI 模拟面试平台提交前自检 ===")
    print(f"项目根目录：{ROOT}")

    check_required_files(reporter)
    check_required_folders(reporter)
    check_python_version(reporter)
    check_python_compile(reporter)
    check_knowledge_base(reporter)
    check_role_capability_dictionaries(reporter)
    check_scoring_weights(reporter)
    check_answer_analysis_contract(reporter)
    check_demo_package(reporter)
    check_assets(reporter)
    check_final_pdf(reporter)
    check_gitignore_and_security(reporter)
    check_output_dirs(reporter)
    check_git_tracked_outputs(reporter)
    check_imports(reporter)
    check_markdown_links(reporter)
    check_stale_references(reporter)
    check_documentation_consistency(reporter)
    check_secret_like_text(reporter)
    print_summary(reporter)
    return 0 if reporter.error == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
