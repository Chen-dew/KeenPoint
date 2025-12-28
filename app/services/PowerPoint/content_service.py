"""内容服务 - 整合大纲、解析和图表分析数据"""

from typing import Dict, List, Any
from app.core.logger import logger

TAG = "[CONTENT]"


def _find_section_in_parse(section_name: str, parse_result: Dict) -> Dict:
    """在解析结果中查找对应章节"""
    sections = parse_result.get("sections", [])
    
    for sec in sections:
        if sec.get("name", "") == section_name:
            return sec
    
    # 尝试模糊匹配（去除数字前缀）
    clean_name = section_name.lstrip("0123456789. ")
    for sec in sections:
        sec_name = sec.get("name", "").lstrip("0123456789. ")
        if sec_name == clean_name:
            return sec
    
    logger.warning(f"{TAG} section not found: {section_name}")
    return {}


def _find_element_by_id(element_id: int, element_type: str, parse_section: Dict) -> Dict:
    """根据ID和类型查找元素"""
    ref_map = {
        "image": "fig_refs",
        "table": "table_refs",
        "equation": "formula_refs"
    }
    
    ref_key = ref_map.get(element_type)
    if not ref_key:
        return {}
    
    refs = parse_section.get(ref_key, [])
    for ref in refs:
        if ref.get("id") == element_id:
            return ref
    
    return {}


def _find_analysis_text(element_id: int, element_type: str, visual_analysis: List[Dict]) -> str:
    """从视觉分析结果中查找分析文本"""
    if not isinstance(visual_analysis, list):
        return ""
    
    for item in visual_analysis:
        elem = item.get("element", {})
        if elem.get("id") == element_id and elem.get("type") == element_type:
            analysis = item.get("analysis", {})
            return analysis.get("analysis_text", "")
    
    return ""


def build_slide_content(outline_section: Dict, parse_result: Dict, 
                        visual_analysis: List[Dict]) -> List[Dict]:
    """构建幻灯片内容
    
    Args:
        outline_section: 大纲中的一个章节，包含 {section_name, raw_result}
        parse_result: 完整的文档解析结果
        visual_analysis: 完整的视觉分析结果
    
    Returns:
        list: 该章节的所有幻灯片内容列表
    """
    section_name = outline_section.get("section_name", "")
    raw_result = outline_section.get("raw_result", {})
    
    if not raw_result or outline_section.get("error"):
        logger.warning(f"{TAG} skip section: {section_name}, error={outline_section.get('error')}")
        return []
    
    # 在解析结果中找到对应章节
    parse_section = _find_section_in_parse(section_name, parse_result)
    section_content = parse_section.get("content", "")
    
    # 获取大纲中的幻灯片列表
    ppt_outline = raw_result.get("ppt_outline", [])
    if not ppt_outline:
        logger.warning(f"{TAG} no ppt_outline for section: {section_name}")
        return []
    
    slides = []
    
    for slide_data in ppt_outline:
        slide_title = slide_data.get("slide_title", "")
        slide_purpose = slide_data.get("slide_purpose", "")
        content_points = slide_data.get("content_points", [])
        visual_refs_ids = slide_data.get("visual_refs", {})
        
        # 构建完整的 visual_refs（包含详细信息和分析文本）
        visual_refs = {
            "images": [],
            "tables": [],
            "equations": []
        }
        
        # 处理图片引用
        for img_id in visual_refs_ids.get("images", []):
            elem = _find_element_by_id(img_id, "image", parse_section)
            if elem:
                elem_full = {
                    "type": "image",
                    "id": img_id,
                    "img_path": elem.get("img_path", ""),
                    "caption": elem.get("caption", ""),
                    "analysis_text": _find_analysis_text(img_id, "image", visual_analysis)
                }
                visual_refs["images"].append(elem_full)
        
        # 处理表格引用
        for tbl_id in visual_refs_ids.get("tables", []):
            elem = _find_element_by_id(tbl_id, "table", parse_section)
            if elem:
                elem_full = {
                    "type": "table",
                    "id": tbl_id,
                    "img_path": elem.get("img_path", ""),
                    "caption": elem.get("caption", ""),
                    "body": elem.get("body", ""),
                    "analysis_text": _find_analysis_text(tbl_id, "table", visual_analysis)
                }
                visual_refs["tables"].append(elem_full)
        
        # 处理公式引用
        for eq_id in visual_refs_ids.get("equations", []):
            elem = _find_element_by_id(eq_id, "equation", parse_section)
            if elem:
                elem_full = {
                    "type": "equation",
                    "id": eq_id,
                    "img_path": elem.get("img_path", ""),
                    "text": elem.get("text", ""),
                    "text_format": elem.get("text_format", "latex"),
                    "analysis_text": _find_analysis_text(eq_id, "equation", visual_analysis)
                }
                visual_refs["equations"].append(elem_full)
        
        # 组装幻灯片内容
        slide_content = {
            "slide_title": slide_title,
            "section_name": section_name,
            "slide_purpose": slide_purpose,
            "content_points": content_points,
            "content": section_content,
            "visual_refs": visual_refs
        }
        
        slides.append(slide_content)
        
        logger.debug(f"{TAG} slide: {slide_title[:40]}, "
                    f"refs=({len(visual_refs['images'])},{len(visual_refs['tables'])},{len(visual_refs['equations'])})")
    
    logger.info(f"{TAG} section '{section_name}': {len(slides)} slides")
    return slides


def build_all_slides_content(outline_result: Dict, parse_result: Dict, 
                             visual_analysis: List[Dict]) -> Dict:
    """构建所有幻灯片内容
    
    Args:
        outline_result: 大纲生成结果，包含 {sections: [...], statistics: {...}}
        parse_result: 文档解析结果
        visual_analysis: 视觉分析结果
    
    Returns:
        dict: {
            slides: [所有幻灯片内容],
            statistics: {total_slides, total_sections, ...}
        }
    """
    logger.info(f"{TAG} building all slides content")
    
    outline_sections = outline_result.get("sections", [])
    all_slides = []
    
    for section in outline_sections:
        if section.get("error"):
            logger.warning(f"{TAG} skip error section: {section.get('section_name')}")
            continue
        
        slides = build_slide_content(section, parse_result, visual_analysis)
        all_slides.extend(slides)
    
    logger.info(f"{TAG} total slides: {len(all_slides)} from {len(outline_sections)} sections")
    
    return {
        "slides": all_slides,
        "statistics": {
            "total_slides": len(all_slides),
            "total_sections": len(outline_sections),
            "success_sections": len([s for s in outline_sections if not s.get("error")]),
            "failed_sections": len([s for s in outline_sections if s.get("error")])
        }
    }


def build_content_from_process_result(process_result: Dict) -> Dict:
    """从 process_document 结果构建幻灯片内容
    
    Args:
        process_result: process_document 的完整输出
    
    Returns:
        dict: {slides: [...], statistics: {...}}
    """
    outline = process_result.get("outline", {})
    parse_result = process_result.get("parse_result", {})
    visual_analysis = process_result.get("visual_analysis", [])
    
    return build_all_slides_content(outline, parse_result, visual_analysis)
