"""大纲生成服务 - 解析文档并生成PPT大纲"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.logger import logger
from app.services.clients.dify_workflow_client import analyze_outline
from app.services.document.parse_service import parse_markdown
from app.services.document.image_service import extract_elements, analyze_elements

TAG = "[OUTLINE]"


def _build_element_map(visual_analysis: List[Dict]) -> Dict[str, Dict[int, str]]:
    """构建元素ID到分析文本的映射"""
    result = {"images": {}, "tables": {}, "equations": {}}
    
    if not isinstance(visual_analysis, list):
        return result
    
    type_map = {"image": "images", "table": "tables", "equation": "equations"}
    
    for item in visual_analysis:
        elem = item.get("element", {})
        analysis = item.get("analysis", {})
        elem_type = elem.get("type")
        elem_id = elem.get("id")
        
        if analysis and elem_id is not None and elem_type in type_map:
            result[type_map[elem_type]][elem_id] = analysis.get("analysis_text", "")
    
    logger.info(f"{TAG} element_map: img={len(result['images'])}, "
                f"tbl={len(result['tables'])}, eq={len(result['equations'])}")
    return result


def _extract_refs(section: Dict, element_map: Dict) -> Dict[str, List[Dict]]:
    """提取章节的图表公式引用"""
    refs = {"images": [], "tables": [], "equations": []}
    
    ref_config = [
        ("fig_refs", "images"),
        ("table_refs", "tables"),
        ("formula_refs", "equations")
    ]
    
    for src_key, dst_key in ref_config:
        for ref in section.get(src_key, []):
            ref_id = ref.get("id")
            if ref_id is not None and ref_id in element_map[dst_key]:
                refs[dst_key].append({
                    "id": ref_id,
                    "analyze_text": element_map[dst_key][ref_id]
                })
    
    return refs


def _extract_sections(parse_result: Dict, element_map: Dict) -> List[Dict]:
    """提取章节数据，跳过第一章节和abstract"""
    sections = parse_result.get("sections", [])
    if not sections:
        logger.warning(f"{TAG} no sections found")
        return []
    
    # 获取摘要
    abstract = ""
    for sec in sections:
        if "abstract" in sec.get("name", "").lower():
            abstract = sec.get("content", "")
            break
    
    results = []
    for idx, sec in enumerate(sections):
        name = sec.get("name", "")
        
        # 跳过第一章节和abstract
        if idx == 0 or "abstract" in name.lower():
            logger.debug(f"{TAG} skip: {name}")
            continue
        
        refs = _extract_refs(sec, element_map)
        results.append({
            "abstract": abstract,
            "section_name": name,
            "content": sec.get("content", ""),
            "refs": refs
        })
        
        logger.debug(f"{TAG} section[{idx}]: {name[:30]}, "
                    f"refs=({len(refs['images'])},{len(refs['tables'])},{len(refs['equations'])})")
    
    logger.info(f"{TAG} extracted {len(results)} sections")
    return results


def generate_outline(parse_result: Dict, visual_analysis: List[Dict]) -> Dict:
    """生成PPT大纲
    
    Args:
        parse_result: 文档解析结果
        visual_analysis: 图表公式分析结果
    
    Returns:
        {sections: [{section_name, raw_result}], statistics: {total, success, failed}}
    """
    logger.info(f"{TAG} generating outline")
    
    element_map = _build_element_map(visual_analysis)
    sections_data = _extract_sections(parse_result, element_map)
    
    if not sections_data:
        return {"sections": [], "statistics": {"total": 0, "success": 0, "failed": 0}}
    
    results = []
    total = len(sections_data)
    
    for idx, data in enumerate(sections_data, 1):
        name = data["section_name"]
        logger.info(f"{TAG} [{idx}/{total}] {name[:40]}")
        
        try:
            query = json.dumps(data, ensure_ascii=False)
            raw_result = analyze_outline(query=query)
            results.append({"section_name": name, "raw_result": raw_result})
            logger.info(f"{TAG} [{idx}/{total}] success")
        except Exception as e:
            logger.error(f"{TAG} [{idx}/{total}] failed: {e}")
            results.append({"section_name": name, "raw_result": None, "error": str(e)})
        
        if idx < total:
            time.sleep(1)
    
    success = len([r for r in results if not r.get("error")])
    failed = total - success
    logger.info(f"{TAG} done: success={success}, failed={failed}")
    
    return {
        "sections": results,
        "statistics": {"total": total, "success": success, "failed": failed}
    }


def process_document(md_path: str, json_path: Optional[str] = None) -> Dict:
    """完整文档处理流程
    
    Args:
        md_path: Markdown文件路径
        json_path: content_list.json路径（可选）
    
    Returns:
        {parse_result, visual_analysis, outline, statistics}
    """
    logger.info(f"{TAG} process: {md_path}")
    base = Path(md_path).parent
    
    # 解析文档
    parse_result = parse_markdown(md_path, json_path)
    logger.info(f"{TAG} parsed: {parse_result.get('metadata', {})}")
    
    # 提取并分析图表公式
    elements = extract_elements(parse_result)
    visual_analysis = analyze_elements(elements, base)
    analyzed = len([v for v in visual_analysis if v.get("analysis")])
    logger.info(f"{TAG} elements: {len(elements)} extracted, {analyzed} analyzed")
    
    # 生成大纲
    outline = generate_outline(parse_result, visual_analysis)
    
    meta = parse_result.get("metadata", {})
    stats = outline.get("statistics", {})
    
    return {
        "parse_result": parse_result,
        "visual_analysis": visual_analysis,
        "outline": outline,
        "statistics": {
            "sections": meta.get("total_sections", 0),
            "elements": len(elements),
            "analyzed": analyzed,
            "outline_total": stats.get("total", 0),
            "outline_success": stats.get("success", 0),
            "outline_failed": stats.get("failed", 0)
        }
    }

