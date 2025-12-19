"""大纲分析服务"""

import json
import re
import time
from typing import List, Dict, Any

from app.core.logger import logger
from app.services.clients.dify_workflow_client import run_outline


def build_outline(parse_result: Dict[str, Any], text_analysis: List[Dict[str, Any]], 
                  visual_analysis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """构建大纲分析输入"""
    sections = parse_result.get("sections", [])
    if not sections:
        logger.warning("[OUTLINE] no sections")
        return []
    
    logger.info(f"[OUTLINE] building: {len(sections)} sections")
    
    # 索引文本分析
    text_map = {a.get("section_name", ""): a for a in text_analysis}
    
    # 索引视觉分析
    visual_map = {}
    for v in visual_analysis:
        elem = v.get("element", {})
        key = f"{elem.get('type')}_{elem.get('id')}"
        visual_map[key] = v.get("analysis", {})
    
    results = []
    for sec in sections:
        name = sec.get("name", "")
        text = text_map.get(name, {})
        
        # 收集视觉元素
        images = []
        for fig in sec.get("fig_refs", []):
            key = f"image_{fig.get('id')}"
            if key in visual_map:
                images.append({
                    "id": fig.get("id"),
                    "caption": fig.get("caption", ""),
                    "ppt_content": visual_map[key].get("ppt_content", {}),
                    "speaker_notes": visual_map[key].get("speaker_notes", {})
                })
        
        tables = []
        for tbl in sec.get("table_refs", []):
            key = f"table_{tbl.get('id')}"
            if key in visual_map:
                tables.append({
                    "id": tbl.get("id"),
                    "caption": tbl.get("caption", ""),
                    "ppt_content": visual_map[key].get("ppt_content", {}),
                    "speaker_notes": visual_map[key].get("speaker_notes", {})
                })
        
        equations = []
        for eq in sec.get("formula_refs", []):
            key = f"equation_{eq.get('id')}"
            if key in visual_map:
                equations.append({
                    "id": eq.get("id"),
                    "text": eq.get("text", ""),
                    "ppt_content": visual_map[key].get("ppt_content", {}),
                    "speaker_notes": visual_map[key].get("speaker_notes", {})
                })
        
        results.append({
            "section_name": name,
            "section_path": sec.get("path", ""),
            "summary": text.get("summary", ""),
            "key_points": text.get("key_points", []),
            "refs": {"images": images, "equations": equations, "tables": tables}
        })
    
    logger.info(f"[OUTLINE] built: {len(results)} sections")
    return results


def analyze_outline(outline_inputs: List[Dict[str, Any]], skip_abstract: bool = True) -> List[Dict[str, Any]]:
    """分析大纲生成PPT结构"""
    if not outline_inputs:
        logger.warning("[OUTLINE] no inputs")
        return []
    
    logger.info(f"[OUTLINE] analyzing: {len(outline_inputs)} sections")
    
    results = []
    skipped = 0
    
    for idx, inp in enumerate(outline_inputs, 1):
        name = inp.get("section_name", "")
        
        # 跳过摘要
        if skip_abstract and ("abstract" in name.lower() or "摘要" in name):
            logger.info(f"[OUTLINE] skip abstract: {name}")
            skipped += 1
            continue
        
        logger.info(f"[OUTLINE] [{idx}/{len(outline_inputs)}] {name}")
        prompt = json.dumps(inp, ensure_ascii=False, indent=2)
        
        # 重试机制
        result = None
        for retry in range(3):
            try:
                answer = ""
                for chunk in run_outline(query=prompt):
                    answer = chunk
                
                if answer:
                    result = _parse_response(answer, name)
                    if not result.get("parse_error"):
                        break
                    raise ValueError(result.get("parse_error"))
                    
            except Exception as e:
                logger.warning(f"[OUTLINE] retry {retry+1}/3: {e}")
                if retry < 2:
                    time.sleep(2)
        
        if result and not result.get("parse_error"):
            result["section_path"] = inp.get("section_path", "")
            results.append(result)
            logger.info(f"[OUTLINE] {name}: {len(result.get('ppt_outline', []))} slides")
        else:
            results.append({
                "section_name": name,
                "section_path": inp.get("section_path", ""),
                "ppt_outline": [],
                "error": result.get("parse_error") if result else "Unknown error"
            })
            logger.error(f"[OUTLINE] {name}: failed")
        
        if idx < len(outline_inputs):
            time.sleep(1)
    
    success = len([r for r in results if not r.get('error')])
    logger.info(f"[OUTLINE] done: success={success}, failed={len(results)-success}, skipped={skipped}")
    return results


def _parse_response(answer: str, section_name: str) -> Dict[str, Any]:
    """解析大纲响应"""
    default = {"section_name": section_name, "ppt_outline": []}
    
    if not answer:
        return default
    
    try:
        text = answer.strip()
        
        # 提取JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        else:
            m = re.search(r'\{\s*"', text)
            if m:
                start = m.start()
                end = text.rfind('}')
                if end > start:
                    text = text[start:end+1]
        
        data = json.loads(text, strict=False)
        return {
            "section_name": data.get("section_name", section_name),
            "ppt_outline": data.get("ppt_outline", []),
            "raw_response": answer
        }
        
    except json.JSONDecodeError as e:
        # 尝试修复
        try:
            fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)
            data = json.loads(fixed, strict=False)
            return {
                "section_name": data.get("section_name", section_name),
                "ppt_outline": data.get("ppt_outline", []),
                "raw_response": answer
            }
        except:
            return {**default, "raw_response": answer, "parse_error": str(e)}
    except Exception as e:
        return {**default, "raw_response": answer, "parse_error": str(e)}

