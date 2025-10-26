"""
文档上传 API
处理用户上传的 PDF 和 Word 文档
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import Dict
from app.services import parser_service
from app.core.logger import logger
from app.core.utils import save_upload_file

router = APIRouter()

@router.post("/", response_model=Dict)
async def upload_document(file: UploadFile = File(...)):
    """
    上传论文文档并解析
    
    支持的文件格式:
    - PDF (.pdf)
    - Word (.doc, .docx)
    
    返回:
    - status: 处理状态
    - data: 解析结果（包含文本、页数/段落数等）
    - file_id: 文件唯一标识符
    """
    logger.info(f"📥 收到文件上传请求: {file.filename}")
    
    # 验证文件类型
    allowed_extensions = ['pdf', 'doc', 'docx']
    file_ext = file.filename.split('.')[-1].lower()
    
    if file_ext not in allowed_extensions:
        logger.warning(f"❌ 不支持的文件类型: {file_ext}")
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。请上传 PDF 或 Word 文档。"
        )
    
    try:
        # 保存上传的文件
        file_path = await save_upload_file(file)
        logger.info(f"💾 文件已保存: {file_path}")
        
        # 解析文档内容
        result = await parser_service.parse_document(file)
        
        logger.info(f"✅ 文档解析成功: {file.filename}")
        
        return {
            "status": "success",
            "message": "文档上传并解析成功",
            "filename": file.filename,
            "data": result
        }
    
    except Exception as e:
        logger.error(f"❌ 文档处理失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"文档处理失败: {str(e)}"
        )

@router.post("/batch")
async def upload_multiple_documents(files: list[UploadFile] = File(...)):
    """
    批量上传多个文档
    
    返回每个文件的处理结果
    """
    logger.info(f"📥 收到批量上传请求，共 {len(files)} 个文件")
    
    results = []
    for file in files:
        try:
            result = await upload_document(file)
            results.append(result)
        except Exception as e:
            results.append({
                "status": "failed",
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "status": "completed",
        "total": len(files),
        "results": results
    }
