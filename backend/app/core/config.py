from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Guardrails"
    API_V1_STR: str = "/api/v1"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_PROVIDER: str = "gemini" # Options: "gemini", "openai"
    # Add other config as needed
    
    class Config:
        env_file = ".env"

settings = Settings()
