from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str = "IPAM Backend"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "IP Address Management System Backend API"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "mysql+pymysql://ipam_user:ipam_pass123@mysql:3306/ipam"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()