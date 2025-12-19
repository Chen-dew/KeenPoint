"""NLP服务: 文档章节分段与分析"""

import re
import time
from typing import List, Dict, Any, Optional

from app.core.logger import logger
from app.services.clients.dify_workflow_client import analyze_summary, analyze_basic


class NLPService:
    """NLP服务类"""
    
    MAX_SEGMENT_LENGTH = 10000
    
    def analyze_full_document(self, parse_result: Dict[str, Any], abstract: str) -> Dict[str, Any]:
        """完整文档分析"""
        logger.info("[NLP] analyze_full_document start")
        
        basic_info = self._extract_basic_info(parse_result)
        segments = self._extract_sections(parse_result)
        sections_analysis = self._analyze_sections(segments, abstract)
        
        stats = {
            "total": len(segments),
            "analyzed": len(sections_analysis),
            "success": len([s for s in sections_analysis if not s.get("error")]),
            "failed": len([s for s in sections_analysis if s.get("error")]),
            "skipped": len(segments) - len(sections_analysis)
        }
        
        logger.info(f"[NLP] analyze_full_document done: {stats}")
        
        return {
            "basic_info": basic_info,
            "sections_analysis": sections_analysis,
            "metadata": parse_result.get("metadata", {}),
            "statistics": stats
        }
    
    def _extract_basic_info(self, parse_result: Dict[str, Any]) -> Dict[str, Any]:
        """提取文章基础信息"""
        sections = parse_result.get("sections", [])
        if not sections:
            logger.warning("[NLP] extract_basic_info: no sections")
            return {"error": "No sections"}
        
        first = sections[0]
        content = first.get("content", "")
        name = first.get("name", "")
        
        if not content:
            logger.warning("[NLP] extract_basic_info: first section empty")
            return {"error": "First section empty"}
        
        query = f"{name}\n\n{content}"
        logger.info(f"[NLP] extract_basic_info: len={len(query)}")
        
        try:
            result = analyze_basic(query=query)
            logger.info("[NLP] extract_basic_info: success")
            return result
        except Exception as e:
            logger.error(f"[NLP] extract_basic_info: {e}")
            return {"error": str(e)}
    
    def _extract_sections(self, parse_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取并拆分章节"""
        sections = parse_result.get("sections", [])
        if not sections:
            logger.warning("[NLP] extract_sections: no sections")
            return []
        
        logger.info(f"[NLP] extract_sections: {len(sections)} sections")
        segments = []
        
        for idx, section in enumerate(sections):
            name = section.get("name", f"Section {idx}")
            content = section.get("content", "")
            
            if len(content) <= self.MAX_SEGMENT_LENGTH:
                segments.append(self._make_segment(idx, name, content))
            else:
                parts = self._split_content(content)
                for part_idx, part_content in enumerate(parts, 1):
                    segments.append(self._make_segment(
                        idx, f"{name} (Part {part_idx}/{len(parts)})", 
                        part_content, is_split=True, part_index=part_idx, total_parts=len(parts)
                    ))
                logger.info(f"[NLP] section {idx} split into {len(parts)} parts")
        
        logger.info(f"[NLP] extract_sections: {len(segments)} segments")
        return segments
    
    def _make_segment(self, section_idx: int, name: str, content: str, 
                      is_split: bool = False, part_index: int = None, total_parts: int = 1) -> Dict:
        """构造片段数据"""
        seg_id = f"{section_idx}_part_{part_index}" if is_split else str(section_idx)
        return {
            "id": seg_id,
            "name": name,
            "content": content,
            "section_idx": section_idx,
            "is_split": is_split,
            "part_index": part_index,
            "total_parts": total_parts
        }
    
    def _split_content(self, content: str) -> List[str]:
        """拆分超长内容"""
        paragraphs = re.split(r'\n\s*\n', content)
        segments = []
        current = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(para) > self.MAX_SEGMENT_LENGTH:
                if current:
                    segments.append(current.strip())
                    current = ""
                segments.extend(self._split_by_sentence(para))
            elif len(current) + len(para) + 2 <= self.MAX_SEGMENT_LENGTH:
                current = f"{current}\n\n{para}" if current else para
            else:
                if current:
                    segments.append(current.strip())
                current = para
        
        if current:
            segments.append(current.strip())
        
        return segments if segments else self._split_by_length(content)
    
    def _split_by_sentence(self, text: str) -> List[str]:
        """按句子拆分"""
        parts = re.split(r'([。！？.!?]+\s*)', text)
        sentences = []
        for i in range(0, len(parts) - 1, 2):
            sentences.append(parts[i] + (parts[i + 1] if i + 1 < len(parts) else ""))
        
        segments = []
        current = ""
        for sent in sentences:
            if len(current) + len(sent) <= self.MAX_SEGMENT_LENGTH:
                current += sent
            else:
                if current:
                    segments.append(current.strip())
                current = sent
        if current:
            segments.append(current.strip())
        
        if not segments or any(len(s) > self.MAX_SEGMENT_LENGTH for s in segments):
            return self._split_by_length(text)
        return segments
    
    def _split_by_length(self, text: str) -> List[str]:
        """按长度强制拆分"""
        return [text[i:i + self.MAX_SEGMENT_LENGTH] 
                for i in range(0, len(text), self.MAX_SEGMENT_LENGTH)]
    
    def _analyze_sections(self, segments: List[Dict], abstract: str) -> List[Dict[str, Any]]:
        """分析章节片段"""
        if not segments:
            logger.warning("[NLP] analyze_sections: no segments")
            return []
        
        logger.info(f"[NLP] analyze_sections: {len(segments)} segments")
        results = []
        summaries_cache = {}
        
        for idx, seg in enumerate(segments, 1):
            seg_id = seg["id"]
            section_idx = seg["section_idx"]
            
            # 跳过第一章节和Abstract
            if section_idx == 0:
                logger.debug(f"[NLP] skip section_idx=0: {seg_id}")
                continue
            if "abstract" in seg["name"].lower() or "摘要" in seg["name"]:
                logger.debug(f"[NLP] skip abstract: {seg_id}")
                continue
            
            # 获取前序摘要
            prev_summaries = None
            if seg["is_split"] and seg["part_index"] > 1:
                prev_summaries = summaries_cache.get(section_idx)
            
            prompt = self._build_prompt(abstract, seg["name"], seg["content"], prev_summaries)
            logger.info(f"[NLP] analyzing [{idx}/{len(segments)}] {seg_id}")
            
            try:
                result = analyze_summary(user_prompt=prompt)
                analysis = {
                    "id": seg_id,
                    "section_name": result.get("section_name", seg["name"]),
                    "summary": result.get("summary", ""),
                    "key_points": result.get("key_points", [])
                }
                
                # 缓存摘要
                if seg["is_split"]:
                    summaries_cache.setdefault(section_idx, []).append({
                        "part": seg["part_index"],
                        "summary": analysis["summary"]
                    })
                
                results.append(analysis)
                logger.info(f"[NLP] analyzed {seg_id}: success")
                
            except Exception as e:
                logger.error(f"[NLP] analyzed {seg_id}: {e}")
                results.append({
                    "id": seg_id,
                    "section_name": seg["name"],
                    "summary": "",
                    "key_points": [],
                    "error": str(e)
                })
            
            if idx < len(segments):
                time.sleep(1)
        
        success = len([r for r in results if not r.get("error")])
        logger.info(f"[NLP] analyze_sections done: success={success}, failed={len(results)-success}")
        return results
    
    def _build_prompt(self, abstract: str, name: str, content: str, 
                      prev_summaries: Optional[List[Dict]] = None) -> str:
        """构建提示词"""
        prompt = f"abstract: {abstract}\n\nname: {name}"
        if prev_summaries:
            prev_text = " ".join([f"Part {s['part']}: {s['summary']}" for s in prev_summaries])
            prompt += f"\n\nprevious_parts_summary: {prev_text}"
        prompt += f"\n\ncontent: {content}"
        return prompt


# 单例
_service = NLPService()


def analyze_full_document(parse_result: Dict[str, Any], abstract: str) -> Dict[str, Any]:
    """完整文档分析"""
    return _service.analyze_full_document(parse_result, abstract)


def extract_article_basic_info(parse_result: Dict[str, Any]) -> Dict[str, Any]:
    """提取文章基础信息"""
    return _service._extract_basic_info(parse_result)


def extract_and_split_sections(parse_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """提取并拆分章节"""
    return _service._extract_sections(parse_result)
