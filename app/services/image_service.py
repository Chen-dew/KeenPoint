"""图表公式提取与分析服务"""

import re
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from app.core.logger import logger
from app.services.clients.dify_workflow_client import analyze_images, upload_files


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
    """使用 Dify 分析图表公式（支持批量上传优化）"""
    if not elements:
        logger.warning("无元素需分析")
        return []
    
    logger.info(f"开始分析: {len(elements)} 个元素")
    
    # 第一步：收集所有需要上传的图片
    elements_to_upload = []
    upload_paths = []
    element_map = {}  # 用于映射上传结果
    
    for idx, elem_data in enumerate(elements):
        element = elem_data.get("element", {})
        element_type = element.get("type")
        element_id = element.get("id")
        img_path = element.get("img_path", "")
        
        if not img_path:
            logger.debug(f"{element_type}-{element_id}: 无图片路径，跳过")
            continue
        
        full_img_path = (base_path / img_path) if base_path else Path(img_path)
        if not full_img_path.exists():
            logger.warning(f"{element_type}-{element_id}: 图片不存在 {full_img_path}")
            continue
        
        elements_to_upload.append((idx, elem_data, full_img_path))
        upload_paths.append(full_img_path)
        element_map[str(full_img_path)] = (idx, elem_data)
    
    # 第二步：批量上传所有图片
    file_id_map = {}
    if upload_paths:
        logger.info(f"批量上传 {len(upload_paths)} 个图片")
        try:
            upload_results = upload_files(upload_paths, continue_on_error=True)
            
            for result in upload_results:
                if result.get('success'):
                    file_id_map[result['file_path']] = result['file_id']
                    logger.debug(f"上传成功: {Path(result['file_path']).name}")
                else:
                    logger.warning(f"上传失败: {Path(result['file_path']).name}")
        except Exception as e:
            logger.error(f"批量上传异常: {str(e)}")
    
    # 第三步：逐个分析元素
    results = []
    
    for idx, elem_data in enumerate(elements, 1):
        element = elem_data.get("element", {})
        element_type = element.get("type")
        element_id = element.get("id")
        img_path = element.get("img_path", "")
        
        logger.debug(f"[{idx}/{len(elements)}] {element_type}-{element_id}")
        
        # 验证图片路径
        if not img_path:
            # 路径为空，使用空文件ID进行分析（某些元素如公式可能没有图片）
            uploaded_file_id = None
        else:
            full_img_path = (base_path / img_path) if base_path else Path(img_path)
            if not full_img_path.exists():
                results.append({**elem_data, "analysis": None, "error": "图片不存在"})
                continue
            
            # 获取上传的文件ID
            uploaded_file_id = file_id_map.get(str(full_img_path))
            if not uploaded_file_id:
                results.append({**elem_data, "analysis": None, "error": "文件上传失败"})
                continue
        
        # 构建提示词
        element_with_id = element.copy()
        element_with_id['img_path'] = uploaded_file_id or ""
        
        prompt = json.dumps({
            "abstract": elem_data.get("abstract", ""),
            "element": element_with_id,
            "local_context": elem_data.get("local_context", ""),
            "section_content": elem_data.get("section_content", "")
        }, ensure_ascii=False, indent=2)
        
        # 分析（阻塞模式直接返回结构化数据）
        analysis_result = None
        error_msg = None
        
        try:
            # 如果有文件ID则传递，否则传递空列表
            file_ids_param = [uploaded_file_id] if uploaded_file_id else None
            
            # 使用 workflow analyze_images，阻塞模式直接返回结果
            answer = analyze_images(
                user_prompt=prompt,
                file_ids=file_ids_param,
                llm_id=2,
                auto_upload=False
            )
            
            # 打印阻塞模式返回的原始结果
            logger.info(f"=== 阻塞模式返回结果 ({element_type}-{element_id}) ===")
            logger.info(f"结果类型: {type(answer).__name__}")
            logger.info(f"结果内容: {json.dumps(answer, ensure_ascii=False, indent=2) if isinstance(answer, dict) else answer}")
            logger.info("=" * 60)
            
            if answer:
                # 阻塞模式直接返回字典，简化处理
                analysis_result = {
                    "element_id": answer.get("element_id", element_id),
                    "element_type": answer.get("element_type", element_type),
                    "ppt_content": answer.get("ppt_content", {"title": "", "bullet_points": [], "highlight": ""}),
                    "speaker_notes": answer.get("speaker_notes", {"explanation": "", "key_reasoning": [], "interpretation_details": ""}),
                    "raw_response": answer
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"分析失败 ({element_type}-{element_id}): {error_msg}")
        
        # 保存结果
        if analysis_result:
            results.append({**elem_data, "prompt": prompt, "analysis": analysis_result, "error": None})
            logger.debug(f"分析完成: {element_type}-{element_id}")
        else:
            err = error_msg or "未知错误"
            results.append({**elem_data, "prompt": prompt, "analysis": None, "error": err})
            logger.error(f"分析失败: {element_type}-{element_id}")
        
        if idx < len(elements):
            time.sleep(1)
    
    success = len([r for r in results if r.get("analysis")])
    logger.info(f"分析完成: 成功 {success}, 失败 {len(results) - success}")
    return results

