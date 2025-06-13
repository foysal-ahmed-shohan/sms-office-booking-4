from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional
import os


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Twilio Configuration
    twilio_account_sid: str = Field(..., env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(..., env="TWILIO_AUTH_TOKEN")
    twilio_phone_number: str = Field(..., env="TWILIO_PHONE_NUMBER")
    
    # Feature Flags
    enable_sms_sending: bool = Field(default=False, env="ENABLE_SMS_SENDING")
    validate_twilio_signature: bool = Field(default=True, env="VALIDATE_TWILIO_SIGNATURE")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    
    # OfficeRND Configuration
    officernd_client_id: str = Field(..., env="OFFICERND_CLIENT_ID")
    officernd_client_secret: str = Field(..., env="OFFICERND_CLIENT_SECRET")
    officernd_base_url: str = Field(default="https://app.officernd.com/api/v2", env="OFFICERND_BASE_URL")
    officernd_identity_url: str = Field(default="https://identity.officernd.com", env="OFFICERND_IDENTITY_URL")
    officernd_org_slug: str = Field(..., env="OFFICERND_ORG_SLUG")
    officernd_scope: str = Field(..., env="OFFICERND_SCOPE")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # API Configuration
    api_title: str = "SMS Service API"
    api_version: str = "1.0.0"
    api_description: str = "A service that receives SMS via Twilio and sends automated replies"
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    db_echo: bool = Field(default=False, env="DB_ECHO")  # SQL query logging
    db_pool_size: int = Field(default=5, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, env="DB_MAX_OVERFLOW")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file_path: str = Field(default="logs/app.log", env="LOG_FILE_PATH")
    log_max_size: int = Field(default=10485760, env="LOG_MAX_SIZE")  # 10MB
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    @validator("twilio_phone_number")
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        if not v.startswith("+"):
            raise ValueError("Phone number must start with + and include country code")
        if len(v) < 10:
            raise ValueError("Phone number seems too short")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {', '.join(valid_levels)}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


def get_settings() -> Settings:
    """Get application settings"""
    return Settings()


# Create a singleton instance
settings = get_settings()