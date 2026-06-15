import json
import os
import re
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()


def str_to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def get_llm_config() -> Dict[str, str]:
    """Read LLM config from environment variables."""
    return {
        "api_key": os.getenv("LLM_API_KEY", "").strip(),
        "base_url": os.getenv("LLM_BASE_URL", "").strip().rstrip("/"),
        "model_name": os.getenv("MODEL_NAME", "").strip(),
        "use_llm": os.getenv("USE_LLM", "false").strip()
    }


def is_llm_enabled() -> bool:
    config = get_llm_config()
    return (
        str_to_bool(config["use_llm"])
        and bool(config["api_key"])
        and bool(config["base_url"])
        and bool(config["model_name"])
    )


def call_chat(
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
    timeout: int = 60
) -> str:
    """Call an OpenAI-compatible chat completions API."""
    config = get_llm_config()
    if not is_llm_enabled():
        raise RuntimeError(
            "LLM is not enabled. Please set USE_LLM=true and configure LLM_API_KEY, "
            "LLM_BASE_URL and MODEL_NAME in your .env file."
        )

    url = f"{config['base_url']}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config["model_name"],
        "messages": messages,
        "temperature": temperature
    }

    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Parse JSON from model output and recover markdown-wrapped JSON if needed."""
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start:end + 1])
        raise
