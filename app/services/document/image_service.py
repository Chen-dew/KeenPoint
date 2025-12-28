"""图表公式提取与分析服务"""

import re
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.logger import logger
from app.services.clients.dify_workflow_client import analyze_images, upload_files


def _get_context(content: str, elem_id: int, elem_type: str, window: int = 200) -> str:
    """提取元素上下文"""
    patterns = {
        "image": rf'(?:Figure|Fig\.|图)\s*{elem_id}\b',
        "table": rf'(?:Table|Tab\.|表)\s*{elem_id}\b'
    }
    
    pattern = patterns.get(elem_type)
    if not pattern:
        return ""
    
    m = re.search(pattern, content, re.IGNORECASE)
    if not m:
        return ""
    
    start = max(0, m.start() - window)
    end = min(len(content), m.start() + window)
    ctx = content[start:end].strip()
    
    return ("..." if start > 0 else "") + ctx + ("..." if end < len(content) else "")


def extract_elements(parse_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从解析结果提取图表公式"""
    sections = parse_result.get("sections", [])
    
    # 获取摘要
    abstract = ""
    for sec in sections:
        if sec.get("name", "").lower() in ["abstract", "摘要"]:
            abstract = sec.get("content", "")
            break
    
    results = []
    for sec in sections:
        name = sec.get("name", "")
        content = sec.get("content", "")
        path = sec.get("path", "")
        
        # 图片
        for fig in sec.get("fig_refs", []):
            results.append({
                "abstract": abstract,
                "element": {
                    "type": "image", "id": fig.get("id"),
                    "img_path": fig.get("img_path", ""),
                    "caption": fig.get("caption", "")
                },
                "local_context": _get_context(content, fig.get("id"), "image"),
                "section_content": content,
                "section_name": name,
                "section_path": path
            })
        
        # 表格
        for tbl in sec.get("table_refs", []):
            results.append({
                "abstract": abstract,
                "element": {
                    "type": "table", "id": tbl.get("id"),
                    "img_path": tbl.get("img_path", ""),
                    "caption": tbl.get("caption", ""),
                    "body": tbl.get("body", "")
                },
                "local_context": _get_context(content, tbl.get("id"), "table"),
                "section_content": content,
                "section_name": name,
                "section_path": path
            })
        
        # 公式
        for eq in sec.get("formula_refs", []):
            results.append({
                "abstract": abstract,
                "element": {
                    "type": "equation", "id": eq.get("id"),
                    "img_path": eq.get("img_path", ""),
                    "text": eq.get("text", ""),
                    "text_format": eq.get("text_format", "latex")
                },
                "local_context": "",
                "section_content": content,
                "section_name": name,
                "section_path": path
            })
    
    logger.info(f"[IMAGE] extracted {len(results)} elements")
    return results


def analyze_elements(elements: List[Dict[str, Any]], base_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """分析图表公式"""
    if not elements:
        logger.warning("[IMAGE] no elements")
        return []
    
    logger.info(f"[IMAGE] analyzing {len(elements)} elements")
    
    # 收集需要上传的图片
    to_upload = []
    for elem in elements:
        img_path = elem.get("element", {}).get("img_path", "")
        if not img_path:
            continue
        full = (base_path / img_path) if base_path else Path(img_path)
        if full.exists():
            to_upload.append(str(full))
    
    # 批量上传
    file_ids = {}
    if to_upload:
        logger.info(f"[IMAGE] uploading {len(to_upload)} files")
        try:
            results = upload_files(to_upload, continue_on_error=True)
            for r in results:
                if r.get('success'):
                    file_ids[r['file_path']] = r['file_id']
        except Exception as e:
            logger.error(f"[IMAGE] upload error: {e}")
    
    # 逐个分析
    results = []
    for idx, elem in enumerate(elements, 1):
        info = elem.get("element", {})
        etype = info.get("type")
        eid = info.get("id")
        img_path = info.get("img_path", "")
        
        logger.info(f"[IMAGE] [{idx}/{len(elements)}] {etype}-{eid}")
        
        # 获取文件ID
        file_id = None
        if img_path:
            full = (base_path / img_path) if base_path else Path(img_path)
            file_id = file_ids.get(str(full))
        
        # 构建prompt
        info_copy = info.copy()
        info_copy['img_path'] = file_id or ""
        prompt = json.dumps({
            "abstract": elem.get("abstract", ""),
            "element": info_copy,
            "local_context": elem.get("local_context", ""),
            "section_content": elem.get("section_content", "")
        }, ensure_ascii=False)
        
        # 调用分析
        try:
            # equation类型通常没有图片，允许空文件列表
            allow_empty = (etype == "equation" and not file_id)
            
            answer = analyze_images(
                user_prompt=prompt,
                file_ids=[file_id] if file_id else [],
                llm_id=2,
                auto_upload=False,
                allow_empty_files=allow_empty
            )
            
            if answer:
                results.append({
                    **elem,
                    "analysis": {
                        "element_id": answer.get("element_id", eid),
                        "element_type": answer.get("element_type", etype),
                        "analysis_text": answer.get("analysis_text", "")
                    }
                })
                logger.info(f"[IMAGE] {etype}-{eid}: success")
            else:
                results.append({**elem, "analysis": None, "error": "Empty response"})
                
        except Exception as e:
            logger.error(f"[IMAGE] {etype}-{eid}: {e}")
            results.append({**elem, "analysis": None, "error": str(e)})
        
        if idx < len(elements):
            time.sleep(1)
    
    success = len([r for r in results if r.get("analysis")])
    logger.info(f"[IMAGE] done: success={success}, failed={len(results)-success}")
    return results

