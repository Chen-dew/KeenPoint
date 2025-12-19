"""KeenPoint API服务"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings, ensure_dirs
from app.core.logger import logger


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    ensure_dirs()
    logger.info(f"[APP] {settings.APP_NAME} v{settings.VERSION} started")


@app.on_event("shutdown")
async def shutdown():
    logger.info("[APP] shutdown")


@app.get("/")
def root():
    return {"name": settings.APP_NAME, "version": settings.VERSION}


@app.get("/health")
def health():
    return {"status": "ok"}
