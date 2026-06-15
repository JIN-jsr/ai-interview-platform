import os
from dotenv import load_dotenv

load_dotenv()


def get_llm_config():
    """Read LLM config from environment variables.

    Day 1 only prepares the structure. Actual API call will be implemented later.
    """
    return {
        "api_key": os.getenv("LLM_API_KEY", ""),
        "base_url": os.getenv("LLM_BASE_URL", ""),
        "model_name": os.getenv("MODEL_NAME", "")
    }


def call_llm(prompt: str) -> str:
    """Placeholder LLM call.

    Replace this function with a real API call in later development.
    """
    config = get_llm_config()
    if not config["api_key"]:
        return "LLM API Key is not configured yet. This is a Day 1 placeholder response."
    return "Real LLM call has not been implemented yet."
