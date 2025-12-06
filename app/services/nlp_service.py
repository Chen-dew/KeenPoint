"""
NLP服务模块
处理论文文档的NLP分析任务，包括章节分段、摘要生成等
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from app.core.logger import logger
from app.services.clients.nlp_client import nlp_client
import re
import json
import time


class NLPService:
    """NLP服务类"""
    
    def __init__(self):
        self.max_segment_length = 10000
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """加载系统提示词"""
        try:
            prompt_path = Path(__file__).parent / "prompt" / "TextUnderstandingAgent.txt"
            if prompt_path.exists():
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    logger.info(f"系统提示词加载成功，长度: {len(content)} 字符")
                    return content
            else:
                logger.warning(f"系统提示词文件不存在: {prompt_path}")
                return ""
        except Exception as e:
            logger.error(f"加载系统提示词失败: {e}")
            return ""
    
    def extract_and_split_sections(self, parse_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从 parse_service 返回结果中提取 sections，并对超长内容进行拆分
        
        Args:
            parse_result: parse_service.parse_markdown_file() 的返回结果
                格式: {
                    "sections": [...],
                    "figures": [...],
                    "formulas": [...],
                    "tables": [...],
                    "metadata": {...}
                }
        
        Returns:
            List[Dict]: 分段后的数组，每个元素包含:
                - id: 唯一标识符，格式 "section_index" 或 "section_index_part_N"
                - name: 章节名称
                - content: 章节内容（拆分后的片段）
                - original_section_index: 原始章节索引
                - is_split: 是否为拆分片段
                - part_index: 如果拆分，表示第几部分（从1开始）
                - total_parts: 如果拆分，总共几部分
        
        Example:
            >>> result = parse_markdown_file("paper.md")
            >>> segments = nlp_service.extract_and_split_sections(result)
            >>> # 输出示例：
            >>> [
            >>>     {"id": "0", "name": "Introduction", "content": "...", ...},
            >>>     {"id": "1_part_1", "name": "Methods (Part 1/3)", "content": "...", ...},
            >>>     {"id": "1_part_2", "name": "Methods (Part 2/3)", "content": "...", ...},
            >>>     {"id": "1_part_3", "name": "Methods (Part 3/3)", "content": "...", ...},
            >>> ]
        """
        sections = parse_result.get("sections", [])
        
        if not sections:
            logger.warning("parse_result 中没有 sections 数据")
            return []
        
        logger.info(f"开始处理 {len(sections)} 个章节")
        
        segments = []
        
        for section_idx, section in enumerate(sections):
            name = section.get("name", f"Section {section_idx}")
            content = section.get("content", "")
            word_count = len(content)
            
            # 如果内容未超过最大长度，直接添加
            if word_count <= self.max_segment_length:
                segments.append({
                    "id": str(section_idx),
                    "name": name,
                    "content": content,
                    "original_section_index": section_idx,
                    "is_split": False,
                    "part_index": None,
                    "total_parts": 1
                })
                logger.debug(f"章节 {section_idx} '{name}': {word_count} 字符，无需拆分")
            else:
                # 需要拆分
                split_segments = self._split_long_content(
                    content=content,
                    section_name=name,
                    section_index=section_idx
                )
                segments.extend(split_segments)
                logger.info(f"章节 {section_idx} '{name}': {word_count} 字符，拆分为 {len(split_segments)} 部分")
        
        logger.info(f"处理完成，共生成 {len(segments)} 个片段")
        return segments
    
    def _split_long_content(self, content: str, section_name: str, section_index: int) -> List[Dict[str, Any]]:
        """
        拆分超长内容为多个片段
        
        优先在段落边界拆分，如果单个段落过长则在句子边界拆分
        
        Args:
            content: 章节内容
            section_name: 章节名称
            section_index: 章节索引
        
        Returns:
            List[Dict]: 拆分后的片段列表
        """
        # 先按段落拆分（连续两个换行符）
        paragraphs = re.split(r'\n\s*\n', content)
        
        segments = []
        current_segment = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 如果当前段落本身就超长，需要在句子边界拆分
            if len(paragraph) > self.max_segment_length:
                # 先保存已累积的内容
                if current_segment:
                    segments.append(current_segment.strip())
                    current_segment = ""
                
                # 拆分超长段落
                sub_segments = self._split_by_sentences(paragraph)
                segments.extend(sub_segments)
            else:
                # 检查加入当前段落后是否超长
                if len(current_segment) + len(paragraph) + 2 <= self.max_segment_length:
                    # 未超长，累加
                    if current_segment:
                        current_segment += "\n\n" + paragraph
                    else:
                        current_segment = paragraph
                else:
                    # 超长，保存当前累积内容，开始新片段
                    if current_segment:
                        segments.append(current_segment.strip())
                    current_segment = paragraph
        
        # 添加最后剩余的内容
        if current_segment:
            segments.append(current_segment.strip())
        
        # 如果没有成功拆分（整个内容没有段落分隔），强制按长度拆分
        if not segments:
            segments = self._split_by_length(content)
        
        # 构建返回结果
        total_parts = len(segments)
        result = []
        
        for part_idx, segment_content in enumerate(segments, 1):
            result.append({
                "id": f"{section_index}_part_{part_idx}",
                "name": f"{section_name} (Part {part_idx}/{total_parts})",
                "content": segment_content,
                "original_section_index": section_index,
                "is_split": True,
                "part_index": part_idx,
                "total_parts": total_parts
            })
        
        return result
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """
        按句子边界拆分文本
        
        支持中英文句子分隔符：。！？.!?
        """
        # 句子分隔符（中英文）
        sentence_pattern = r'([。！？\.!?]+[\s]*)'
        sentences = re.split(sentence_pattern, text)
        
        # 重新组合句子和分隔符
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                combined_sentences.append(sentences[i] + sentences[i + 1])
            else:
                combined_sentences.append(sentences[i])
        
        # 按最大长度组合句子
        segments = []
        current_segment = ""
        
        for sentence in combined_sentences:
            if len(current_segment) + len(sentence) <= self.max_segment_length:
                current_segment += sentence
            else:
                if current_segment:
                    segments.append(current_segment.strip())
                current_segment = sentence
        
        if current_segment:
            segments.append(current_segment.strip())
        
        # 如果仍然无法拆分（单个句子超长），强制按长度拆分
        if not segments or any(len(seg) > self.max_segment_length for seg in segments):
            return self._split_by_length(text)
        
        return segments
    
    def _split_by_length(self, text: str) -> List[str]:
        """
        强制按固定长度拆分文本（最后手段）
        """
        segments = []
        start = 0
        
        while start < len(text):
            end = start + self.max_segment_length
            segments.append(text[start:end])
            start = end
        
        return segments
    
    def analyze_segments_with_abstract(
        self, 
        segments: List[Dict[str, Any]], 
        abstract: str,
        skip_abstract_section: bool = True
    ) -> List[Dict[str, Any]]:
        """分析章节片段，拆分章节的后续部分将接收前面部分的摘要作为上下文"""
        if not segments:
            logger.warning("没有需要分析的片段")
            return []
        
        if not self.system_prompt:
            logger.error("系统提示词未加载，无法进行分析")
            return []
        
        logger.info(f"开始分析，片段数: {len(segments)}, Abstract长度: {len(abstract)}")
        
        results = []
        skipped_count = 0
        split_section_summaries = {}
        
        for idx, segment in enumerate(segments, 1):
            segment_id = segment.get("id", str(idx))
            segment_name = segment.get("name", "Unknown Section")
            segment_content = segment.get("content", "")
            is_split = segment.get("is_split", False)
            original_section_index = segment.get("original_section_index")
            part_index = segment.get("part_index")
            
            if skip_abstract_section:
                name_lower = segment_name.lower()
                if "abstract" in name_lower or "摘要" in segment_name:
                    logger.info(f"跳过Abstract章节: {segment_id}")
                    skipped_count += 1
                    continue
            
            previous_summaries = None
            if is_split and part_index and part_index > 1:
                if original_section_index in split_section_summaries:
                    previous_summaries = split_section_summaries[original_section_index]
                    logger.info(f"使用前置摘要: {segment_id}, 前置部分数: {len(previous_summaries)}")
            
            user_prompt = self._build_user_prompt(abstract, segment_name, segment_content, previous_summaries)
            logger.info(f"分析进度: [{idx}/{len(segments)}], ID: {segment_id}")
            
            max_retries = 3
            retry_count = 0
            analysis_result = None
            last_error = None
            
            while retry_count < max_retries:
                try:
                    nlp_response = nlp_client.chat_sync(
                        prompt=user_prompt,
                        system_prompt=self.system_prompt
                    )
                    analysis_result = self._parse_nlp_response(nlp_response, segment_id, segment_name)
                    break
                except Exception as e:
                    retry_count += 1
                    last_error = e
                    error_msg = str(e)
                    
                    if "peer closed connection" in error_msg or "incomplete chunked read" in error_msg:
                        logger.warning(f"网络错误，重试: {retry_count}/{max_retries}, ID: {segment_id}")
                        if retry_count < max_retries:
                            wait_time = retry_count * 2
                            logger.info(f"等待重试: {wait_time}秒")
                            time.sleep(wait_time)
                            continue
                    else:
                        logger.error(f"分析失败: {segment_id}, 错误: {error_msg}")
                        break
            
            if analysis_result:
                analysis_result["id"] = segment_id
                
                if is_split and original_section_index is not None:
                    if original_section_index not in split_section_summaries:
                        split_section_summaries[original_section_index] = []
                    split_section_summaries[original_section_index].append({
                        "part_index": part_index,
                        "summary": analysis_result.get("summary", "")
                    })
                    
                    if previous_summaries:
                        analysis_result["previous_part_summary"] = " ".join([s["summary"] for s in previous_summaries])
                
                results.append(analysis_result)
                logger.info(f"分析完成: {segment_id}")
            else:
                error_msg = str(last_error) if last_error else "未知错误"
                logger.error(f"分析失败，已重试{max_retries}次: {segment_id}, 错误: {error_msg}")
                results.append({
                    "id": segment_id,
                    "section_name": segment_name,
                    "summary": f"分析失败，已重试{max_retries}次: {error_msg}",
                    "key_points": [],
                    "error": error_msg,
                    "retry_count": retry_count
                })
        
        success_count = len([r for r in results if not r.get('error')])
        failure_count = len([r for r in results if r.get('error')])
        logger.info(f"分析完成，成功: {success_count}, 失败: {failure_count}, 跳过: {skipped_count}")
        return results
    
    def _build_user_prompt(
        self, 
        abstract: str, 
        section_name: str, 
        section_content: str,
        previous_summaries: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """构建用户提示词"""
        prompt = f"""abstract: {abstract}

name: {section_name}"""

        if previous_summaries:
            previous_text = " ".join([f"Part {s['part_index']}: {s['summary']}" for s in previous_summaries])
            prompt += f"""

previous_parts_summary: {previous_text}"""
        
        prompt += f"""

content: {section_content}"""
        
        return prompt
    
    def _parse_nlp_response(self, nlp_response: Dict[str, Any], segment_id: str, segment_name: str) -> Dict[str, Any]:
        """解析NLP响应"""
        try:
            answer = nlp_response.get("answer", "")
            if not answer:
                logger.warning(f"响应为空: {segment_id}")
                return {"section_name": segment_name, "summary": "", "key_points": []}
            
            json_str = answer
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(json_str)
            result = {
                "section_name": parsed.get("section_name", segment_name),
                "summary": parsed.get("summary", ""),
                "key_points": parsed.get("key_points", [])
            }
            
            usage = nlp_response.get("usage", {})
            if usage:
                logger.debug(f"Token使用: {segment_id}, {usage}")
            
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {segment_id}, 错误: {e}")
            return {"section_name": segment_name, "summary": answer, "key_points": []}
        except Exception as e:
            logger.error(f"解析异常: {segment_id}, 错误: {e}")
            return {"section_name": segment_name, "summary": "", "key_points": []}


nlp_service = NLPService()


def extract_and_split_sections(parse_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """提取并拆分章节"""
    return nlp_service.extract_and_split_sections(parse_result)


def analyze_segments_with_abstract(
    segments: List[Dict[str, Any]], 
    abstract: str,
    skip_abstract_section: bool = True
) -> List[Dict[str, Any]]:
    """分析章节片段"""
    return nlp_service.analyze_segments_with_abstract(segments, abstract, skip_abstract_section)
