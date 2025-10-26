"""
日志配置模块
提供统一的日志记录功能
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from app.core.config import settings
import os

# 创建日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name: str = "app") -> logging.Logger:
    """
    配置并返回日志记录器
    
    参数:
    - name: 日志记录器名称
    
    返回:
    - logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器 (带自动轮转)
    try:
        # 确保日志目录存在
        log_dir = os.path.dirname(settings.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"无法创建文件日志处理器: {e}")
    
    return logger

# 创建全局日志实例
logger = setup_logger("academic_paper_assistant")

# 便捷函数
def log_info(message: str):
    """记录信息级别日志"""
    logger.info(message)

def log_warning(message: str):
    """记录警告级别日志"""
    logger.warning(message)

def log_error(message: str, exc_info=False):
    """记录错误级别日志"""
    logger.error(message, exc_info=exc_info)

def log_debug(message: str):
    """记录调试级别日志"""
    logger.debug(message)
