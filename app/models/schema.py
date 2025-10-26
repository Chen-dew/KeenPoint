"""
Pydantic 数据模型
定义 API 请求和响应的数据结构
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

# ========== 文档相关模型 ==========

class DocumentMetadata(BaseModel):
    """文档元数据"""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None

class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    status: str
    message: str
    filename: str
    document_id: str
    type: str  # pdf or word
    page_count: Optional[int] = None
    paragraph_count: Optional[int] = None
    text_length: int
    metadata: DocumentMetadata

# ========== 分析相关模型 ==========

class AnalysisRequest(BaseModel):
    """结构分析请求"""
    text: str = Field(..., min_length=100, description="论文文本内容")
    options: Optional[Dict] = Field(default={}, description="可选参数")

class SectionDetail(BaseModel):
    """章节详细信息"""
    keyword_matched: str
    occurrences: int
    first_position: int

class StructureAnalysisResponse(BaseModel):
    """结构分析响应"""
    status: str
    sections_detected: List[str]
    section_count: int
    details: Dict[str, SectionDetail] = {}

class KeywordExtractionResponse(BaseModel):
    """关键词提取响应"""
    status: str
    keywords: List[str]
    count: int

class SummaryResponse(BaseModel):
    """摘要生成响应"""
    status: str
    summary: str
    length: int

# ========== 图像相关模型 ==========

class ImageInfo(BaseModel):
    """图像信息"""
    id: int
    name: str
    path: str
    page: Optional[int] = None
    type: str  # chart, diagram, photo, equation
    format: str
    size: int
    caption: Optional[str] = None

class ImageExtractionResponse(BaseModel):
    """图像提取响应"""
    status: str
    images: List[ImageInfo]
    count: int

class ImageClassificationResponse(BaseModel):
    """图像分类响应"""
    status: str
    classified: Dict[str, List[Dict]]
    total: int

class ImageExportResponse(BaseModel):
    """图像导出响应"""
    status: str
    download_url: str
    file_size: int
    format: str

# ========== PPT 相关模型 ==========

class PPTGenerationRequest(BaseModel):
    """PPT 生成请求"""
    document_id: str = Field(..., description="文档唯一标识符")
    structure_data: Dict = Field(..., description="论文结构分析数据")
    include_images: bool = Field(default=True, description="是否包含图像")
    template: str = Field(default="default", description="PPT 模板")
    options: Optional[Dict] = Field(default={}, description="其他自定义选项")

class PPTGenerationResponse(BaseModel):
    """PPT 生成响应"""
    status: str
    ppt_path: str
    slide_count: int
    download_url: str

class PPTTemplate(BaseModel):
    """PPT 模板信息"""
    id: str
    name: str
    description: str
    preview: str

class PPTCustomizationRequest(BaseModel):
    """PPT 自定义请求"""
    ppt_path: str
    customizations: Dict = Field(
        ...,
        description="自定义配置 (theme, font, layout)"
    )

# ========== 通用响应模型 ==========

class SuccessResponse(BaseModel):
    """成功响应"""
    status: str = "success"
    message: str
    data: Optional[Dict] = None

class ErrorResponse(BaseModel):
    """错误响应"""
    status: str = "error"
    message: str
    detail: Optional[str] = None

class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)
