"""布局服务: PPT页面模板渲染"""

from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader

from app.core.logger import logger
from app.services.document.nlp_service import extract_article_basic_info

TAG = "[LAYOUT]"


class LayoutService:
    """布局服务类"""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent / "template"
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
    
    def render_title_page(self, basic_info: Dict[str, Any]) -> str:
        """渲染标题页模板"""
        logger.info(f"{TAG} render_title_page")
        
        try:
            template = self.env.get_template("title_page.html")
            
            template_vars = {
                "title": basic_info.get("title", "Untitled Document"),
                "subtitle": basic_info.get("subtitle", ""),
                "authors": basic_info.get("authors", []),
                "affiliation": basic_info.get("affiliation", ""),
                "date": basic_info.get("date", "")
            }
            
            if not template_vars["date"]:
                from datetime import datetime
                template_vars["date"] = datetime.now().strftime("%Y-%m-%d")
            
            html = template.render(**template_vars)
            logger.info(f"{TAG} render_title_page done, len={len(html)}")
            return html
            
        except Exception as e:
            logger.error(f"{TAG} render_title_page error: {e}")
            raise
    
    def render_title_page_from_parse_result(self, parse_result: Dict[str, Any]) -> str:
        """从解析结果直接渲染标题页"""
        logger.info(f"{TAG} render_title_page_from_parse_result")
        
        basic_info = extract_article_basic_info(parse_result)
        
        if basic_info.get("error"):
            logger.warning(f"{TAG} basic_info extraction failed: {basic_info['error']}")
            basic_info = {"title": "Document", "subtitle": "", "authors": [], "affiliation": "", "date": ""}
        
        return self.render_title_page(basic_info)
    
    def render_picture_page(self, data: Dict[str, Any]) -> str:
        """渲染图文页模板"""
        logger.info(f"{TAG} render_picture_page: {data.get('slide_title', '')[:40]}")
        
        try:
            template = self.env.get_template("test.html")
            
            # 支持两种数据格式
            text_content = data.get("text_content", {})
            if text_content:
                # 新格式: text_content.paragraphs, text_content.bullet_points
                paragraphs = text_content.get("paragraphs", [])
                bullet_points = text_content.get("bullet_points", [])
            else:
                # 旧格式: 直接的 paragraphs, bullets
                paragraphs = data.get("paragraphs", [])
                bullet_points = data.get("bullets", [])
            
            # 处理图片数据 - test.html 使用 src/alt
            image = data.get("image", {})
            image_data = {
                "src": image.get("url") or image.get("src", ""),
                "alt": image.get("alt_text") or image.get("alt", ""),
                "caption": image.get("caption", "")
            }
            
            template_vars = {
                "section_index": data.get("section_index", ""),
                "section_title": data.get("section_title", ""),
                "title": data.get("slide_title", ""),
                "paragraphs": paragraphs,
                "bullet_points": bullet_points,
                "image": image_data
            }
            
            html = template.render(**template_vars)
            logger.info(f"{TAG} render_picture_page done, len={len(html)}")
            return html
            
        except Exception as e:
            logger.error(f"{TAG} render_picture_page error: {e}")
            raise
            raise
    
    def save_title_page(self, basic_info: Dict[str, Any], output_path: str) -> str:
        """渲染并保存标题页"""
        logger.info(f"{TAG} save_title_page: {output_path}")
        html = self.render_title_page(basic_info)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return output_path
    
    def save_picture_page(self, data: Dict[str, Any], output_path: str) -> str:
        """渲染并保存图文页"""
        logger.info(f"{TAG} save_picture_page: {output_path}")
        html = self.render_picture_page(data)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return output_path


# 单例
_service = LayoutService()


def render_title_page(basic_info: Dict[str, Any]) -> str:
    """渲染标题页模板"""
    return _service.render_title_page(basic_info)


def render_title_page_from_parse_result(parse_result: Dict[str, Any]) -> str:
    """从解析结果直接渲染标题页"""
    return _service.render_title_page_from_parse_result(parse_result)


def render_picture_page(data: Dict[str, Any]) -> str:
    """渲染图文页模板"""
    return _service.render_picture_page(data)


def save_title_page(basic_info: Dict[str, Any], output_path: str) -> str:
    """渲染并保存标题页"""
    return _service.save_title_page(basic_info, output_path)


def save_picture_page(data: Dict[str, Any], output_path: str) -> str:
    """渲染并保存图文页"""
    return _service.save_picture_page(data, output_path)
