"""大纲分析服务模块：整合文档解析、文本分析和图表分析结果"""

import json
import re
import time
from typing import List, Dict, Any, Optional
from app.core.logger import logger
from app.services.clients.dify_client import analyze_outline


class OutlineService:
    """大纲分析服务类"""
    
    def __init__(self):
        pass
    
    def build_outline_prompt(
        self,
        parse_result: Dict[str, Any],
        text_analysis: List[Dict[str, Any]],
        visual_analysis: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        构建大纲分析的输入数据
        
        Args:
            parse_result: 来自 parse_service 的解析结果
            text_analysis: 来自 nlp_service 的文本分析结果
            visual_analysis: 来自 image_service 的图表分析结果
            
        Returns:
            每个章节的大纲分析输入数据列表
        """
        sections = parse_result.get("sections", [])
        if not sections:
            logger.warning("无章节数据")
            return []
        
        logger.info(f"开始构建大纲 prompt: {len(sections)} 个章节")
        
        # 建立文本分析索引（按章节名称）
        text_analysis_map = {}
        for analysis in text_analysis:
            section_name = analysis.get("section_name", "")
            if section_name:
                text_analysis_map[section_name] = analysis
        
        # 建立视觉元素分析索引（按类型和ID）
        visual_map = {}
        for visual in visual_analysis:
            element = visual.get("element", {})
            element_type = element.get("type")
            element_id = element.get("id")
            if element_type and element_id is not None:
                key = f"{element_type}_{element_id}"
                visual_map[key] = visual.get("analysis", {})
        
        # 为每个章节构建输入
        outline_inputs = []
        
        for section in sections:
            section_name = section.get("name", "")
            section_path = section.get("path", "")
            
            # 获取文本分析结果
            text_result = text_analysis_map.get(section_name, {})
            summary = text_result.get("summary", "")
            key_points = text_result.get("key_points", [])
            
            # 获取章节中的视觉元素引用
            fig_refs = section.get("fig_refs", [])
            table_refs = section.get("table_refs", [])
            formula_refs = section.get("formula_refs", [])
            
            # 提取视觉元素的分析结果
            images_explanations = []
            for fig in fig_refs:
                fig_id = fig.get("id")
                key = f"image_{fig_id}"
                analysis = visual_map.get(key, {})
                if analysis:
                    images_explanations.append({
                        "id": fig_id,
                        "caption": fig.get("caption", ""),
                        "ppt_content": analysis.get("ppt_content", {}),
                        "speaker_notes": analysis.get("speaker_notes", {})
                    })
            
            tables_explanations = []
            for table in table_refs:
                table_id = table.get("id")
                key = f"table_{table_id}"
                analysis = visual_map.get(key, {})
                if analysis:
                    tables_explanations.append({
                        "id": table_id,
                        "caption": table.get("caption", ""),
                        "ppt_content": analysis.get("ppt_content", {}),
                        "speaker_notes": analysis.get("speaker_notes", {})
                    })
            
            equations_explanations = []
            for formula in formula_refs:
                formula_id = formula.get("id")
                key = f"equation_{formula_id}"
                analysis = visual_map.get(key, {})
                if analysis:
                    equations_explanations.append({
                        "id": formula_id,
                        "text": formula.get("text", ""),
                        "ppt_content": analysis.get("ppt_content", {}),
                        "speaker_notes": analysis.get("speaker_notes", {})
                    })
            
            # 构建该章节的输入数据
            section_input = {
                "section_name": section_name,
                "section_path": section_path,
                "summary": summary,
                "key_points": key_points,
                "refs": {
                    "images": images_explanations,
                    "equations": equations_explanations,
                    "tables": tables_explanations
                }
            }
            
            outline_inputs.append(section_input)
            logger.debug(f"构建章节 prompt: {section_name}, "
                        f"images={len(images_explanations)}, "
                        f"tables={len(tables_explanations)}, "
                        f"equations={len(equations_explanations)}")
        
        logger.info(f"构建完成: {len(outline_inputs)} 个章节")
        return outline_inputs
    
    def analyze_outline(
        self,
        outline_inputs: List[Dict[str, Any]],
        skip_abstract: bool = True
    ) -> List[Dict[str, Any]]:
        """
        分析大纲，生成PPT结构
        
        Args:
            outline_inputs: 章节输入数据列表
            skip_abstract: 是否跳过Abstract章节
            
        Returns:
            大纲分析结果列表
        """
        if not outline_inputs:
            logger.warning("无需分析的大纲输入")
            return []
        
        logger.info(f"开始大纲分析: {len(outline_inputs)} 个章节")
        
        results = []
        skipped_count = 0
        
        for idx, section_input in enumerate(outline_inputs, 1):
            section_name = section_input.get("section_name", "")
            
            # 跳过Abstract章节
            if skip_abstract:
                name_lower = section_name.lower()
                if "abstract" in name_lower or "摘要" in section_name:
                    logger.info(f"跳过Abstract章节: {section_name}")
                    skipped_count += 1
                    continue
            
            # 构建JSON prompt
            prompt = json.dumps(section_input, ensure_ascii=False, indent=2)
            
            logger.info(f"分析进度 [{idx}/{len(outline_inputs)}]: {section_name}")
            
            # 重试机制
            max_retries = 3
            retry_count = 0
            analysis_result = None
            last_error = None
            current_prompt = prompt
            
            while retry_count < max_retries:
                try:
                    answer = ""
                    for chunk in analyze_outline(query=current_prompt):
                        answer = chunk
                    
                    if answer:
                        parsed_result = self._parse_outline_response(answer, section_name)
                        
                        # 检查是否有解析错误
                        if parsed_result.get("parse_error"):
                            raise ValueError(f"JSON解析失败: {parsed_result.get('parse_error')}")
                        
                        analysis_result = parsed_result
                        break
                
                except Exception as e:
                    retry_count += 1
                    last_error = e
                    logger.warning(f"分析失败 [{section_name}] 第{retry_count}次: {str(e)}")
                    
                    if retry_count < max_retries:
                        logger.info(f"准备重新提问 Agent (尝试{retry_count + 1}/{max_retries})")
                        # 构造重新提问的prompt
                        current_prompt = f"""上一次回答的JSON格式有误，无法解析。请严格按照以下格式重新回答：

{{
  "section_name": "章节名称",
  "ppt_outline": [
    {{
      "slide_title": "幻灯片标题",
      "slide_purpose": "幻灯片目的",
      "content_points": ["要点1", "要点2"],
      "visual_refs": {{
        "images": ["image_1", "image_2"],
        "equations": ["equation_1"],
        "tables": ["table_1"]
      }}
    }}
  ]
}}

注意：
1. 必须返回有效的JSON格式
2. 不要在JSON前后添加markdown代码块标记
3. 所有字段都是必需的
4. visual_refs中的ID必须是字符串格式（如"image_1"）

原始任务：
{prompt}"""
                        wait_time = 2
                        logger.info(f"等待{wait_time}秒后重试")
                        time.sleep(wait_time)
            
            # 保存结果
            if analysis_result:
                analysis_result["section_name"] = section_name
                analysis_result["section_path"] = section_input.get("section_path", "")
                results.append(analysis_result)
                logger.info(f"分析完成: {section_name}, "
                          f"生成 {len(analysis_result.get('ppt_outline', []))} 个幻灯片")
            else:
                error_msg = str(last_error) if last_error else "未知错误"
                logger.error(f"分析失败 [{section_name}]: {error_msg}")
                results.append({
                    "section_name": section_name,
                    "section_path": section_input.get("section_path", ""),
                    "ppt_outline": [],
                    "error": error_msg
                })
            
            # 间隔请求
            if idx < len(outline_inputs):
                time.sleep(1)
        
        success_count = len([r for r in results if not r.get('error')])
        logger.info(f"大纲分析完成: 成功 {success_count}, 失败 {len(results) - success_count}, 跳过 {skipped_count}")
        return results
    
    def _parse_outline_response(self, answer: str, section_name: str) -> Dict[str, Any]:
        """
        解析大纲分析响应
        
        Args:
            answer: Dify返回的响应
            section_name: 章节名称
            
        Returns:
            解析后的大纲结果
        """
        default_result = {
            "section_name": section_name,
            "ppt_outline": []
        }
        
        try:
            if not answer:
                return default_result
            
            json_str = answer.strip()
            
            # 方法1: 查找JSON代码块
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            else:
                # 方法2: 查找JSON对象开始标记
                match = re.search(r'\{\s*"', json_str)
                if match:
                    start_idx = match.start()
                    end_idx = json_str.rfind('}')
                    if end_idx != -1 and end_idx > start_idx:
                        json_str = json_str[start_idx:end_idx + 1].strip()
                        logger.debug(f"提取JSON [{section_name}]: 位置 {start_idx}-{end_idx}, 长度 {len(json_str)}")
                else:
                    # 降级方案
                    start_idx = json_str.find('{')
                    if start_idx != -1:
                        end_idx = json_str.rfind('}')
                        if end_idx != -1 and end_idx > start_idx:
                            json_str = json_str[start_idx:end_idx + 1].strip()
                            logger.debug(f"提取JSON(降级) [{section_name}]: 位置 {start_idx}-{end_idx}, 长度 {len(json_str)}")
            
            parsed = json.loads(json_str, strict=False)
            return {
                "section_name": parsed.get("section_name", section_name),
                "ppt_outline": parsed.get("ppt_outline", []),
                "raw_response": answer
            }
        
        except json.JSONDecodeError as e:
            # 尝试修复常见JSON错误
            try:
                # 步骤1: 修复无效转义字符
                fixed_json = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', json_str)
                
                # 步骤2: 修复常见格式错误
                fixed_json = re.sub(r'"\]\s*\n\s*\}', '"\n  }', fixed_json)
                
                parsed = json.loads(fixed_json, strict=False)
                logger.debug(f"修复JSON格式错误后成功解析 [{section_name}]")
                return {
                    "section_name": parsed.get("section_name", section_name),
                    "ppt_outline": parsed.get("ppt_outline", []),
                    "raw_response": answer
                }
            except Exception as e2:
                logger.error(f"JSON解析失败 [{section_name}]: {str(e)}")
                logger.debug(f"尝试解析的JSON字符串 (前200字符): {json_str[:200]}")
                return {
                    **default_result,
                    "raw_response": answer,
                    "parse_error": str(e)
                }
        
        except Exception as e:
            logger.error(f"解析异常 [{section_name}]: {str(e)}")
            return {
                **default_result,
                "raw_response": answer,
                "parse_error": str(e)
            }


# 全局实例
outline_service = OutlineService()


def build_outline_prompt(
    parse_result: Dict[str, Any],
    text_analysis: List[Dict[str, Any]],
    visual_analysis: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """构建大纲分析输入数据"""
    return outline_service.build_outline_prompt(parse_result, text_analysis, visual_analysis)


def analyze_outline_with_dify(
    outline_inputs: List[Dict[str, Any]],
    skip_abstract: bool = True
) -> List[Dict[str, Any]]:
    """分析大纲生成PPT结构"""
    return outline_service.analyze_outline(outline_inputs, skip_abstract)

