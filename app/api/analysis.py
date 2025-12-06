"""
结构分析 API
对论文进行章节识别和内容分析
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, List
from fastapi import APIRouter, HTTPException
from app.services.api import pdf2md_api
from app.services.md_service import parse_markdown_structure
from app.core.logger import logger

# 创建路由器
router = APIRouter()


async def parse_latest_uploaded_file() -> Optional[str]:
    """
    读取 uploads 文件夹下最新时间文件夹内的最新文件，并调用 parser_service 进行解析
    
    Returns:
        Optional[str]: 解析成功返回文件路径，失败返回 None
    """
    uploads_dir = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\uploads")
    
    if not uploads_dir.exists():
        logger.error(f"上传目录不存在: {uploads_dir}")
        return None
    
    # 获取所有子文件夹，按修改时间排序
    subdirs = [d for d in uploads_dir.iterdir() if d.is_dir()]
    if not subdirs:
        logger.warning("上传目录下没有找到任何文件夹")
        return None
    
    # 找到最新的文件夹
    latest_dir = max(subdirs, key=lambda d: d.stat().st_mtime)
    logger.info(f"找到最新文件夹: {latest_dir}")
    
    # 获取该文件夹下的所有文件
    files = [f for f in latest_dir.iterdir() if f.is_file()]
    if not files:
        logger.warning(f"文件夹 {latest_dir} 中没有找到任何文件")
        return None
    
    # 找到最新的文件
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    logger.info(f"找到最新文件: {latest_file}")
    
    try:
        # 调用 parser_service 的 main 函数进行解析
        logger.info(f"开始解析文件: {latest_file}")
        await pdf2md_api.main([str(latest_file)])
        logger.info(f"文件解析完成: {latest_file}")
        return str(latest_file)
    except Exception as e:
        logger.error(f"文件解析失败: {e}")
        return None


def parse_latest_uploaded_file_sync() -> Optional[str]:
    """
    同步版本：读取 uploads 文件夹下最新时间文件夹内的最新文件，并调用 parser_service 进行解析
    
    Returns:
        Optional[str]: 解析成功返回文件路径，失败返回 None
    """
    return asyncio.run(parse_latest_uploaded_file())


def find_md_file_from_parsed() -> Optional[Path]:
    """
    从解析后的下载目录中查找MD文档
    
    Returns:
        Optional[Path]: 找到的MD文件路径，未找到返回 None
    """
    download_dir = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads")
    
    if not download_dir.exists():
        logger.error(f"下载目录不存在: {download_dir}")
        return None
    
    # 递归查找所有.md文件
    md_files = list(download_dir.rglob("*.md"))
    
    if not md_files:
        logger.warning("下载目录中没有找到任何MD文件")
        return None
    
    # 返回最新的MD文件
    latest_md = max(md_files, key=lambda f: f.stat().st_mtime)
    logger.info(f"找到最新MD文件: {latest_md}")
    
    return latest_md


def truncate_content(content: str, max_length: int = 50) -> str:
    """
    截断内容到指定长度
    
    Args:
        content: 原始内容
        max_length: 最大长度，默认50
    
    Returns:
        str: 截断后的内容
    """
    if len(content) <= max_length:
        return content
    return content[:max_length] + "..."


def process_structure_for_frontend(structure: List[Dict], truncate_length: int = 50) -> List[Dict]:
    """
    处理结构数据以供前端展示（递归处理子节点）
    
    Args:
        structure: 原始结构数据
        truncate_length: 内容截断长度
    
    Returns:
        List[Dict]: 处理后的结构数据
    """
    processed = []
    
    for item in structure:
        processed_item = {
            "level": item.get("level"),
            "title": item.get("title"),
            "content_preview": truncate_content(item.get("content", ""), truncate_length),
            "content_full": item.get("content", ""),
            "has_children": len(item.get("children", [])) > 0,
            "children_count": len(item.get("children", []))
        }
        
        # 如果有数字编号，添加编号信息
        if "number" in item:
            processed_item["number"] = item["number"]
            processed_item["number_str"] = ".".join(map(str, item["number"]))
        
        # 递归处理子节点
        if item.get("children"):
            processed_item["children"] = process_structure_for_frontend(
                item["children"], 
                truncate_length
            )
        else:
            processed_item["children"] = []
        
        processed.append(processed_item)
    
    return processed


async def parse_and_analyze_md() -> Dict:
    """
    解析上传的文件并分析MD文档结构
    
    Returns:
        Dict: 包含文档结构的JSON数据
    """
    # 1. 解析最新上传的文件
    logger.info("开始解析最新上传的文件...")
    file_path = await parse_latest_uploaded_file()
    
    if not file_path:
        raise Exception("未找到上传的文件或解析失败")
    
    # 2. 查找生成的MD文件
    logger.info("查找生成的MD文件...")
    md_file = find_md_file_from_parsed()
    
    if not md_file:
        raise Exception("未找到解析生成的MD文件")
    
    # 3. 读取MD文件内容
    logger.info(f"读取MD文件: {md_file}")
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 4. 解析MD文档结构（使用数字层级）
    logger.info("解析MD文档结构...")
    structure_data = parse_markdown_structure(md_content, use_numeric_hierarchy=True)
    
    # 5. 处理数据以供前端展示
    logger.info("处理数据以供前端展示...")
    processed_structure = process_structure_for_frontend(structure_data["structure"], truncate_length=50)
    
    # 6. 构建返回数据
    result = {
        "status": "success",
        "message": "文档结构解析成功",
        "data": {
            "title": structure_data["title"],
            "file_path": str(md_file),
            "metadata": structure_data["metadata"],
            "structure": processed_structure
        }
    }
    
    logger.info(f"解析完成: 共 {structure_data['metadata']['total_headings']} 个标题")
    
    return result


@router.post("/parse-structure")
async def parse_structure_api():
    """
    解析最新上传文件的文档结构
    
    Returns:
        Dict: 文档结构数据
    """
    try:
        result = await parse_and_analyze_md()
        return result
    except Exception as e:
        logger.error(f"解析文档结构失败: {e}")
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")


@router.get("/structure/{file_name}")
async def get_structure_by_file(file_name: str):
    """
    根据文件名获取文档结构
    
    Args:
        file_name: MD文件名
    
    Returns:
        Dict: 文档结构数据
    """
    try:
        download_dir = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads")
        
        # 查找指定的MD文件
        md_files = list(download_dir.rglob(f"**/{file_name}"))
        
        if not md_files:
            raise HTTPException(status_code=404, detail=f"未找到文件: {file_name}")
        
        md_file = md_files[0]
        
        # 读取并解析
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        structure_data = parse_markdown_structure(md_content, use_numeric_hierarchy=True)
        processed_structure = process_structure_for_frontend(structure_data["structure"], truncate_length=50)
        
        return {
            "status": "success",
            "data": {
                "title": structure_data["title"],
                "file_path": str(md_file),
                "metadata": structure_data["metadata"],
                "structure": processed_structure
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档结构失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")
