import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Keys
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OLLAMA_API_BASE: str = "http://localhost:11434"

    # Services
    SANDBOX_AGENT_URL: str = "http://sandbox:5001"
    
    # Defaults
    DEFAULT_PROVIDER: str = "mock"
    DEFAULT_MODEL: str = "mock-model"
    MAX_STEPS: int = 30
    DEFAULT_RISK_POLICY: str = "confirm_high"  # auto_confirm, confirm_high, confirm_medium_high

    # Network access policy
    NETWORK_POLICY_MODE: str = "blocklist"  # blocklist, allowlist

    # Vision / screen recognition
    VISION_GRID_OVERLAY: bool = True       # overlay coordinate grid for accurate clicks
    VISION_GRID_SPACING: int = 100         # grid spacing in screen coordinate pixels
    VISION_CHANGE_DETECTION: bool = True   # detect whether the last action changed the screen
    VISION_NO_EFFECT_THRESHOLD: float = 0.012  # below this change ratio an action counts as ineffective

    # App
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 3000

settings = Settings()
