"""
FastAPI 主应用入口
提供学术论文辅助系统的核心 API 服务
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes
from app.core.config import settings
from app.core.logger import logger

# 创建 FastAPI 应用实例
app = FastAPI(
    title="Academic Paper Assistant",
    description="AI 学术论文辅助网站 - 支持文档解析、结构分析、图像管理和 PPT 生成",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册所有 API 路由
app.include_router(routes.router)

@app.on_event("startup")
async def startup_event():
    """应用启动时执行的操作"""
    logger.info("🚀 Academic Paper Assistant API 正在启动...")
    logger.info(f"📝 环境: {settings.ENVIRONMENT}")
    logger.info(f"📁 上传目录: {settings.UPLOAD_DIR}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行的操作"""
    logger.info("👋 Academic Paper Assistant API 正在关闭...")

@app.get("/")
def home():
    """
    API 根路径 - 欢迎页面
    """
    return {
        "message": "Welcome to the Academic Paper Assistant API 🚀",
        "version": "0.1.0",
        "docs": "/docs",
        "features": [
            "文档解析 (PDF/Word)",
            "结构分析 (章节识别)",
            "图像管理 (提取与分类)",
            "PPT 生成 (自动演示文稿)"
        ]
    }

@app.get("/health")
def health_check():
    """
    健康检查接口
    """
    return {
        "status": "healthy",
        "service": "Academic Paper Assistant",
        "version": "0.1.0"
    }
