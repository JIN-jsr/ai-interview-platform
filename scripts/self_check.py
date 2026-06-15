"""Simple project self-check script.

Run from project root:
    python scripts/self_check.py
"""

from pathlib import Path
import json
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "app.py",
    "requirements.txt",
    "README.md",
    ".env.example",
    "data/knowledge_base.json",
    "data/sample_resume.txt",
    "src/llm_client.py",
    "src/resume_parser.py",
    "src/resume_file_loader.py",
    "src/profile_generator.py",
    "src/rag_retriever.py",
    "src/interviewer.py",
    "src/answer_analyzer.py",
    "src/evaluator.py",
]

PYTHON_FILES = [
    "app.py",
    "src/llm_client.py",
    "src/resume_parser.py",
    "src/resume_file_loader.py",
    "src/profile_generator.py",
    "src/rag_retriever.py",
    "src/interviewer.py",
    "src/answer_analyzer.py",
    "src/evaluator.py",
]


def check_files():
    missing = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            missing.append(rel)
    return missing


def check_python_compile():
    errors = []
    for rel in PYTHON_FILES:
        try:
            py_compile.compile(str(ROOT / rel), doraise=True)
        except Exception as exc:
            errors.append((rel, str(exc)))
    return errors


def check_knowledge_base():
    kb_path = ROOT / "data" / "knowledge_base.json"
    data = json.loads(kb_path.read_text(encoding="utf-8"))
    categories = sorted(set(item.get("category", "") for item in data))
    invalid = []
    required = {"id", "category", "tags", "difficulty", "question", "answer", "follow_up", "source"}
    for item in data:
        missing = required - set(item.keys())
        if missing:
            invalid.append((item.get("id", "unknown"), sorted(missing)))
    return len(data), categories, invalid


def main():
    print("=== AI Interview Platform Self Check ===")

    missing = check_files()
    if missing:
        print("[FAIL] Missing files:")
        for m in missing:
            print(" -", m)
        sys.exit(1)
    print("[OK] Required files exist.")

    compile_errors = check_python_compile()
    if compile_errors:
        print("[FAIL] Python syntax errors:")
        for rel, err in compile_errors:
            print(f" - {rel}: {err}")
        sys.exit(1)
    print("[OK] Python files compile.")

    total, categories, invalid = check_knowledge_base()
    if invalid:
        print("[FAIL] Invalid knowledge entries:")
        for entry in invalid[:10]:
            print(" -", entry)
        sys.exit(1)

    print(f"[OK] Knowledge base entries: {total}")
    print("[OK] Categories:")
    for c in categories:
        print(" -", c)

    print("=== Self check passed ===")


if __name__ == "__main__":
    main()
