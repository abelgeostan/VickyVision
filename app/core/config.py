import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "VICKY OS"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8090

    # Database configuration
    DATABASE_URL: str = "postgresql://vicky:vickypass@localhost:5432/vicky_os"
    DB_ECHO: bool = False

    # Ollama / LLM configuration
    OLLAMA_BASE_URL: str = "http://192.168.1.20:11434"
    OLLAMA_TIMEOUT_SECONDS: float = 60.0
    DEFAULT_MODEL: str = "gemma3:4b"
    TECHY_MODEL: str = "gemma3:4b"
    ELDER_MODEL: str = "gemma3:4b"
    ARCHY_MODEL: str = "gemma3:4b"
    PA_MODEL: str = "gemma3:4b"

    # Techy Execution Runtime configuration
    TECHY_EXEC_PROVIDER: str = "ssh"  # "ssh" or "local"
    TECHY_SSH_HOST: str = "192.168.1.123"
    TECHY_SSH_PORT: int = 22
    TECHY_SSH_USER: str = "vickyops"
    TECHY_SSH_PASSWORD: Optional[str] = "vickythegoat"
    TECHY_SSH_KEY_PATH: Optional[str] = None
    TECHY_SUDO_PASSWORD: Optional[str] = "vickythegoat"
    TECHY_MAX_STEPS: int = 15
    TECHY_LOOP_TIMEOUT_SECONDS: float = 180.0
    TECHY_EXEC_TIMEOUT_SECONDS: float = 60.0

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
