"""
文档上传 API
处理用户上传的 PDF 和 Word 文档
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import Dict
from app.core.logger import logger
from app.core.utils import save_upload_file, get_file_size, format_file_size
from app.core.config import settings
import os

router = APIRouter()

@router.post("/", response_model=Dict)
async def upload_document(file: UploadFile = File(...)):
    """
    上传论文文档
    
    支持的文件格式:
    - PDF (.pdf)
    - Word (.doc, .docx)
    - Text (.txt)
    
    返回:
    - status: 处理状态
    - file_path: 文件保存路径
    - file_info: 文件信息
    """
    logger.info(f"📥 收到文件上传请求: {file.filename}")
    
    # 验证文件类型
    file_ext = file.filename.split('.')[-1].lower()
    
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        logger.warning(f"❌ 不支持的文件类型: {file_ext}")
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。请上传 PDF、Word 或 TXT 文档。支持的格式: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # 检查文件大小
    content = await file.read()
    file_size = len(content)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        logger.warning(f"❌ 文件过大: {format_file_size(file_size)}")
        raise HTTPException(
            status_code=413,
            detail=f"文件过大。最大允许大小: {format_file_size(settings.MAX_UPLOAD_SIZE)}"
        )
    
    # 重置文件指针
    await file.seek(0)
    
    try:
        # 保存上传的文件到指定目录
        file_path = await save_upload_file(file)
        logger.info(f"💾 文件已保存: {file_path}")
        
        # 获取文件信息
        actual_size = get_file_size(file_path)
        
        logger.info(f"✅ 文档上传成功: {file.filename}")
        
        return {
            "status": "success",
            "message": "文档上传成功",
            "file_info": {
                "filename": file.filename,
                "file_path": file_path,
                "file_size": actual_size,
                "file_size_formatted": format_file_size(actual_size),
                "file_type": file_ext,
                "upload_dir": settings.UPLOAD_DIR
            }
        }
    
    except Exception as e:
        logger.error(f"❌ 文档上传失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"文档上传失败: {str(e)}"
        )
