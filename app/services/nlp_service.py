"""NLP服务模块：文档章节分段与分析"""

from typing import List, Dict, Any, Optional
from app.core.logger import logger
from app.services.clients.dify_workflow_client import analyze_summary
import re
import time


class NLPService:
    """NLP服务类"""
    
    def __init__(self):
        self.max_segment_length = 10000
    
    def extract_and_split_sections(self, parse_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取章节并拆分超长内容"""
        sections = parse_result.get("sections", [])
        if not sections:
            logger.warning("无 sections 数据")
            return []
        
        logger.info(f"开始处理章节，共 {len(sections)} 个")
        segments = []
        
        for section_idx, section in enumerate(sections):
            name = section.get("name", f"Section {section_idx}")
            content = section.get("content", "")
            content_len = len(content)
            
            if content_len <= self.max_segment_length:
                segments.append({
                    "id": str(section_idx),
                    "name": name,
                    "content": content,
                    "original_section_index": section_idx,
                    "is_split": False,
                    "part_index": None,
                    "total_parts": 1
                })
            else:
                split_segments = self._split_long_content(content, name, section_idx)
                segments.extend(split_segments)
                logger.info(f"章节 {section_idx} '{name}' 拆分为 {len(split_segments)} 部分，原长度: {content_len}")
        
        logger.info(f"处理完成，生成 {len(segments)} 个片段")
        return segments
    
    def _split_long_content(self, content: str, section_name: str, section_index: int) -> List[Dict[str, Any]]:
        """拆分超长内容，优先按段落边界拆分"""
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
        """按句子边界拆分文本"""
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
        """强制按固定长度拆分文本"""
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
        """分析章节片段，拆分章节后续部分将接收前面部分的摘要作为上下文"""
        if not segments:
            logger.warning("无需分析的片段")
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
                    logger.info(f"跳过Abstract [{segment_id}]")
                    skipped_count += 1
                    continue
            
            previous_summaries = None
            if is_split and part_index and part_index > 1:
                if original_section_index in split_section_summaries:
                    previous_summaries = split_section_summaries[original_section_index]
            
            user_prompt = self._build_user_prompt(abstract, segment_name, segment_content, previous_summaries)
            logger.info(f"分析进度 [{idx}/{len(segments)}] ID: {segment_id}, 长度: {len(segment_content)}")
            
            analysis_result = None
            error_msg = None
            
            try:
                # 调用 workflow 分析（阻塞模式，直接返回结构化数据）
                result = analyze_summary(user_prompt=user_prompt)
                
                if result:
                    # 阻塞模式直接返回字典，简化处理
                    analysis_result = {
                        "section_name": result.get("section_name", segment_name),
                        "summary": result.get("summary", ""),
                        "key_points": result.get("key_points", [])
                    }
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"分析失败 [{segment_id}]: {error_msg}")
            
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
                logger.info(f"分析完成 [{segment_id}]")
            else:
                err = error_msg or "未知错误"
                logger.error(f"分析失败 [{segment_id}]: {err}")
                results.append({
                    "id": segment_id,
                    "section_name": segment_name,
                    "summary": f"分析失败: {err}",
                    "key_points": [],
                    "error": err
                })
            
            if idx < len(segments):
                time.sleep(1)
        
        success_count = len([r for r in results if not r.get('error')])
        logger.info(f"分析完成，成功: {success_count}, 失败: {len(results) - success_count}, 跳过: {skipped_count}")
        return results
    
    def _build_user_prompt(
        self, 
        abstract: str, 
        section_name: str, 
        section_content: str,
        previous_summaries: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """构建分析提示词"""
        prompt = f"""abstract: {abstract}

name: {section_name}"""

        if previous_summaries:
            previous_text = " ".join([f"Part {s['part_index']}: {s['summary']}" for s in previous_summaries])
            prompt += f"""

previous_parts_summary: {previous_text}"""
        
        prompt += f"""

content: {section_content}"""
        
        return prompt


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
