"""
通用工具函数模块
提供文件处理、字符串处理等常用工具
"""

import os
import uuid
import hashlib
from datetime import datetime
from typing import Optional
from fastapi import UploadFile
from app.core.config import settings
from app.core.logger import logger

def generate_unique_id() -> str:
    """
    生成唯一标识符
    
    返回:
    - 唯一 ID 字符串
    """
    return str(uuid.uuid4())

def generate_file_hash(file_content: bytes) -> str:
    """
    生成文件内容的 MD5 哈希值
    
    参数:
    - file_content: 文件内容（字节）
    
    返回:
    - MD5 哈希字符串
    """
    return hashlib.md5(file_content).hexdigest()

async def save_upload_file(file: UploadFile, custom_name: Optional[str] = None) -> str:
    """
    保存上传的文件到本地
    
    参数:
    - file: FastAPI UploadFile 对象
    - custom_name: 自定义文件名（可选）
    
    返回:
    - 保存后的完整文件路径
    """
    try:
        # 生成唯一文件名
        file_ext = file.filename.split('.')[-1]
        if custom_name:
            filename = f"{custom_name}.{file_ext}"
        else:
            unique_id = generate_unique_id()
            filename = f"{unique_id}.{file_ext}"
        
        # 按日期组织目录
        date_dir = datetime.now().strftime("%Y%m%d")
        save_dir = os.path.join(settings.UPLOAD_DIR, date_dir)
        os.makedirs(save_dir, exist_ok=True)
        
        # 完整保存路径
        file_path = os.path.join(save_dir, filename)
        
        # 保存文件
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"✅ 文件保存成功: {file_path}")
        return file_path
    
    except Exception as e:
        logger.error(f"❌ 文件保存失败: {str(e)}")
        raise

def get_file_size(file_path: str) -> int:
    """
    获取文件大小（字节）
    
    参数:
    - file_path: 文件路径
    
    返回:
    - 文件大小（字节）
    """
    return os.path.getsize(file_path) if os.path.exists(file_path) else 0

def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小为可读格式
    
    参数:
    - size_bytes: 文件大小（字节）
    
    返回:
    - 格式化的大小字符串 (如 "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def clean_text(text: str) -> str:
    """
    清理文本内容（去除多余空白、特殊字符等）
    
    参数:
    - text: 原始文本
    
    返回:
    - 清理后的文本
    """
    import re
    # 替换多个空白为单个空格
    text = re.sub(r'\s+', ' ', text)
    # 去除首尾空白
    text = text.strip()
    return text

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本到指定长度
    
    参数:
    - text: 原始文本
    - max_length: 最大长度
    - suffix: 截断后缀
    
    返回:
    - 截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def ensure_directory_exists(directory: str) -> bool:
    """
    确保目录存在，不存在则创建
    
    参数:
    - directory: 目录路径
    
    返回:
    - 是否成功
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"📁 创建目录: {directory}")
        return True
    except Exception as e:
        logger.error(f"❌ 创建目录失败: {str(e)}")
        return False

def get_timestamp() -> str:
    """
    获取当前时间戳字符串
    
    返回:
    - 格式化的时间戳
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """
    验证文件扩展名是否在允许列表中
    
    参数:
    - filename: 文件名
    - allowed_extensions: 允许的扩展名列表
    
    返回:
    - 是否有效
    """
    ext = filename.split('.')[-1].lower()
    return ext in [e.lower() for e in allowed_extensions]
