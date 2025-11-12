"""
图像处理服务
处理文档中的图片、表格、公式提取
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from app.core.logger import logger
from app.core.config import settings


async def extract_visual_elements(content_list_path: str) -> List[Dict]:
    """
    从 content_list.json 中提取视觉元素（图片、表格、公式）
    
    Args:
        content_list_path: content_list.json 文件的完整路径
    
    Returns:
        提取的视觉元素列表，每个元素不包含 bbox 字段
        
    Example:
        >>> elements = await extract_visual_elements("downloads/test/xxx_content_list.json")
        >>> print(len(elements))  # 输出提取的元素数量
    """
    try:
        # 读取 JSON 文件
        with open(content_list_path, 'r', encoding='utf-8') as f:
            content_list = json.load(f)
        
        logger.info(f"Reading content list from: {content_list_path}")
        logger.info(f"Total content blocks: {len(content_list)}")
        
        # 筛选类型为 image、table、equation 的元素
        visual_types = {'image', 'table', 'equation'}
        visual_elements = []
        
        type_counts = {'image': 0, 'table': 0, 'equation': 0}
        
        for item in content_list:
            item_type = item.get('type', '')
            
            if item_type in visual_types:
                # 创建新字典，排除 bbox 字段
                filtered_item = {k: v for k, v in item.items() if k != 'bbox'}
                visual_elements.append(filtered_item)
                
                # 统计数量
                type_counts[item_type] += 1
        
        # 输出统计信息
        logger.info(f"Extracted visual elements:")
        logger.info(f"  Images: {type_counts['image']}")
        logger.info(f"  Tables: {type_counts['table']}")
        logger.info(f"  Equations: {type_counts['equation']}")
        logger.info(f"  Total: {len(visual_elements)}")
        
        return visual_elements
    
    except FileNotFoundError:
        logger.error(f"File not found: {content_list_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error extracting visual elements: {str(e)}")
        return []


async def extract_visual_elements_from_folder(folder_path: str) -> Dict[str, List[Dict]]:
    """
    从指定文件夹中查找所有 content_list.json 文件并提取视觉元素
    
    Args:
        folder_path: 文件夹路径（如 downloads/）
    
    Returns:
        字典，key 为文件名，value 为提取的视觉元素列表
        
    Example:
        >>> results = await extract_visual_elements_from_folder("downloads")
        >>> for filename, elements in results.items():
        ...     print(f"{filename}: {len(elements)} elements")
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        logger.error(f"Folder not found: {folder_path}")
        return {}
    
    # 查找所有 content_list.json 文件
    content_files = list(folder.rglob("*content_list.json"))
    
    if not content_files:
        logger.warning(f"No content_list.json files found in: {folder_path}")
        return {}
    
    logger.info(f"Found {len(content_files)} content_list.json file(s)")
    
    results = {}
    
    for content_file in content_files:
        logger.info(f"Processing: {content_file}")
        
        # 提取视觉元素
        visual_elements = await extract_visual_elements(str(content_file))
        
        # 使用相对路径作为 key
        relative_path = content_file.relative_to(folder)
        results[str(relative_path)] = visual_elements
    
    return results


async def save_visual_elements(
    visual_elements: List[Dict],
    output_path: str,
    pretty: bool = True
) -> bool:
    """
    保存提取的视觉元素到 JSON 文件
    
    Args:
        visual_elements: 视觉元素列表
        output_path: 输出文件路径
        pretty: 是否格式化输出（默认 True）
    
    Returns:
        是否保存成功
    """
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 保存 JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(visual_elements, f, ensure_ascii=False, indent=2)
            else:
                json.dump(visual_elements, f, ensure_ascii=False)
        
        logger.info(f"Visual elements saved to: {output_path}")
        logger.info(f"Total elements: {len(visual_elements)}")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to save visual elements: {str(e)}")
        return False


async def get_visual_element_paths(
    visual_elements: List[Dict],
    base_folder: str
) -> Dict[str, List[str]]:
    """
    获取所有视觉元素的文件路径
    
    Args:
        visual_elements: 视觉元素列表
        base_folder: 基础文件夹路径
    
    Returns:
        字典，包含 images、tables、equations 的文件路径列表
    """
    paths = {
        'images': [],
        'tables': [],
        'equations': []
    }
    
    base_path = Path(base_folder)
    
    for element in visual_elements:
        element_type = element.get('type')
        img_path = element.get('img_path')
        
        if not img_path:
            continue
        
        # 构建完整路径
        full_path = base_path / img_path
        
        if full_path.exists():
            if element_type == 'image':
                paths['images'].append(str(full_path))
            elif element_type == 'table':
                paths['tables'].append(str(full_path))
            elif element_type == 'equation':
                paths['equations'].append(str(full_path))
        else:
            logger.warning(f"File not found: {full_path}")
    
    logger.info(f"Found file paths:")
    logger.info(f"  Images: {len(paths['images'])}")
    logger.info(f"  Tables: {len(paths['tables'])}")
    logger.info(f"  Equations: {len(paths['equations'])}")
    
    return paths


async def generate_visual_summary(visual_elements: List[Dict]) -> Dict:
    """
    生成视觉元素的统计摘要
    
    Args:
        visual_elements: 视觉元素列表
    
    Returns:
        包含统计信息的字典
    """
    summary = {
        'total_count': len(visual_elements),
        'by_type': {'image': 0, 'table': 0, 'equation': 0},
        'by_page': {},
        'with_caption': 0,
        'with_footnote': 0,
        'elements': []
    }
    
    for element in visual_elements:
        element_type = element.get('type', 'unknown')
        page_idx = element.get('page_idx', -1)
        
        # 统计类型
        if element_type in summary['by_type']:
            summary['by_type'][element_type] += 1
        
        # 统计页面分布
        if page_idx not in summary['by_page']:
            summary['by_page'][page_idx] = 0
        summary['by_page'][page_idx] += 1
        
        # 统计 caption 和 footnote
        if element_type == 'image':
            if element.get('image_caption'):
                summary['with_caption'] += 1
            if element.get('image_footnote'):
                summary['with_footnote'] += 1
        elif element_type == 'table':
            if element.get('table_caption'):
                summary['with_caption'] += 1
            if element.get('table_footnote'):
                summary['with_footnote'] += 1
        
        # 添加元素信息
        summary['elements'].append({
            'type': element_type,
            'page': page_idx,
            'path': element.get('img_path', ''),
            'has_caption': bool(
                element.get('image_caption') or 
                element.get('table_caption')
            )
        })
    
    return summary