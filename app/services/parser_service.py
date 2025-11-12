"""
文档解析服务
使用 MinerU API 进行文档解析
"""

import tempfile
import os
import zipfile
import re
import aiohttp
import aiofiles
from typing import List, Dict
from app.core.logger import logger
from app.core.config import settings

async def parse_pdf_with_mineru(pdf_path: str, output_folder: str) -> str:
    """
    使用 MinerU API 解析 PDF 文件并提取文本和图像
    
    参数:
    - pdf_path: PDF 文件路径
    - output_folder: 保存提取内容的根目录
    
    返回:
    - str: 提取内容的文件夹路径
    """
    assert settings.MINERU_API is not None, "MINERU_API is not set"
    logger.info(f"Using MinerU API to parse PDF: {pdf_path}")
    
    os.makedirs(output_folder, exist_ok=True)

    # 读取 PDF 文件内容
    async with aiofiles.open(pdf_path, "rb") as f:
        pdf_content = await f.read()

    # 准备表单数据
    data = aiohttp.FormData()
    data.add_field(
        "files",
        pdf_content,
        filename=os.path.basename(pdf_path),
        content_type="application/pdf",
    )
    data.add_field("return_images", "True")
    data.add_field("response_format_zip", "True")

    # 准备请求头
    headers = {
        "Authorization": f"Bearer {settings.MINERU_TOKEN}"
    }

    # 发送请求到 MinerU API
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(settings.MINERU_API, data=data, headers=headers) as response:
                response.raise_for_status()
                content = await response.read()

                # 保存 ZIP 文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                    tmp.write(content)
                    zip_path = tmp.name

                logger.info("Received ZIP response, extracting files...")

                # 解压 ZIP 文件
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    # 获取顶层文件夹名称
                    top_level = {
                        name.split("/", 1)[0] for name in zip_ref.namelist() if name.strip()
                    }
                    if len(top_level) != 1:
                        raise RuntimeError("Expected exactly one top-level folder in zip")
                    prefix = list(top_level)[0] + "/"

                    # 提取所有文件
                    for member in zip_ref.infolist():
                        filename = member.filename
                        dest_path = os.path.join(
                            output_folder, filename.removeprefix(prefix)
                        )

                        if not member.is_dir():
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            with zip_ref.open(member) as src, open(dest_path, "wb") as dst:
                                dst.write(src.read())

                # 清理临时 ZIP 文件
                try:
                    os.unlink(zip_path)
                except:
                    pass

                logger.info(f"PDF parsing completed successfully, output folder: {output_folder}")
                return output_folder

        except aiohttp.ClientError as e:
            logger.error(f"MinerU API request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"PDF parsing failed: {str(e)}")
            raise


def count_markdown_chunks(markdown: str) -> List[Dict]:
    """
    Extract headings and count characters in each section
    
    Args:
        markdown: Markdown content
    
    Returns:
        List of chunks with heading, level, and character count
    """
    # Match Markdown headings (# to ######)
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    chunks = []
    matches = list(heading_pattern.finditer(markdown))
    
    for i, match in enumerate(matches):
        level = len(match.group(1))
        heading = match.group(2).strip()
        start_pos = match.end()
        
        # Calculate end position (next heading or end of document)
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        
        # Extract content between headings
        content = markdown[start_pos:end_pos].strip()
        char_count = len(content)
        
        chunks.append({
            "level": level,
            "heading": heading,
            "char_count": char_count,
            "content": content
        })
    
    return chunks


def calculate_hierarchical_counts(chunks: List[Dict]) -> List[Dict]:
    """
    Calculate hierarchical character counts (direct + all children)
    
    Args:
        chunks: List of chunks from count_markdown_chunks
    
    Returns:
        Chunks with added direct_char_count and total_char_count
    """
    if not chunks:
        return []
    
    # Add direct and total count fields
    for chunk in chunks:
        chunk["direct_char_count"] = chunk["char_count"]
        chunk["total_char_count"] = chunk["char_count"]
    
    # Calculate total counts (including all descendants)
    for i in range(len(chunks) - 1, -1, -1):
        current_level = chunks[i]["level"]
        
        # Find all direct children and accumulate their total counts
        j = i + 1
        while j < len(chunks):
            if chunks[j]["level"] <= current_level:
                break
            if chunks[j]["level"] == current_level + 1:
                chunks[i]["total_char_count"] += chunks[j]["total_char_count"]
            j += 1
    
    return chunks


async def get_tree_structure(markdown: str, add_tag: bool = True) -> str:
    """
    Display tree structure statistics with character counts
    
    Args:
        markdown: Markdown content
        add_tag: Whether to wrap heading in <title> tags
    
    Returns:
        Formatted tree structure string
    
    Example:
        ■ Introduction [Direct:150 | Total:500]
          ├─ Background [Direct:200 | Total:200]
          ├─ Motivation [Direct:150 | Total:150]
    """
    try:
        chunks = count_markdown_chunks(markdown.strip())
        if not chunks:
            logger.info("No headings found in markdown")
            return "No headings found"
        
        chunks_with_hierarchy = calculate_hierarchical_counts(chunks)
        
        tree = ""
        for chunk in chunks_with_hierarchy:
            indent = "  " * (chunk["level"] - 1)
            tree_symbol = "├─" if chunk["level"] > 1 else "■"
            
            if add_tag:
                heading = f"<title>{chunk['heading']}</title>"
            else:
                heading = chunk["heading"]
            
            tree += (
                f"{indent}{tree_symbol} {heading} "
                f"[Direct:{chunk['direct_char_count']} | Total:{chunk['total_char_count']}]\n"
            )
        
        logger.info(f"Generated tree structure with {len(chunks)} nodes")
        return tree
    
    except Exception as e:
        logger.error(f"Failed to generate tree structure: {str(e)}")
        return f"Error: {str(e)}"


async def extract_heading_tree(markdown_content: str) -> List[Dict]:
    """
    Extract heading tree structure from Markdown document
    
    Args:
        markdown_content: Markdown document content
    
    Returns:
        Hierarchical tree structure with nested children
    
    Example:
        [
            {
                "level": 1,
                "title": "Introduction",
                "line": 1,
                "char_count": 150,
                "children": [
                    {
                        "level": 2,
                        "title": "Background",
                        "line": 5,
                        "char_count": 200,
                        "children": []
                    }
                ]
            }
        ]
    """
    try:
        # Match Markdown headings (# to ######)
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        
        headings = []
        matches = list(heading_pattern.finditer(markdown_content))
        
        for i, match in enumerate(matches):
            level = len(match.group(1))
            title = match.group(2).strip()
            line = markdown_content[:match.start()].count('\n') + 1
            
            # Calculate character count in this section
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(markdown_content)
            char_count = len(markdown_content[start_pos:end_pos].strip())
            
            headings.append({
                "level": level,
                "title": title,
                "line": line,
                "char_count": char_count,
                "children": []
            })
        
        if not headings:
            logger.info("No headings found in markdown content")
            return []
        
        # Build tree structure using stack
        root = []
        stack = []
        
        for heading in headings:
            # Pop nodes with level >= current level
            while stack and stack[-1]["level"] >= heading["level"]:
                stack.pop()
            
            # Add to root or parent's children
            if not stack:
                root.append(heading)
                stack.append(heading)
            else:
                stack[-1]["children"].append(heading)
                stack.append(heading)
        
        logger.info(f"Extracted heading tree with {len(headings)} headings, {len(root)} root nodes")
        return root
    
    except Exception as e:
        logger.error(f"Failed to extract heading tree: {str(e)}")
        return []


async def extract_heading_tree_from_file(markdown_path: str) -> List[Dict]:
    """
    Extract heading tree structure from Markdown file
    
    Args:
        markdown_path: Path to Markdown file
    
    Returns:
        Hierarchical tree structure
    """
    try:
        async with aiofiles.open(markdown_path, "r", encoding="utf-8") as f:
            content = await f.read()
        
        logger.info(f"Reading markdown file: {markdown_path}")
        return await extract_heading_tree(content)
    
    except FileNotFoundError:
        logger.error(f"Markdown file not found: {markdown_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to read markdown file: {str(e)}")
        return []

