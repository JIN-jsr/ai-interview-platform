"""Final submission self-check script.

Run from project root:
    python scripts/self_check.py
"""

from __future__ import annotations

import importlib.util
import json
import py_compile
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "app.py",
    "requirements.txt",
    "README.md",
    ".gitignore",
    ".env.example",
    "start_app.bat",
    "data/knowledge_base.json",
    "docs/Project_Design_Document.md",
]

OPTIONAL_FILES = [
    "docs/final_submission_checklist.md",
    "docs/demo_script.md",
    "demo/README.md",
]

REQUIRED_FOLDERS = [
    "src",
    "data",
    "docs",
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
]

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
]

DANGEROUS_LOCAL_PATHS = [
    ".env",
    ".venv",
    "outputs/sessions",
    "outputs/reports",
]

IMPORT_CHECKS = {
    "streamlit": "streamlit",
    "python-dotenv": "dotenv",
    "requests": "requests",
    "pdfplumber": "pdfplumber",
    "python-docx": "docx",
    "Pillow": "PIL",
}


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


def check_required_files(reporter: Reporter) -> None:
    for rel in REQUIRED_FILES:
        if rel_exists(rel):
            reporter.ok_msg(f"必需文件存在：{rel}")
        else:
            reporter.error_msg(f"缺少必需文件：{rel}")

    for rel in OPTIONAL_FILES:
        if rel_exists(rel):
            reporter.ok_msg(f"可选文件存在：{rel}")
        else:
            reporter.warn_msg(f"可选文件缺失：{rel}")


def check_required_folders(reporter: Reporter) -> None:
    for rel in REQUIRED_FOLDERS:
        path = ROOT / rel
        if path.is_dir():
            reporter.ok_msg(f"必需目录存在：{rel}/")
        else:
            reporter.error_msg(f"缺少必需目录：{rel}/")


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
            reporter.error_msg(f"Python 语法或导入前检查失败：{rel}，{exc}")


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
    return False


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

    for rel in DANGEROUS_LOCAL_PATHS:
        path = ROOT / rel
        if not path.exists():
            reporter.ok_msg(f"本地未发现敏感/输出路径：{rel}")
            continue
        if pattern_is_covered(patterns, rel + "/" if path.is_dir() else rel):
            reporter.warn_msg(f"本地存在但已被忽略：{rel}。提交前不要手动 git add -f。")
        else:
            reporter.error_msg(f"本地存在且未被 .gitignore 覆盖：{rel}")

    env_example = read_text_safe(".env.example")
    if "your_api_key_here" in env_example and "sk-" not in env_example:
        reporter.ok_msg(".env.example 使用占位密钥，未发现明显真实 API Key。")
    else:
        reporter.warn_msg(".env.example 请确认只包含占位密钥。")


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
    check_python_compile(reporter)
    check_knowledge_base(reporter)
    check_demo_package(reporter)
    check_gitignore_and_security(reporter)
    check_imports(reporter)
    print_summary(reporter)
    return 0 if reporter.error == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
