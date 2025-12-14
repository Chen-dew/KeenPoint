"""
Markdown 文档解析服务
```json
{
  "name": "4.2.1 Results on CIFAR-10",
  "level": 3,
  "path": "4. Experiments > 4.2. Results and Analysis > 4.2.1 Results on CIFAR-10",
  "content": "章节的文本内容（不含标题行）",
  "word_count": 1523,
  "direct_char_count": 10632,
  "total_char_count": 10632,
  "fig_refs": [1, 2],
  "table_refs": [1, 2, 3],
  "formula_refs": [4, 5]
}
```

字段说明：
- `name`: 完整标题（含数字编号）
- `level`: 层级（基于数字编号，如 4.2.1 为 level 3）
- `path`: 完整路径（从根到当前节点）
- `content`: 章节文本内容
- `word_count`: 字数（中文按字符，英文按单词）
- `direct_char_count`: 当前章节字符数
- `total_char_count`: 包含所有子章节的总字符数
- `fig_refs`: 章节中引用的图片ID数组
- `table_refs`: 章节中引用的表格ID数组
- `formula_refs`: 章节中引用的公式ID数组
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.core.logger import logger


class MarkdownParser:
    """Markdown 文档解析器"""
    
    def __init__(self):
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.image_pattern = re.compile(r'!\[([^\]]*)\]\(([^\s\)]+)(?:\s+"([^"]*)")?\)')
        self.number_pattern = re.compile(r'^(\d+(?:\.\d+)*)\.?\s+(.*)$')
        self.formula_block_pattern = re.compile(r'\$\$([^\$]+?)\$\$', re.DOTALL)
        self.table_pattern = re.compile(r'<table[^>]*>(.*?)</table>', re.DOTALL | re.IGNORECASE)
    
    def _extract_from_json(self, json_path: Path) -> Dict[str, List[Dict]]:
        if not json_path.exists():
            logger.warning(f"JSON文件不存在: {json_path}")
            return {"images": [], "tables": [], "equations": []}
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                content_list = json.load(f)
            
            images, tables, equations = [], [], []
            image_id = table_id = equation_id = 1
            
            for item in content_list:
                item_type = item.get("type")
                
                if item_type == "image":
                    caption = " ".join(item.get("image_caption", []))
                    images.append({
                        "type": "image",
                        "id": image_id,
                        "img_path": item.get("img_path", ""),
                        "caption": caption
                    })
                    image_id += 1
                
                elif item_type == "table":
                    caption = " ".join(item.get("table_caption", []))
                    tables.append({
                        "type": "table",
                        "id": table_id,
                        "img_path": item.get("img_path", ""),
                        "caption": caption,
                        "body": item.get("table_body", "")
                    })
                    table_id += 1
                
                elif item_type == "equation":
                    equations.append({
                        "type": "equation",
                        "id": equation_id,
                        "img_path": item.get("img_path", ""),
                        "text": item.get("text", ""),
                        "text_format": item.get("text_format", "latex")
                    })
                    equation_id += 1
            
            logger.info(f"JSON提取完成: images={len(images)}, tables={len(tables)}, equations={len(equations)}")
            return {"images": images, "tables": tables, "equations": equations}
        
        except Exception as e:
            logger.error(f"JSON解析失败: {e}")
            return {"images": [], "tables": [], "equations": []}
    
    def parse_markdown_file(self, file_path: str, json_path: Optional[str] = None) -> Dict[str, Any]:
        try:
            md_path = Path(file_path)
            if not md_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            json_data = None
            json_file_path = None
            if json_path:
                json_data = self._extract_from_json(Path(json_path))
                json_file_path = Path(json_path)
            else:
                json_candidates = list(md_path.parent.glob("*content_list.json"))
                if json_candidates:
                    json_data = self._extract_from_json(json_candidates[0])
                    json_file_path = json_candidates[0]
            
            return self.parse_markdown_content(content, md_path.parent, json_data, json_file_path)
        
        except Exception as e:
            logger.error(f"MD文件解析失败: {e}")
            raise
    
    def parse_markdown_content(self, content: str, base_path: Optional[Path] = None, 
                              json_data: Optional[Dict] = None, json_file_path: Optional[Path] = None) -> Dict[str, Any]:
        """解析 Markdown 内容用于文档总结"""
        headings = self._extract_headings(content)
        
        if json_data:
            figures = json_data.get("images", [])
            formulas = json_data.get("equations", [])
            tables = json_data.get("tables", [])
            logger.info("使用JSON数据源")
        else:
            figures = self._extract_figures(content, base_path)
            formulas = self._extract_formulas(content)
            tables = self._extract_tables(content, base_path)
            logger.info("使用Markdown数据源")
        
        sections = self._build_sections_from_json(json_file_path, figures, formulas, tables) if json_file_path else self._build_sections(content, headings, figures, formulas, tables)
        metadata = self._calculate_metadata(sections, figures, formulas, tables)
        
        return {
            "sections": sections,
            "metadata": metadata
        }
    
    def _extract_headings(self, content: str) -> List[Dict[str, Any]]:
        headings = []
        for match in self.heading_pattern.finditer(content):
            hash_level = len(match.group(1))
            full_title = match.group(2).strip()
            start_pos = match.start()
            
            detected_level = hash_level
            number_match = self.number_pattern.match(full_title)
            if number_match:
                number = number_match.group(1)
                detected_level = len(number.split('.'))
            
            headings.append({
                "level": detected_level,
                "hash_level": hash_level,
                "title": full_title,
                "start": start_pos,
                "end": None
            })
        
        for i in range(len(headings)):
            if i < len(headings) - 1:
                headings[i]["end"] = headings[i + 1]["start"]
            else:
                headings[i]["end"] = len(content)
        
        return headings
    
    def _extract_figures(self, content: str, base_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        figures = []
        for idx, match in enumerate(self.image_pattern.finditer(content), 1):
            alt_text = match.group(1) or ""
            img_path = match.group(2)
            caption = match.group(3) or alt_text
            
            if base_path and not img_path.startswith(('http://', 'https://', '/')):
                full_path = base_path / img_path
                img_path = str(full_path) if full_path.exists() else img_path
            
            figures.append({
                "id": idx,
                "caption": caption,
                "img_path": img_path,
                "alt": alt_text
            })
        
        return figures
    
    def _extract_formulas(self, content: str) -> List[Dict[str, Any]]:
        formulas = []
        for idx, match in enumerate(self.formula_block_pattern.finditer(content), 1):
            formulas.append({
                "id": idx,
                "type": "block",
                "text": f"$$\n{match.group(1).strip()}\n$$",
                "position": match.start()
            })
        return formulas
    
    def _extract_tables(self, content: str, base_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        tables = []
        for idx, match in enumerate(self.table_pattern.finditer(content), 1):
            table_html = match.group(0)
            start_pos = match.start()
            
            caption = ""
            lines_before = content[:start_pos].split('\n')
            for line in reversed(lines_before[-3:]):
                if re.search(r'(?:Table|Tab\.|表)\s*\d+', line, re.IGNORECASE):
                    caption = line.strip()
                    break
            
            tables.append({
                "id": idx,
                "caption": caption,
                "body": table_html,
                "img_path": None,
                "position": start_pos
            })
        
        return tables
    
    def _build_sections(self, content: str, headings: List[Dict], figures: List[Dict], 
                       formulas: List[Dict], tables: List[Dict]) -> List[Dict[str, Any]]:
        if not headings:
            return [{
                "name": "Document",
                "level": 0,
                "path": "Document",
                "content": content.strip(),
                "fig_refs": self._find_items_in_section(figures, content, "image"),
                "table_refs": self._find_items_in_section(tables, content, "table"),
                "formula_refs": self._find_items_in_section(formulas, content, "equation")
            }]
        
        sections = []
        path_stack = []
        
        for heading in headings:
            section_content = content[heading["start"]:heading["end"]]
            lines = section_content.split('\n')
            pure_content = '\n'.join(lines[1:]).strip()
            
            fig_data = self._find_items_in_section(figures, pure_content, "image")
            table_data = self._find_items_in_section(tables, pure_content, "table")
            formula_data = self._find_items_in_section(formulas, pure_content, "equation")
            
            current_level = heading["level"]
            while path_stack and path_stack[-1]["level"] >= current_level:
                path_stack.pop()
            
            path_stack.append({"name": heading["title"], "level": current_level})
            path = " > ".join([item["name"] for item in path_stack])
            
            sections.append({
                "name": heading["title"],
                "level": current_level,
                "path": path,
                "content": pure_content,
                "fig_refs": fig_data,
                "table_refs": table_data,
                "formula_refs": formula_data
            })
        
        return sections
    
    def _build_sections_from_json(self, json_file_path: Path, figures: List[Dict], 
                                   formulas: List[Dict], tables: List[Dict]) -> List[Dict[str, Any]]:
        """从 JSON 文件构建章节，并根据位置分配图表公式"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                content_list = json.load(f)
        except Exception as e:
            logger.error(f"JSON 文件读取失败: {e}")
            return []
        
        # 构建章节结构
        sections = []
        current_section = None
        path_stack = []
        
        # 为每个图表公式建立索引映射（在 content_list 中的位置）
        element_positions = {}
        image_idx = table_idx = equation_idx = 1
        
        for idx, item in enumerate(content_list):
            item_type = item.get("type")
            if item_type == "image":
                element_positions[f"image_{image_idx}"] = idx
                image_idx += 1
            elif item_type == "table":
                element_positions[f"table_{table_idx}"] = idx
                table_idx += 1
            elif item_type == "equation":
                element_positions[f"equation_{equation_idx}"] = idx
                equation_idx += 1
        
        # 遍历构建章节
        for idx, item in enumerate(content_list):
            item_type = item.get("type")
            text = item.get("text", "").strip()
            
            if item_type == "text" and text:
                text_level = item.get("text_level", 0)
                
                if text_level > 0:
                    # 这是一个标题
                    level = text_level
                    
                    # 保存上一个章节
                    if current_section:
                        sections.append(current_section)
                    
                    # 更新路径栈
                    while path_stack and path_stack[-1]["level"] >= level:
                        path_stack.pop()
                    
                    path_stack.append({"name": text, "level": level, "index": idx})
                    path = " > ".join([p["name"] for p in path_stack])
                    
                    # 创建新章节
                    current_section = {
                        "name": text,
                        "level": level,
                        "path": path,
                        "content": "",
                        "start_index": idx,
                        "fig_refs": [],
                        "table_refs": [],
                        "formula_refs": []
                    }
                else:
                    # 这是正文内容
                    if current_section is None:
                        # 没有标题的情况，创建默认章节
                        current_section = {
                            "name": "Document",
                            "level": 0,
                            "path": "Document",
                            "content": "",
                            "start_index": 0,
                            "fig_refs": [],
                            "table_refs": [],
                            "formula_refs": []
                        }
                    
                    # 添加内容
                    if current_section["content"]:
                        current_section["content"] += "\n\n"
                    current_section["content"] += text
        
        # 添加最后一个章节
        if current_section:
            sections.append(current_section)
        
        # 为每个章节分配图表公式
        for section in sections:
            section_start = section.get("start_index", 0)
            # 找到下一个章节的起始位置
            section_end = len(content_list)
            for other_section in sections:
                if other_section.get("start_index", 0) > section_start:
                    section_end = min(section_end, other_section.get("start_index", 0))
            
            # 分配图片
            for fig in figures:
                fig_key = f"image_{fig['id']}"
                if fig_key in element_positions:
                    pos = element_positions[fig_key]
                    if section_start <= pos < section_end:
                        section["fig_refs"].append(fig)
            
            # 分配表格
            for tbl in tables:
                tbl_key = f"table_{tbl['id']}"
                if tbl_key in element_positions:
                    pos = element_positions[tbl_key]
                    if section_start <= pos < section_end:
                        section["table_refs"].append(tbl)
            
            # 分配公式
            for eq in formulas:
                eq_key = f"equation_{eq['id']}"
                if eq_key in element_positions:
                    pos = element_positions[eq_key]
                    if section_start <= pos < section_end:
                        section["formula_refs"].append(eq)
            
            # 删除临时字段
            section.pop("start_index", None)
        
        logger.info(f"从 JSON 构建章节: {len(sections)} 个")
        return sections
    
    def _find_items_in_section(self, items: List[Dict], section_content: str, 
                               item_type: str) -> List[Dict]:
        """查找章节中的图表公式，返回完整数据"""
        found_items = []
        
        for item in items:
            item_id = item.get("id")
            if not item_id:
                continue
            
            found = False
            
            if item_type == "image":
                pattern = rf'(?:Figure|Fig\.|图)\s*{item_id}\b'
                if re.search(pattern, section_content, re.IGNORECASE):
                    found = True
            
            elif item_type == "table":
                pattern = rf'(?:Table|Tab\.|表)\s*{item_id}\b'
                if re.search(pattern, section_content, re.IGNORECASE):
                    found = True
            
            elif item_type == "equation":
                formula_text = item.get("text", "")
                if formula_text:
                    formula_snippet = formula_text.replace('$$', '').replace('\n', ' ').strip()[:30]
                    if formula_snippet and formula_snippet in section_content:
                        found = True
            
            if found:
                found_items.append(item)
        
        return found_items
    
    def _count_words(self, text: str) -> int:
        text = re.sub(r'[#*`_\[\]()!]', '', text)
        text = re.sub(r'https?://\S+', '', text)
        
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        english_text = re.sub(r'[\u4e00-\u9fff]', '', text)
        english_words = [word for word in english_text.split() if word.strip()]
        
        return len(chinese_chars) + len(english_words)
    
    def _calculate_metadata(self, sections: List[Dict], figures: List[Dict], 
                           formulas: List[Dict], tables: List[Dict]) -> Dict[str, Any]:
        total_words = sum(section.get("word_count", 0) for section in sections)
        
        return {
            "total_sections": len(sections),
            "total_figures": len(figures),
            "total_formulas": len(formulas),
            "total_tables": len(tables),
            "total_words": total_words,
            "top_level_sections": len([s for s in sections if s.get("level") == 1])
        }

markdown_parser = MarkdownParser()


def parse_markdown_for_summary(file_path: str, json_path: Optional[str] = None) -> Dict[str, Any]:
    """解析 Markdown 文件用于文档总结"""
    return markdown_parser.parse_markdown_file(file_path, json_path)

