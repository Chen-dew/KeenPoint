"""应用配置"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """配置项"""
    
    # 基础
    APP_NAME: str = "KeenPoint"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 路径
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    UPLOAD_DIR: str = "uploads"
    DOWNLOAD_DIR: str = "downloads"
    OUTPUT_DIR: str = "outputs"
    LOG_DIR: str = "logs"
    
    # 日志
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Dify API
    DIFY_API_KEY: Optional[str] = "app-VWzZqV55lOhVZoQm91SGaSLO"
    DIFY_API_URL: str = "https://api.dify.ai/v1"
    DIFY_USER: str = "keenpoint"
    
    # MinerU API
    MINERU_TOKEN: Optional[str] = None
    MINERU_MODEL: str = "vlm"
    MINERU_UPLOAD_URL: str = "https://mineru.net/api/v4/file-urls/batch"
    MINERU_RESULT_URL: str = "https://mineru.net/api/v4/extract-results/batch"
    MINERU_POLL_INTERVAL: int = 10
    
    # 限制
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024
    MAX_SEGMENT_LENGTH: int = 10000
    
    @property
    def MINERU_HEADERS(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.MINERU_TOKEN}"
        }
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def ensure_dirs():
    """创建必要目录"""
    for d in [settings.UPLOAD_DIR, settings.DOWNLOAD_DIR, settings.OUTPUT_DIR, settings.LOG_DIR]:
        os.makedirs(d, exist_ok=True)
