"""
结构分析 API
对论文进行章节识别和内容分析
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from app.services import nlp_service
from app.core.logger import logger

router = APIRouter()

class AnalysisRequest(BaseModel):
    """分析请求模型"""
    text: str
    options: Dict = {}

class AnalysisResponse(BaseModel):
    """分析结果模型"""
    status: str
    sections_detected: List[str]
    section_count: int
    details: Dict = {}

@router.post("/structure", response_model=AnalysisResponse)
async def analyze_structure(request: AnalysisRequest):
    """
    分析论文结构
    
    自动识别论文章节:
    - Introduction (引言)
    - Related Work (相关工作)
    - Methods (方法)
    - Results (结果)
    - Discussion (讨论)
    - Conclusion (结论)
    
    参数:
    - text: 论文文本内容
    - options: 可选参数（如语言、详细程度等）
    
    返回:
    - sections_detected: 检测到的章节列表
    - section_count: 章节数量
    - details: 详细分析结果
    """
    logger.info("🔍 开始论文结构分析...")
    
    if not request.text or len(request.text) < 100:
        raise HTTPException(
            status_code=400,
            detail="文本内容过短，无法进行有效分析"
        )
    
    try:
        # 调用 NLP 服务进行结构分析
        result = nlp_service.analyze_structure(request.text)
        
        logger.info(f"✅ 结构分析完成，检测到 {result['section_count']} 个章节")
        
        return {
            "status": "success",
            "sections_detected": result["sections_detected"],
            "section_count": result["section_count"],
            "details": result.get("details", {})
        }
    
    except Exception as e:
        logger.error(f"❌ 结构分析失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"结构分析失败: {str(e)}"
        )

@router.post("/keywords")
async def extract_keywords(text: str, top_n: int = 10):
    """
    提取论文关键词
    
    参数:
    - text: 论文文本
    - top_n: 返回关键词数量
    
    返回:
    - keywords: 关键词列表
    """
    logger.info("🔑 开始提取关键词...")
    
    try:
        keywords = nlp_service.extract_keywords(text, top_n)
        
        return {
            "status": "success",
            "keywords": keywords,
            "count": len(keywords)
        }
    
    except Exception as e:
        logger.error(f"❌ 关键词提取失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"关键词提取失败: {str(e)}"
        )

@router.post("/summary")
async def generate_summary(text: str, max_length: int = 200):
    """
    生成论文摘要
    
    参数:
    - text: 论文文本
    - max_length: 摘要最大长度
    
    返回:
    - summary: 自动生成的摘要
    """
    logger.info("📝 开始生成摘要...")
    
    try:
        summary = nlp_service.generate_summary(text, max_length)
        
        return {
            "status": "success",
            "summary": summary,
            "length": len(summary)
        }
    
    except Exception as e:
        logger.error(f"❌ 摘要生成失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"摘要生成失败: {str(e)}"
        )
