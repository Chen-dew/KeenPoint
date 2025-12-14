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
    UPLOAD_DIR: str = r"D:\MyFiles\AIPPT\Code\keenPoint\uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list = ["pdf", "doc", "docx", "txt"]
    
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
    
    # DashScope (阿里云百炼) 配置
    DASHSCOPE_API_KEY: Optional[str] = "sk-ede7a86133d54732b59b8b6b4596ad31"
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    DASHSCOPE_MODEL: str = "deepseek-v3.2"
    
    # Dify 配置
    DIFY_IMAGE_API_KEY: Optional[str] = "app-x0l8Aj6TPR3dge76Lg5x1tRA"  # 图像分析 API Key
    DIFY_TEXT_API_KEY: Optional[str] = "app-LAveMnIbI7rybMZ5hVJnJgpP"  # 文本分析 API Key
    DIFY_API_BASE_URL: str = "https://api.dify.ai/v1"
    DIFY_USER: str = "keenpoint-user"
    
    # PPT 生成配置
    PPT_DEFAULT_TEMPLATE: str = "default"
    PPT_MAX_SLIDES: int = 50
    
    # 图像处理配置
    IMAGE_MAX_SIZE: tuple = (1920, 1080)
    IMAGE_QUALITY: int = 85
    
    # MinerU API 配置
    MINERU_API_TOKEN: str = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI2OTMwMDM4MCIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2NDkxNjA4NCwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiOTY3OTFmOWYtNTZiOS00ZjI3LTgyYjEtYmU1OTM5OWRlMGZhIiwiZW1haWwiOiIiLCJleHAiOjE3NjYxMjU2ODR9.qgCbgHxh-uJDRrQ43SHATSgMrzvAq7oWBXsedrWnM8kaYRUdGKQAqcLDz1HTky5yjTjlt6PCgdj0RBwK_PUkiA"
    MINERU_MODEL_VERSION: str = "vlm"  # "pipeline" or "vlm"
    MINERU_UPLOAD_URL: str = "https://mineru.net/api/v4/file-urls/batch"
    MINERU_RESULT_URL: str = "https://mineru.net/api/v4/extract-results/batch"
    MINERU_POLL_INTERVAL: int = 10  # seconds
    MINERU_DOWNLOAD_DIR: str = "./downloads"
    
    @property
    def MINERU_HEADERS(self):
        """MinerU API request headers"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.MINERU_API_TOKEN}"
        }
    
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
