"""
文档解析服务
处理 PDF 和 Word 文档的解析与文本提取
"""

import fitz  # PyMuPDF
from docx import Document
import tempfile
import os
from typing import Dict
from app.core.logger import logger
from app.core.utils import generate_unique_id

async def parse_document(file) -> Dict:
    """
    解析 PDF 或 Word 文件
    
    参数:
    - file: UploadFile 对象
    
    返回:
    - 解析结果字典
    """
    suffix = file.filename.split(".")[-1].lower()
    
    if suffix == "pdf":
        return await _parse_pdf(file)
    elif suffix in ["doc", "docx"]:
        return await _parse_word(file)
    else:
        logger.error(f"不支持的文件类型: {suffix}")
        return {"error": "Unsupported file type"}

async def _parse_pdf(file) -> Dict:
    """
    解析 PDF 文件
    
    参数:
    - file: UploadFile 对象
    
    返回:
    - PDF 解析结果
    """
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # 使用 PyMuPDF 解析
        doc = fitz.open(tmp_path)
        
        # 提取文本
        text = ""
        for page_num, page in enumerate(doc, start=1):
            text += f"\n--- Page {page_num} ---\n"
            text += page.get_text()
        
        # 提取元数据
        metadata = doc.metadata
        
        # 统计信息
        result = {
            "type": "pdf",
            "filename": file.filename,
            "page_count": len(doc),
            "text_length": len(text),
            "text_preview": text[:1000] + "..." if len(text) > 1000 else text,
            "full_text": text,
            "metadata": {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", "")
            },
            "document_id": generate_unique_id()
        }
        
        doc.close()
        
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        logger.info(f"✅ PDF 解析成功: {file.filename}, {len(doc)} 页")
        return result
    
    except Exception as e:
        logger.error(f"❌ PDF 解析失败: {str(e)}")
        return {"error": f"PDF parsing failed: {str(e)}"}

async def _parse_word(file) -> Dict:
    """
    解析 Word 文件
    
    参数:
    - file: UploadFile 对象
    
    返回:
    - Word 解析结果
    """
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # 使用 python-docx 解析
        doc = Document(tmp_path)
        
        # 提取段落文本
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
        
        # 提取表格内容
        tables_count = len(doc.tables)
        
        # 提取核心属性
        core_properties = doc.core_properties
        
        result = {
            "type": "word",
            "filename": file.filename,
            "paragraph_count": len(paragraphs),
            "tables_count": tables_count,
            "text_length": len(text),
            "text_preview": text[:1000] + "..." if len(text) > 1000 else text,
            "full_text": text,
            "metadata": {
                "title": core_properties.title or "",
                "author": core_properties.author or "",
                "subject": core_properties.subject or "",
                "keywords": core_properties.keywords or ""
            },
            "document_id": generate_unique_id()
        }
        
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        logger.info(f"✅ Word 解析成功: {file.filename}, {len(paragraphs)} 段落")
        return result
    
    except Exception as e:
        logger.error(f"❌ Word 解析失败: {str(e)}")
        return {"error": f"Word parsing failed: {str(e)}"}

def extract_text_from_file(file_path: str) -> str:
    """
    从文件路径直接提取文本
    
    参数:
    - file_path: 文件路径
    
    返回:
    - 提取的文本
    """
    ext = file_path.split('.')[-1].lower()
    
    try:
        if ext == 'pdf':
            doc = fitz.open(file_path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            return text
        elif ext in ['doc', 'docx']:
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        else:
            return ""
    except Exception as e:
        logger.error(f"❌ 文本提取失败: {str(e)}")
        return ""
