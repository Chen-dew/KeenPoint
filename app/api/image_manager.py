"""
图像管理 API
处理论文中的图像提取、分类和导出
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
from app.services import image_service
from app.core.logger import logger

router = APIRouter()

@router.post("/extract")
async def extract_images(pdf_path: str):
    """
    从 PDF 中提取所有图像
    
    参数:
    - pdf_path: PDF 文件路径
    
    返回:
    - images: 提取的图像列表
    - count: 图像数量
    """
    logger.info(f"🖼️ 开始从 PDF 提取图像: {pdf_path}")
    
    try:
        images = image_service.extract_figures_from_pdf(pdf_path)
        
        logger.info(f"✅ 成功提取 {len(images)} 张图像")
        
        return {
            "status": "success",
            "images": images,
            "count": len(images)
        }
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"文件未找到: {pdf_path}"
        )
    except Exception as e:
        logger.error(f"❌ 图像提取失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"图像提取失败: {str(e)}"
        )

@router.get("/list")
async def list_images(
    document_id: str = Query(..., description="文档 ID"),
    image_type: str = Query(None, description="图像类型过滤 (chart/diagram/photo)")
):
    """
    列出文档的所有图像
    
    参数:
    - document_id: 文档唯一标识符
    - image_type: 可选的图像类型过滤
    
    返回:
    - images: 图像列表
    """
    logger.info(f"📋 查询文档 {document_id} 的图像列表")
    
    try:
        images = image_service.get_images_by_document(document_id, image_type)
        
        return {
            "status": "success",
            "document_id": document_id,
            "images": images,
            "count": len(images)
        }
    
    except Exception as e:
        logger.error(f"❌ 获取图像列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取图像列表失败: {str(e)}"
        )

@router.post("/classify")
async def classify_images(image_paths: List[str]):
    """
    对图像进行自动分类
    
    分类类型:
    - chart: 图表 (柱状图、折线图等)
    - diagram: 示意图
    - photo: 照片
    - equation: 公式
    
    参数:
    - image_paths: 图像路径列表
    
    返回:
    - classified: 分类结果
    """
    logger.info(f"🏷️ 开始对 {len(image_paths)} 张图像进行分类")
    
    try:
        classified = image_service.classify_images(image_paths)
        
        return {
            "status": "success",
            "classified": classified,
            "total": len(image_paths)
        }
    
    except Exception as e:
        logger.error(f"❌ 图像分类失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"图像分类失败: {str(e)}"
        )

@router.post("/export")
async def export_images(
    document_id: str,
    export_format: str = "zip",
    include_captions: bool = True
):
    """
    导出文档中的所有图像
    
    参数:
    - document_id: 文档 ID
    - export_format: 导出格式 (zip/folder)
    - include_captions: 是否包含图注
    
    返回:
    - download_url: 下载链接
    """
    logger.info(f"📦 导出文档 {document_id} 的图像")
    
    try:
        export_result = image_service.export_images(
            document_id,
            export_format,
            include_captions
        )
        
        return {
            "status": "success",
            "download_url": export_result["url"],
            "file_size": export_result.get("size", 0),
            "format": export_format
        }
    
    except Exception as e:
        logger.error(f"❌ 图像导出失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"图像导出失败: {str(e)}"
        )
