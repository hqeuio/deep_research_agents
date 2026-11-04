import os
from pathlib import Path
from dotenv import load_dotenv

def load_settings(env_path: Path | None = None) -> dict[str, str]:
    if env_path is None:
        env_path = Path(__file__).resolve().parent / '.env'
    # 将 .env 加载到进程环境，不覆盖已有环境变量
    load_dotenv(dotenv_path=env_path, override=False)
    required_keys = (
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_BASE_URL",
        "DEEPSEEK_MODEL"
    )

    settings = {}
    for key in required_keys:
        value = os.environ.get(key, "").strip()
        if not value:
            raise ValueError(f"{key} is missing or empty")
        settings[key] = value

    return {
        "base_url": settings["DEEPSEEK_BASE_URL"],
        "api_key": settings["DEEPSEEK_API_KEY"],
        "model": settings["DEEPSEEK_MODEL"]
    }