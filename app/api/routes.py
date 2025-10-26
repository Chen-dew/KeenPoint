"""
API 路由聚合器
整合所有业务模块的路由到统一的 router
"""

from fastapi import APIRouter
from . import upload, analysis, image_manager, ppt_generator

# 创建主路由器
router = APIRouter(prefix="/api/v1")

# 注册各功能模块的路由
router.include_router(
    upload.router,
    prefix="/upload",
    tags=["📤 文档上传"]
)

router.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["🔍 结构分析"]
)

router.include_router(
    image_manager.router,
    prefix="/images",
    tags=["🖼️ 图像管理"]
)

router.include_router(
    ppt_generator.router,
    prefix="/ppt",
    tags=["📊 PPT生成"]
)
