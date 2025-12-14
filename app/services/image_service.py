"""图表公式提取与分析服务"""

import re
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.core.logger import logger
from app.services.clients.dify_client import analyze_image, get_image_client


def _extract_local_context(content: str, element_id: int, element_type: str, window_size: int = 200) -> str:
    """提取元素上下文"""
    patterns = {
        "image": rf'(?:Figure|Fig\.|图)\s*{element_id}\b',
        "table": rf'(?:Table|Tab\.|表)\s*{element_id}\b'
    }
    
    pattern = patterns.get(element_type)
    if not pattern:
        return ""
    
    match = re.search(pattern, content, re.IGNORECASE)
    if not match:
        return ""
    
    pos = match.start()
    start = max(0, pos - window_size)
    end = min(len(content), pos + window_size)
    context = content[start:end].strip()
    
    if start > 0:
        context = "..." + context
    if end < len(content):
        context = context + "..."
    
    return context


def extract_elements_with_context(parse_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从解析结果中提取图表公式及上下文"""
    sections = parse_result.get("sections", [])
    
    # 提取摘要
    abstract = ""
    for section in sections:
        if section.get("name", "").lower() in ["abstract", "摘要"]:
            abstract = section.get("content", "")
            break
    
    results = []
    
    for section in sections:
        section_name = section.get("name", "")
        section_content = section.get("content", "")
        section_path = section.get("path", "")
        
        # 图片
        for fig in section.get("fig_refs", []):
            results.append({
                "abstract": abstract,
                "element": {
                    "type": "image",
                    "id": fig.get("id"),
                    "img_path": fig.get("img_path", ""),
                    "caption": fig.get("caption", "")
                },
                "local_context": _extract_local_context(section_content, fig.get("id"), "image"),
                "section_content": section_content,
                "section_name": section_name,
                "section_path": section_path
            })
        
        # 表格
        for table in section.get("table_refs", []):
            results.append({
                "abstract": abstract,
                "element": {
                    "type": "table",
                    "id": table.get("id"),
                    "img_path": table.get("img_path", ""),
                    "caption": table.get("caption", ""),
                    "body": table.get("body", "")
                },
                "local_context": _extract_local_context(section_content, table.get("id"), "table"),
                "section_content": section_content,
                "section_name": section_name,
                "section_path": section_path
            })
        
        # 公式
        for formula in section.get("formula_refs", []):
            results.append({
                "abstract": abstract,
                "element": {
                    "type": "equation",
                    "id": formula.get("id"),
                    "img_path": formula.get("img_path", ""),
                    "text": formula.get("text", ""),
                    "text_format": formula.get("text_format", "latex")
                },
                "local_context": "",
                "section_content": section_content,
                "section_name": section_name,
                "section_path": section_path
            })
    
    logger.info(f"提取元素: {len(results)} 个")
    return results


def analyze_elements_with_dify(elements: List[Dict[str, Any]], base_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """使用 Dify 分析图表公式"""
    if not elements:
        logger.warning("无元素需分析")
        return []
    
    logger.info(f"开始分析: {len(elements)} 个元素")
    results = []
    
    for idx, elem_data in enumerate(elements, 1):
        element = elem_data.get("element", {})
        element_type = element.get("type")
        element_id = element.get("id")
        img_path = element.get("img_path", "")
        
        logger.info(f"[{idx}/{len(elements)}] {element_type}-{element_id}")
        
        # 验证图片路径
        if not img_path:
            logger.warning(f"{element_type}-{element_id}: 无图片路径")
            results.append({**elem_data, "analysis": None, "error": "无图片路径"})
            continue
        
        full_img_path = (base_path / img_path) if base_path else Path(img_path)
        if not full_img_path.exists():
            logger.warning(f"{element_type}-{element_id}: 图片不存在 {full_img_path}")
            results.append({**elem_data, "analysis": None, "error": "图片不存在"})
            continue
        
        # 上传图片
        try:
            client = get_image_client()
            upload_result = client.upload_file(str(full_img_path))
            uploaded_file_id = upload_result.get('id')
            logger.info(f"上传成功: {uploaded_file_id}")
        except Exception as e:
            logger.error(f"上传失败: {str(e)}")
            results.append({**elem_data, "analysis": None, "error": f"上传失败: {str(e)}"})
            continue
        
        # 构建提示词
        element_with_id = element.copy()
        element_with_id['img_path'] = uploaded_file_id
        
        prompt = json.dumps({
            "abstract": elem_data.get("abstract", ""),
            "element": element_with_id,
            "local_context": elem_data.get("local_context", ""),
            "section_content": elem_data.get("section_content", "")
        }, ensure_ascii=False, indent=2)
        
        # 分析（带重试）
        analysis_result = None
        last_error = None
        
        for retry in range(3):
            try:
                answer = ""
                for chunk in analyze_image(query=prompt, file_ids=[uploaded_file_id], auto_upload=False):
                    answer = chunk
                
                if answer:
                    analysis_result = _parse_analysis_response(answer, element_type, element_id)
                    break
            except Exception as e:
                last_error = e
                logger.error(f"分析失败 (重试{retry + 1}/3): {str(e)}")
                if retry < 2:
                    time.sleep(2 ** (retry + 1))
        
        # 保存结果
        if analysis_result:
            results.append({**elem_data, "prompt": prompt, "analysis": analysis_result, "error": None})
            logger.info(f"分析完成: {element_type}-{element_id}")
        else:
            error_msg = str(last_error) if last_error else "未知错误"
            results.append({**elem_data, "prompt": prompt, "analysis": None, "error": error_msg})
            logger.error(f"分析失败: {element_type}-{element_id} - {error_msg}")
        
        if idx < len(elements):
            time.sleep(1)
    
    success = len([r for r in results if r.get("analysis")])
    logger.info(f"分析完成: 成功 {success}, 失败 {len(results) - success}")
    return results


def _parse_analysis_response(answer: str, element_type: str, element_id: int) -> Dict[str, Any]:
    """解析分析响应"""
    default_result = {
        "element_id": element_id,
        "element_type": element_type,
        "ppt_content": {"title": "", "bullet_points": [], "highlight": ""},
        "speaker_notes": {"explanation": "", "key_reasoning": [], "interpretation_details": ""}
    }
    
    if not answer:
        return default_result
    
    # 提取JSON
    json_str = answer.strip()
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0].strip()
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0].strip()
    
    try:
        parsed = json.loads(json_str)
        return {
            "element_id": parsed.get("element_id", element_id),
            "element_type": parsed.get("element_type", element_type),
            "ppt_content": {
                "title": parsed.get("ppt_content", {}).get("title", ""),
                "bullet_points": parsed.get("ppt_content", {}).get("bullet_points", []),
                "highlight": parsed.get("ppt_content", {}).get("highlight", "")
            },
            "speaker_notes": {
                "explanation": parsed.get("speaker_notes", {}).get("explanation", ""),
                "key_reasoning": parsed.get("speaker_notes", {}).get("key_reasoning", []),
                "interpretation_details": parsed.get("speaker_notes", {}).get("interpretation_details", "")
            },
            "raw_response": answer
        }
    except json.JSONDecodeError as e:
        logger.warning(f"JSON解析失败 {element_type}-{element_id}: {str(e)}")
        return {
            **default_result,
            "speaker_notes": {"explanation": answer[:500], "key_reasoning": [], "interpretation_details": ""},
            "raw_response": answer,
            "parse_error": str(e)
        }
    except Exception as e:
        logger.error(f"解析异常 {element_type}-{element_id}: {str(e)}")
        return {**default_result, "raw_response": answer, "parse_error": str(e)}
