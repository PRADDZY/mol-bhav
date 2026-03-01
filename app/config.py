from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM — NVIDIA NIM (OpenAI-compatible)
    nim_api_key: str = ""
    nim_base_url: str = "https://integrate.api.nvidia.com/v1"
    nim_model: str = "z-ai/glm4_7"

    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "mol_bhav"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Negotiation defaults
    default_beta: float = 5.0
    default_alpha: float = 0.6
    default_max_rounds: int = 15
    default_session_ttl_seconds: int = 300

    # Security
    min_response_delay_ms: int = 2000
    cors_allowed_origins: list[str] = ["http://localhost:3000"]
    api_admin_key: str = ""
    max_requests_per_minute_per_ip: int = 30
    max_request_body_bytes: int = 65_536

    # Environment
    env: str = "development"  # development | staging | production
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
