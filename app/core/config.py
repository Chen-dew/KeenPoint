"""
应用配置模块
管理所有环境变量和应用配置
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "Academic Paper Assistant"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API 配置
    API_PREFIX: str = "/api/v1"
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list = ["pdf", "doc", "docx"]
    
    # 文件存储配置
    STATIC_DIR: str = "static"
    OUTPUT_DIR: str = "outputs"
    TEMP_DIR: str = "temp"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # 数据库配置 (可选，用于未来扩展)
    DATABASE_URL: Optional[str] = None
    
    # Redis 配置 (可选，用于缓存)
    REDIS_URL: Optional[str] = None
    
    # NLP 配置
    NLP_MODEL: str = "default"
    MAX_TEXT_LENGTH: int = 1000000  # 最大处理文本长度
    
    # PPT 生成配置
    PPT_DEFAULT_TEMPLATE: str = "default"
    PPT_MAX_SLIDES: int = 50
    
    # 图像处理配置
    IMAGE_MAX_SIZE: tuple = (1920, 1080)
    IMAGE_QUALITY: int = 85
    
    # MinerU API 配置
    MINERU_API: str = "https://mineru.net/api/v4/extract/task"
    MINERU_TOKEN: str = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI2OTMwMDM4MCIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2MjE0NzMxMywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiN2QyMWJjNjctOGI0ZC00YmQyLTgxMjItYmEzOWIxYWQ5MDZlIiwiZW1haWwiOiIiLCJleHAiOjE3NjMzNTY5MTN9.gZWhu-PKDvLA52rJn9n0hb8XpkYTeqG0bIDNJ3nRjLG7GoFhTUyb8RTPOg03jNxq9uvZPUElliFxqZyT2_20VA"
    class Config:
        env_file = ".env"
        case_sensitive = True

# 创建全局配置实例
settings = Settings()

# 确保必要的目录存在
def ensure_directories():
    """确保所有必要的目录都存在"""
    directories = [
        settings.UPLOAD_DIR,
        settings.STATIC_DIR,
        settings.OUTPUT_DIR,
        settings.TEMP_DIR,
        os.path.dirname(settings.LOG_FILE)
    ]
    
    for directory in directories:
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"📁 创建目录: {directory}")

# 初始化目录
ensure_directories()
