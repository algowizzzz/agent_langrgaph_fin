from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import List
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class UploadConfig(BaseModel):
    max_file_size_mb: int = 10
    allowed_extensions: List[str] = ['.doc', '.docx', '.xlsx', '.csv', '.pdf', '.txt']
    allowed_mime_types: List[str] = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword', 
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv'
    ]

class AIConfig(BaseModel):
    similarity_threshold: float = 0.8
    max_conversation_history: int = 10
    chunk_size: int = 1500
    chunk_overlap: int = 200
    timeout_seconds: int = 30
    max_retries: int = 3
    rate_limit_delay_seconds: int = 2
    # API Keys (loaded from environment)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    enable_mock_mode: bool = False

class SessionConfig(BaseModel):
    cleanup_on_chat_end: bool = True
    auto_cleanup_hours: int = 24

class ExportConfig(BaseModel):
    ai_generated_prefix: str = "AI generated content\n\n"

class APIConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["http://localhost:8501"]

class MockDataConfig(BaseModel):
    file_path: str = "mock_data.json"
    keyword_match_threshold: float = 0.5

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

from pydantic import Field

class Settings(BaseSettings):
    # Environment variables that will be loaded
    openai_api_key: str = ""
    # Use an alias to load CLAUDE_API_KEY from .env into this field
    anthropic_api_key: str = Field(alias='CLAUDE_API_KEY', default="")
    
    upload: UploadConfig = UploadConfig()
    ai: AIConfig = AIConfig()
    session: SessionConfig = SessionConfig()
    export: ExportConfig = ExportConfig()
    api: APIConfig = APIConfig()
    mock_data: MockDataConfig = MockDataConfig()
    logging: LoggingConfig = LoggingConfig()
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        # Allow population by alias
        populate_by_name = True

def load_config() -> Settings:
    """Load configuration from YAML file and environment variables."""
    # Start with defaults from environment variables
    settings = Settings()
    
    # Override with YAML config if exists
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Merge YAML data with environment settings
        for key, value in config_data.items():
            if hasattr(settings, key):
                if isinstance(getattr(settings, key), BaseModel):
                    # Update nested config objects
                    current_config = getattr(settings, key)
                    for sub_key, sub_value in value.items():
                        if hasattr(current_config, sub_key):
                            setattr(current_config, sub_key, sub_value)
                else:
                    setattr(settings, key, value)
    
    # Update AI config with API keys from environment
    settings.ai.openai_api_key = settings.openai_api_key
    settings.ai.anthropic_api_key = settings.anthropic_api_key
    
    return settings

# Global config instance
config = load_config()