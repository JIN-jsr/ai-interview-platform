import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
SESSION_DIR = ROOT / "outputs" / "sessions"
INDEX_PATH = SESSION_DIR / "session_index.json"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_session_dir() -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)


def make_json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): make_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [make_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [make_json_safe(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def generate_session_title(target_role: str = "", difficulty: str = "", created_at: Optional[str] = None) -> str:
    timestamp = created_at or now_text()
    try:
        display_time = datetime.strptime(timestamp[:19], "%Y-%m-%d %H:%M:%S").strftime("%m月%d日 %H:%M")
    except Exception:
        display_time = timestamp[:16]
    role = target_role or "模拟面试"
    level = difficulty or "中等"
    return f"{display_time}｜{role}｜{level}"


def session_path(session_id: str) -> Path:
    return SESSION_DIR / f"session_{session_id}.json"


def _read_index() -> List[Dict[str, Any]]:
    ensure_session_dir()
    if not INDEX_PATH.exists():
        return []
    try:
        data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict) and item.get("session_id")]


def _write_index(index: List[Dict[str, Any]]) -> None:
    ensure_session_dir()
    INDEX_PATH.write_text(json.dumps(make_json_safe(index), ensure_ascii=False, indent=2), encoding="utf-8")


def session_summary(session: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "session_id": session.get("session_id", ""),
        "title": session.get("title", ""),
        "updated_at": session.get("updated_at", ""),
        "target_role": session.get("target_role", ""),
        "difficulty": session.get("difficulty", ""),
        "status": session.get("status", "in_progress"),
    }


def update_session_index(session: Dict[str, Any]) -> None:
    index = _read_index()
    summary = session_summary(session)
    index = [item for item in index if item.get("session_id") != summary["session_id"]]
    index.insert(0, summary)
    index.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    _write_index(index)


def create_new_session(
    target_role: str = "",
    difficulty: str = "",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    ensure_session_dir()
    created_at = now_text()
    session = {
        "session_id": uuid.uuid4().hex,
        "title": title or generate_session_title(target_role, difficulty, created_at),
        "created_at": created_at,
        "updated_at": created_at,
        "target_role": target_role,
        "difficulty": difficulty,
        "resume_text": "",
        "uploaded_file_names": [],
        "extracted_file_text": "",
        "parsed_resume": None,
        "profile": None,
        "rag_items": [],
        "rag_index": 0,
        "messages": [],
        "question_meta": [],
        "current_question_meta": None,
        "interview_records": [],
        "show_immediate_answer_feedback": True,
        "use_llm_answer_feedback": True,
        "overall_answer_feedback": None,
        "overall_answer_feedback_key": "",
        "followup_count": 0,
        "used_knowledge_ids": [],
        "used_categories": [],
        "final_report": None,
        "report_markdown": "",
        "report_json": "",
        "interview_started": False,
        "status": "created",
    }
    save_session(session)
    return session


def save_session(session: Dict[str, Any]) -> Dict[str, Any]:
    ensure_session_dir()
    safe_session = make_json_safe(dict(session or {}))
    if not safe_session.get("session_id"):
        safe_session["session_id"] = uuid.uuid4().hex
    if not safe_session.get("created_at"):
        safe_session["created_at"] = now_text()
    safe_session["updated_at"] = now_text()
    if not safe_session.get("title"):
        safe_session["title"] = generate_session_title(
            safe_session.get("target_role", ""),
            safe_session.get("difficulty", ""),
            safe_session.get("created_at"),
        )
    session_path(safe_session["session_id"]).write_text(
        json.dumps(safe_session, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    update_session_index(safe_session)
    return safe_session


def load_session(session_id: str) -> Optional[Dict[str, Any]]:
    path = session_path(session_id)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return None
    return data


def list_sessions() -> Tuple[List[Dict[str, Any]], List[str]]:
    warnings: List[str] = []
    index = _read_index()
    valid: List[Dict[str, Any]] = []
    changed = False
    for item in index:
        session_id = item.get("session_id", "")
        try:
            session = load_session(session_id)
        except Exception as exc:
            warnings.append(f"{session_id}: {exc}")
            changed = True
            continue
        if not session:
            warnings.append(f"{session_id}: 文件不存在或格式无效")
            changed = True
            continue
        valid.append(session_summary(session))
    if changed:
        _write_index(valid)
    return valid, warnings


def delete_session(session_id: str) -> None:
    path = session_path(session_id)
    if path.exists():
        path.unlink()
    index = [item for item in _read_index() if item.get("session_id") != session_id]
    _write_index(index)


def rename_session(session_id: str, title: str) -> Optional[Dict[str, Any]]:
    session = load_session(session_id)
    if not session:
        return None
    session["title"] = str(title or "").strip() or session.get("title") or "未命名面试"
    return save_session(session)
