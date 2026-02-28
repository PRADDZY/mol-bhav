from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

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

    # Environment
    env: str = "development"  # development | staging | production

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
