"""
PPT 生成 API
根据论文分析结果自动生成演示文稿
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
from app.services import ppt_service
from app.core.logger import logger

router = APIRouter()

class PPTGenerationRequest(BaseModel):
    """PPT 生成请求模型"""
    document_id: str
    structure_data: Dict
    include_images: bool = True
    template: str = "default"
    options: Optional[Dict] = {}

class PPTGenerationResponse(BaseModel):
    """PPT 生成响应模型"""
    status: str
    ppt_path: str
    slide_count: int
    download_url: str

@router.post("/generate", response_model=PPTGenerationResponse)
async def generate_ppt(request: PPTGenerationRequest):
    """
    根据论文结构生成 PPT
    
    参数:
    - document_id: 文档 ID
    - structure_data: 论文结构分析数据
    - include_images: 是否包含图像
    - template: PPT 模板 (default/academic/modern)
    - options: 其他自定义选项
    
    返回:
    - status: 生成状态
    - ppt_path: PPT 文件路径
    - slide_count: 幻灯片数量
    - download_url: 下载链接
    """
    logger.info(f"📊 开始生成 PPT，文档 ID: {request.document_id}")
    
    if not request.structure_data:
        raise HTTPException(
            status_code=400,
            detail="缺少结构数据，无法生成 PPT"
        )
    
    try:
        # 生成 PPT
        result = ppt_service.generate_ppt(
            structure_data=request.structure_data,
            include_images=request.include_images,
            template=request.template,
            options=request.options
        )
        
        logger.info(f"✅ PPT 生成成功: {result['ppt_path']}")
        
        return {
            "status": "success",
            "ppt_path": result["ppt_path"],
            "slide_count": result.get("slide_count", 0),
            "download_url": f"/api/v1/ppt/download?file={result['ppt_path']}"
        }
    
    except Exception as e:
        logger.error(f"❌ PPT 生成失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"PPT 生成失败: {str(e)}"
        )

@router.get("/download")
async def download_ppt(file: str):
    """
    下载生成的 PPT 文件
    
    参数:
    - file: PPT 文件路径
    
    返回:
    - 文件流
    """
    logger.info(f"📥 下载 PPT 文件: {file}")
    
    try:
        import os
        if not os.path.exists(file):
            raise HTTPException(
                status_code=404,
                detail="文件不存在"
            )
        
        return FileResponse(
            path=file,
            filename=os.path.basename(file),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
    
    except Exception as e:
        logger.error(f"❌ 文件下载失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"文件下载失败: {str(e)}"
        )

@router.post("/customize")
async def customize_ppt(
    ppt_path: str,
    customizations: Dict
):
    """
    自定义 PPT 样式
    
    参数:
    - ppt_path: 现有 PPT 文件路径
    - customizations: 自定义配置
        - theme: 主题颜色
        - font: 字体设置
        - layout: 布局调整
    
    返回:
    - 更新后的 PPT 路径
    """
    logger.info(f"🎨 自定义 PPT 样式: {ppt_path}")
    
    try:
        result = ppt_service.customize_ppt(ppt_path, customizations)
        
        return {
            "status": "success",
            "ppt_path": result["ppt_path"],
            "message": "PPT 样式已更新"
        }
    
    except Exception as e:
        logger.error(f"❌ PPT 自定义失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"PPT 自定义失败: {str(e)}"
        )

@router.get("/templates")
async def list_templates():
    """
    获取可用的 PPT 模板列表
    
    返回:
    - templates: 模板列表
    """
    templates = [
        {
            "id": "default",
            "name": "默认模板",
            "description": "简洁的学术风格",
            "preview": "/static/templates/default_preview.png"
        },
        {
            "id": "academic",
            "name": "学术模板",
            "description": "专业的学术报告风格",
            "preview": "/static/templates/academic_preview.png"
        },
        {
            "id": "modern",
            "name": "现代模板",
            "description": "现代化设计风格",
            "preview": "/static/templates/modern_preview.png"
        }
    ]
    
    return {
        "status": "success",
        "templates": templates,
        "count": len(templates)
    }
