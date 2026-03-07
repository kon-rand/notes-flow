from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    OLLAMA_BASE_URL: str = "http://127.0.0.1:8080/v1"
    OLLAMA_MODEL: str = "unsloth/Qwen3.5-35B-A3B"
    DEFAULT_SUMMARIZE_DELAY: int = 300

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings: Settings = Settings()  # type: ignore[call-arg]