from typing import Any, Dict


FRONTEND_DISPLAY_OVERRIDES = {
    "backend_ext_003": {
        "display_id": "frontend_api_performance_001",
        "display_category": "前端开发 / 接口联调",
        "display_topic": "接口联调与性能分析",
    },
    "backend_ext_006": {
        "display_id": "frontend_idempotency_001",
        "display_category": "前端开发 / 接口联调",
        "display_topic": "前端重复提交与接口幂等",
    },
    "net_ext_019": {
        "display_id": "frontend_cors_001",
        "display_category": "前端开发 / 网络与跨域",
        "display_topic": "CORS 跨域与生产排查",
    },
    "swe_ext_007": {
        "display_id": "frontend_e2e_testing_001",
        "display_category": "前端开发 / 测试",
        "display_topic": "端到端与集成测试",
    },
    "proj_ext_014": {
        "display_id": "frontend_secret_management_001",
        "display_category": "前端开发 / 安全",
        "display_topic": "前端项目密钥与安全边界",
    },
    "swe_ext_012": {
        "display_id": "frontend_engineering_001",
        "display_category": "前端开发 / 工程化",
        "display_topic": "前端工程化与 CI/CD",
    },
}


FRONTEND_TERMS = (
    "前端",
    "frontend",
    "javascript",
    "typescript",
    "vue",
    "react",
    "html",
    "css",
    "cors",
    "跨域",
    "浏览器",
    "页面",
    "组件",
)


def _text_blob(meta: Dict[str, Any], target_role: str = "") -> str:
    tags = meta.get("tags", [])
    if isinstance(tags, list):
        tags_text = " ".join(str(tag) for tag in tags)
    else:
        tags_text = str(tags or "")
    return " ".join(
        str(value or "")
        for value in [
            target_role,
            meta.get("display_category", ""),
            meta.get("display_topic", ""),
            meta.get("category", ""),
            tags_text,
            meta.get("question", ""),
            meta.get("reason", ""),
        ]
    ).lower()


def should_use_frontend_display(meta: Dict[str, Any], target_role: str = "") -> bool:
    knowledge_id = str((meta or {}).get("knowledge_id") or (meta or {}).get("id") or "")
    if knowledge_id not in FRONTEND_DISPLAY_OVERRIDES:
        return False
    text = _text_blob(meta or {}, target_role)
    return any(term.lower() in text for term in FRONTEND_TERMS) or "前端" in str(target_role)


def get_rag_display_fields(meta: Dict[str, Any], target_role: str = "") -> Dict[str, str]:
    meta = meta or {}
    knowledge_id = str(meta.get("knowledge_id") or meta.get("id") or "")
    if should_use_frontend_display(meta, target_role):
        override = FRONTEND_DISPLAY_OVERRIDES[knowledge_id]
        return {
            "display_id": override["display_id"],
            "display_category": override["display_category"],
            "display_topic": override["display_topic"],
        }

    tags = meta.get("tags", [])
    topic = ""
    if isinstance(tags, list) and tags:
        topic = str(tags[0])
    return {
        "display_id": str(meta.get("display_id") or knowledge_id),
        "display_category": str(meta.get("display_category") or meta.get("category") or ""),
        "display_topic": str(meta.get("display_topic") or topic or meta.get("question_type") or ""),
    }


def attach_rag_display_fields(meta: Dict[str, Any], target_role: str = "") -> Dict[str, Any]:
    result = dict(meta or {})
    result.update(get_rag_display_fields(result, target_role))
    return result
