"""日志配置"""

import os
import logging
from logging.handlers import RotatingFileHandler

_LOG_FMT = "%(asctime)s [%(levelname)s] %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str = "keenpoint", level: str = "INFO", log_file: str = None) -> logging.Logger:
    """配置日志"""
    log = logging.getLogger(name)
    log.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    if log.handlers:
        return log
    
    fmt = logging.Formatter(_LOG_FMT, _DATE_FMT)
    
    # 控制台
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    log.addHandler(ch)
    
    # 文件
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        fh = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
        fh.setFormatter(fmt)
        log.addHandler(fh)
    
    return log


# 全局日志实例
logger = setup_logger("keenpoint", "INFO", "logs/app.log")
