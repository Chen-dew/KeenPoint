"""Markdown文档解析服务"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.logger import logger


class MarkdownParser:
    """Markdown解析器"""
    
    HEADING_RE = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    IMAGE_RE = re.compile(r'!\[([^\]]*)\]\(([^\s\)]+)(?:\s+"([^"]*)")?\)')
    NUMBER_RE = re.compile(r'^(\d+(?:\.\d+)*)\.?\s+(.*)$')
    FORMULA_RE = re.compile(r'\$\$([^\$]+?)\$\$', re.DOTALL)
    TABLE_RE = re.compile(r'<table[^>]*>(.*?)</table>', re.DOTALL | re.IGNORECASE)
    
    def parse(self, file_path: str, json_path: Optional[str] = None) -> Dict[str, Any]:
        """解析Markdown文件"""
        md_path = Path(file_path)
        if not md_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试加载JSON数据
        json_data = None
        json_file = None
        if json_path:
            json_file = Path(json_path)
            json_data = self._load_json(json_file)
        else:
            candidates = list(md_path.parent.glob("*content_list.json"))
            if candidates:
                json_file = candidates[0]
                json_data = self._load_json(json_file)
        
        return self._parse_content(content, md_path.parent, json_data, json_file)
    
    def _load_json(self, path: Path) -> Optional[Dict]:
        """加载JSON文件提取图表公式"""
        if not path.exists():
            logger.warning(f"[PARSE] json not found: {path}")
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            images, tables, equations = [], [], []
            img_id = tbl_id = eq_id = 1
            
            for item in data:
                t = item.get("type")
                if t == "image":
                    images.append({
                        "type": "image", "id": img_id,
                        "img_path": item.get("img_path", ""),
                        "caption": " ".join(item.get("image_caption", []))
                    })
                    img_id += 1
                elif t == "table":
                    tables.append({
                        "type": "table", "id": tbl_id,
                        "img_path": item.get("img_path", ""),
                        "caption": " ".join(item.get("table_caption", [])),
                        "body": item.get("table_body", "")
                    })
                    tbl_id += 1
                elif t == "equation":
                    equations.append({
                        "type": "equation", "id": eq_id,
                        "img_path": item.get("img_path", ""),
                        "text": item.get("text", ""),
                        "text_format": item.get("text_format", "latex")
                    })
                    eq_id += 1
            
            logger.info(f"[PARSE] json loaded: images={len(images)}, tables={len(tables)}, equations={len(equations)}")
            return {"images": images, "tables": tables, "equations": equations, "raw": data}
        except Exception as e:
            logger.error(f"[PARSE] json load error: {e}")
            return None
    
    def _parse_content(self, content: str, base_path: Path, 
                       json_data: Optional[Dict], json_file: Optional[Path]) -> Dict[str, Any]:
        """解析Markdown内容"""
        headings = self._extract_headings(content)
        
        if json_data:
            figures = json_data.get("images", [])
            tables = json_data.get("tables", [])
            formulas = json_data.get("equations", [])
            sections = self._build_sections_from_json(json_data.get("raw", []), figures, tables, formulas)
        else:
            figures = self._extract_figures(content, base_path)
            tables = self._extract_tables(content)
            formulas = self._extract_formulas(content)
            sections = self._build_sections(content, headings, figures, tables, formulas)
        
        metadata = {
            "total_sections": len(sections),
            "total_figures": len(figures),
            "total_tables": len(tables),
            "total_formulas": len(formulas)
        }
        
        logger.info(f"[PARSE] done: {metadata}")
        return {"sections": sections, "metadata": metadata}
    
    def _extract_headings(self, content: str) -> List[Dict]:
        """提取标题"""
        headings = []
        for m in self.HEADING_RE.finditer(content):
            level = len(m.group(1))
            title = m.group(2).strip()
            
            # 根据数字编号判断层级
            num_match = self.NUMBER_RE.match(title)
            if num_match:
                level = len(num_match.group(1).split('.'))
            
            headings.append({
                "level": level,
                "title": title,
                "start": m.start(),
                "end": None
            })
        
        for i in range(len(headings)):
            headings[i]["end"] = headings[i + 1]["start"] if i < len(headings) - 1 else len(content)
        
        return headings
    
    def _extract_figures(self, content: str, base_path: Path) -> List[Dict]:
        """提取图片"""
        figures = []
        for idx, m in enumerate(self.IMAGE_RE.finditer(content), 1):
            img_path = m.group(2)
            if base_path and not img_path.startswith(('http://', 'https://')):
                full = base_path / img_path
                if full.exists():
                    img_path = str(full)
            
            figures.append({
                "id": idx,
                "img_path": img_path,
                "caption": m.group(3) or m.group(1) or "",
                "alt": m.group(1) or ""
            })
        return figures
    
    def _extract_tables(self, content: str) -> List[Dict]:
        """提取表格"""
        tables = []
        for idx, m in enumerate(self.TABLE_RE.finditer(content), 1):
            # 查找表格标题
            caption = ""
            before = content[:m.start()].split('\n')
            for line in reversed(before[-3:]):
                if re.search(r'(?:Table|Tab\.|表)\s*\d+', line, re.IGNORECASE):
                    caption = line.strip()
                    break
            
            tables.append({
                "id": idx,
                "caption": caption,
                "body": m.group(0),
                "img_path": None
            })
        return tables
    
    def _extract_formulas(self, content: str) -> List[Dict]:
        """提取公式"""
        formulas = []
        for idx, m in enumerate(self.FORMULA_RE.finditer(content), 1):
            formulas.append({
                "id": idx,
                "type": "block",
                "text": f"$$\n{m.group(1).strip()}\n$$"
            })
        return formulas
    
    def _build_sections(self, content: str, headings: List[Dict], 
                        figures: List[Dict], tables: List[Dict], formulas: List[Dict]) -> List[Dict]:
        """构建章节结构"""
        if not headings:
            return [{
                "name": "Document", "level": 0, "path": "Document",
                "content": content.strip(),
                "fig_refs": figures, "table_refs": tables, "formula_refs": formulas
            }]
        
        sections = []
        path_stack = []
        
        for h in headings:
            text = content[h["start"]:h["end"]]
            pure_content = '\n'.join(text.split('\n')[1:]).strip()
            
            # 更新路径栈
            while path_stack and path_stack[-1]["level"] >= h["level"]:
                path_stack.pop()
            path_stack.append({"name": h["title"], "level": h["level"]})
            
            sections.append({
                "name": h["title"],
                "level": h["level"],
                "path": " > ".join([p["name"] for p in path_stack]),
                "content": pure_content,
                "fig_refs": self._find_refs(figures, pure_content, "image"),
                "table_refs": self._find_refs(tables, pure_content, "table"),
                "formula_refs": self._find_refs(formulas, pure_content, "equation")
            })
        
        return sections
    
    def _build_sections_from_json(self, raw_data: List, figures: List[Dict], 
                                   tables: List[Dict], formulas: List[Dict]) -> List[Dict]:
        """从JSON构建章节"""
        if not raw_data:
            return []
        
        # 建立元素位置索引
        elem_pos = {}
        img_id = tbl_id = eq_id = 1
        for idx, item in enumerate(raw_data):
            t = item.get("type")
            if t == "image":
                elem_pos[f"image_{img_id}"] = idx
                img_id += 1
            elif t == "table":
                elem_pos[f"table_{tbl_id}"] = idx
                tbl_id += 1
            elif t == "equation":
                elem_pos[f"equation_{eq_id}"] = idx
                eq_id += 1
        
        # 构建章节
        sections = []
        current = None
        path_stack = []
        
        for idx, item in enumerate(raw_data):
            t = item.get("type")
            text = item.get("text", "").strip()
            
            if t == "text" and text:
                level = item.get("text_level", 0)
                
                if level > 0:
                    # 标题
                    if current:
                        sections.append(current)
                    
                    while path_stack and path_stack[-1]["level"] >= level:
                        path_stack.pop()
                    path_stack.append({"name": text, "level": level})
                    
                    current = {
                        "name": text,
                        "level": level,
                        "path": " > ".join([p["name"] for p in path_stack]),
                        "content": "",
                        "start_idx": idx,
                        "fig_refs": [], "table_refs": [], "formula_refs": []
                    }
                else:
                    # 正文
                    if current is None:
                        current = {
                            "name": "Document", "level": 0, "path": "Document",
                            "content": "", "start_idx": 0,
                            "fig_refs": [], "table_refs": [], "formula_refs": []
                        }
                    current["content"] += ("\n\n" if current["content"] else "") + text
        
        if current:
            sections.append(current)
        
        # 分配图表公式到章节
        for sec in sections:
            start = sec.get("start_idx", 0)
            end = min([s.get("start_idx", len(raw_data)) for s in sections if s.get("start_idx", 0) > start] or [len(raw_data)])
            
            for fig in figures:
                pos = elem_pos.get(f"image_{fig['id']}")
                if pos is not None and start <= pos < end:
                    sec["fig_refs"].append(fig)
            
            for tbl in tables:
                pos = elem_pos.get(f"table_{tbl['id']}")
                if pos is not None and start <= pos < end:
                    sec["table_refs"].append(tbl)
            
            for eq in formulas:
                pos = elem_pos.get(f"equation_{eq['id']}")
                if pos is not None and start <= pos < end:
                    sec["formula_refs"].append(eq)
            
            sec.pop("start_idx", None)
        
        return sections
    
    def _find_refs(self, items: List[Dict], content: str, item_type: str) -> List[Dict]:
        """查找章节中引用的元素"""
        found = []
        patterns = {
            "image": r'(?:Figure|Fig\.|图)\s*{}\b',
            "table": r'(?:Table|Tab\.|表)\s*{}\b'
        }
        
        for item in items:
            item_id = item.get("id")
            if item_type in patterns:
                if re.search(patterns[item_type].format(item_id), content, re.IGNORECASE):
                    found.append(item)
            elif item_type == "equation":
                text = item.get("text", "").replace('$$', '').strip()[:30]
                if text and text in content:
                    found.append(item)
        
        return found


# 单例
_parser = MarkdownParser()


def parse_markdown(file_path: str, json_path: Optional[str] = None) -> Dict[str, Any]:
    """解析Markdown文件"""
    return _parser.parse(file_path, json_path)

