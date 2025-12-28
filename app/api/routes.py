"""API路由"""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.logger import logger
from app.core.config import settings
from app.services.document.parse_service import parse_markdown
from app.services.document.nlp_service import analyze_full_document, extract_article_basic_info
from app.services.document.image_service import extract_elements, analyze_elements
from app.services.document.outline_service import build_outline, analyze_outline

router = APIRouter()


@router.post("/parse")
async def api_parse(md_path: str, json_path: Optional[str] = None):
    """解析Markdown文档"""
    logger.info(f"[API] parse: {md_path}")
    try:
        result = parse_markdown(md_path, json_path)
        return {"status": "ok", "data": result}
    except Exception as e:
        logger.error(f"[API] parse error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/basic")
async def api_analyze_basic(parse_result: dict):
    """提取文章基础信息"""
    logger.info("[API] analyze/basic")
    try:
        result = extract_article_basic_info(parse_result)
        return {"status": "ok", "data": result}
    except Exception as e:
        logger.error(f"[API] analyze/basic error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/full")
async def api_analyze_full(parse_result: dict, abstract: str = ""):
    """完整文档分析"""
    logger.info("[API] analyze/full")
    try:
        result = analyze_full_document(parse_result, abstract)
        return {"status": "ok", "data": result}
    except Exception as e:
        logger.error(f"[API] analyze/full error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/images")
async def api_analyze_images(parse_result: dict, base_path: Optional[str] = None):
    """图表分析"""
    logger.info("[API] analyze/images")
    try:
        elements = extract_elements(parse_result)
        bp = Path(base_path) if base_path else None
        result = analyze_elements(elements, bp)
        return {"status": "ok", "data": result}
    except Exception as e:
        logger.error(f"[API] analyze/images error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outline/build")
async def api_outline_build(parse_result: dict, text_analysis: list, visual_analysis: list):
    """构建大纲输入"""
    logger.info("[API] outline/build")
    try:
        result = build_outline(parse_result, text_analysis, visual_analysis)
        return {"status": "ok", "data": result}
    except Exception as e:
        logger.error(f"[API] outline/build error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outline/analyze")
async def api_outline_analyze(outline_inputs: list):
    """大纲分析"""
    logger.info("[API] outline/analyze")
    try:
        result = analyze_outline(outline_inputs)
        return {"status": "ok", "data": result}
    except Exception as e:
        logger.error(f"[API] outline/analyze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
