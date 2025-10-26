"""
图像服务
处理 PDF 中图像的提取、分类和管理
"""

import fitz  # PyMuPDF
import os
from typing import List, Dict, Optional
from app.core.logger import logger
from app.core.config import settings
from app.core.utils import generate_unique_id, ensure_directory_exists

def extract_figures_from_pdf(pdf_path: str) -> List[Dict]:
    """
    从 PDF 中提取图像
    
    参数:
    - pdf_path: PDF 文件路径
    
    返回:
    - 图像信息列表
    """
    logger.info(f"🖼️ 开始从 PDF 提取图像: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        logger.error(f"❌ 文件不存在: {pdf_path}")
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
        images = []
        image_index = 0
        
        # 创建图像保存目录
        output_dir = os.path.join(settings.OUTPUT_DIR, "images", generate_unique_id())
        ensure_directory_exists(output_dir)
        
        # 遍历所有页面
        for page_num, page in enumerate(doc, start=1):
            # 获取页面中的图像
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]  # 图像的 xref 编号
                    base_image = doc.extract_image(xref)
                    
                    if base_image:
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # 保存图像
                        image_filename = f"figure_{image_index + 1}.{image_ext}"
                        image_path = os.path.join(output_dir, image_filename)
                        
                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)
                        
                        # 添加图像信息
                        images.append({
                            "id": image_index + 1,
                            "name": image_filename,
                            "path": image_path,
                            "page": page_num,
                            "type": _guess_image_type(image_filename),
                            "format": image_ext,
                            "size": len(image_bytes),
                            "caption": f"Figure {image_index + 1} from page {page_num}"
                        })
                        
                        image_index += 1
                
                except Exception as e:
                    logger.warning(f"⚠️ 提取图像失败 (page {page_num}): {str(e)}")
                    continue
        
        doc.close()
        
        logger.info(f"✅ 成功提取 {len(images)} 张图像")
        return images
    
    except Exception as e:
        logger.error(f"❌ 图像提取失败: {str(e)}")
        raise

def _guess_image_type(filename: str) -> str:
    """
    根据文件名推测图像类型
    
    参数:
    - filename: 文件名
    
    返回:
    - 图像类型
    """
    # 简单的启发式分类
    # 实际应用中应使用图像识别模型
    ext = filename.split('.')[-1].lower()
    
    if ext in ['jpg', 'jpeg']:
        return "photo"
    elif ext == 'png':
        return "chart"
    else:
        return "diagram"

def get_images_by_document(document_id: str, image_type: Optional[str] = None) -> List[Dict]:
    """
    获取指定文档的图像列表
    
    参数:
    - document_id: 文档 ID
    - image_type: 可选的类型过滤
    
    返回:
    - 图像列表
    """
    logger.info(f"📋 获取文档 {document_id} 的图像列表")
    
    # 模拟数据（实际应从数据库查询）
    sample_images = [
        {
            "id": 1,
            "name": "Figure 1",
            "type": "chart",
            "caption": "实验结果比较",
            "path": "/outputs/images/figure_1.png"
        },
        {
            "id": 2,
            "name": "Figure 2",
            "type": "diagram",
            "caption": "系统架构图",
            "path": "/outputs/images/figure_2.png"
        },
        {
            "id": 3,
            "name": "Figure 3",
            "type": "photo",
            "caption": "实验设备照片",
            "path": "/outputs/images/figure_3.jpg"
        }
    ]
    
    # 类型过滤
    if image_type:
        sample_images = [img for img in sample_images if img["type"] == image_type]
    
    return sample_images

def classify_images(image_paths: List[str]) -> Dict:
    """
    对图像进行自动分类
    
    参数:
    - image_paths: 图像路径列表
    
    返回:
    - 分类结果
    """
    logger.info(f"🏷️ 开始对 {len(image_paths)} 张图像进行分类")
    
    classified = {
        "chart": [],
        "diagram": [],
        "photo": [],
        "equation": []
    }
    
    for img_path in image_paths:
        # 简单的基于扩展名的分类
        # 实际应使用图像识别模型
        image_type = _guess_image_type(img_path)
        
        if image_type in classified:
            classified[image_type].append({
                "path": img_path,
                "name": os.path.basename(img_path)
            })
        else:
            classified["diagram"].append({
                "path": img_path,
                "name": os.path.basename(img_path)
            })
    
    logger.info(f"✅ 分类完成: {len(classified['chart'])} 图表, "
                f"{len(classified['diagram'])} 示意图, "
                f"{len(classified['photo'])} 照片")
    
    return classified

def export_images(
    document_id: str,
    export_format: str = "zip",
    include_captions: bool = True
) -> Dict:
    """
    导出文档的所有图像
    
    参数:
    - document_id: 文档 ID
    - export_format: 导出格式
    - include_captions: 是否包含图注
    
    返回:
    - 导出结果
    """
    logger.info(f"📦 导出文档 {document_id} 的图像")
    
    try:
        # 获取图像列表
        images = get_images_by_document(document_id)
        
        # 创建导出目录
        export_dir = os.path.join(settings.OUTPUT_DIR, "exports", document_id)
        ensure_directory_exists(export_dir)
        
        if export_format == "zip":
            import zipfile
            zip_path = os.path.join(export_dir, f"{document_id}_images.zip")
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for img in images:
                    if os.path.exists(img["path"]):
                        zipf.write(img["path"], os.path.basename(img["path"]))
                    
                    # 如果需要包含图注
                    if include_captions:
                        caption_file = f"{img['name']}_caption.txt"
                        caption_path = os.path.join(export_dir, caption_file)
                        with open(caption_path, 'w', encoding='utf-8') as f:
                            f.write(img.get("caption", ""))
                        zipf.write(caption_path, caption_file)
                        os.remove(caption_path)
            
            logger.info(f"✅ 图像已导出到: {zip_path}")
            
            return {
                "url": zip_path,
                "size": os.path.getsize(zip_path) if os.path.exists(zip_path) else 0,
                "format": "zip"
            }
        
        else:
            # 导出为文件夹
            logger.info(f"✅ 图像已导出到目录: {export_dir}")
            return {
                "url": export_dir,
                "format": "folder"
            }
    
    except Exception as e:
        logger.error(f"❌ 图像导出失败: {str(e)}")
        raise
