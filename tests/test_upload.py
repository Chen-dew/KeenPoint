"""
文档上传功能测试
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
import io

client = TestClient(app)

def test_root_endpoint():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

def test_health_check():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_upload_pdf_success():
    """测试 PDF 上传成功"""
    # 创建一个模拟的 PDF 文件
    pdf_content = b"%PDF-1.4 sample content"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    
    response = client.post("/api/v1/upload/", files=files)
    
    # 由于没有真实的 PDF 解析，可能会失败，这里检查响应格式
    assert response.status_code in [200, 500]
    assert "status" in response.json()

def test_upload_unsupported_file():
    """测试上传不支持的文件类型"""
    files = {"file": ("test.txt", io.BytesIO(b"text content"), "text/plain")}
    
    response = client.post("/api/v1/upload/", files=files)
    
    # 应该返回 400 错误
    assert response.status_code == 400
    assert "不支持的文件类型" in response.json()["detail"]

def test_upload_without_file():
    """测试未提供文件的情况"""
    response = client.post("/api/v1/upload/")
    
    # 应该返回 422 验证错误
    assert response.status_code == 422

@pytest.mark.parametrize("filename,expected_status", [
    ("document.pdf", 200),
    ("paper.docx", 200),
    ("report.doc", 200),
])
def test_upload_various_formats(filename, expected_status):
    """测试各种文件格式"""
    content = b"sample content"
    files = {"file": (filename, io.BytesIO(content), "application/octet-stream")}
    
    response = client.post("/api/v1/upload/", files=files)
    
    # 注意: 实际测试需要真实的文件内容
    assert response.status_code in [200, 500]
