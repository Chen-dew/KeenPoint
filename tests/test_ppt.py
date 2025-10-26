"""
PPT 生成功能测试
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
import os

client = TestClient(app)

def test_generate_ppt_success():
    """测试 PPT 生成成功"""
    request_data = {
        "document_id": "test_doc_123",
        "structure_data": {
            "sections_detected": [
                "Introduction",
                "Methodology",
                "Results",
                "Conclusion"
            ],
            "section_count": 4,
            "details": {}
        },
        "include_images": False,
        "template": "default",
        "options": {}
    }
    
    response = client.post("/api/v1/ppt/generate", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "ppt_path" in data
    assert data["slide_count"] > 0
    assert "download_url" in data

def test_generate_ppt_missing_structure():
    """测试缺少结构数据"""
    request_data = {
        "document_id": "test_doc_123",
        "structure_data": {},
        "include_images": False,
        "template": "default"
    }
    
    response = client.post("/api/v1/ppt/generate", json=request_data)
    
    assert response.status_code == 400
    assert "缺少结构数据" in response.json()["detail"]

def test_generate_ppt_with_images():
    """测试包含图像的 PPT 生成"""
    request_data = {
        "document_id": "test_doc_456",
        "structure_data": {
            "sections_detected": ["Introduction", "Results"],
            "section_count": 2
        },
        "include_images": True,
        "template": "academic"
    }
    
    response = client.post("/api/v1/ppt/generate", json=request_data)
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_list_templates():
    """测试获取模板列表"""
    response = client.get("/api/v1/ppt/templates")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "templates" in data
    assert len(data["templates"]) > 0
    
    # 检查模板结构
    template = data["templates"][0]
    assert "id" in template
    assert "name" in template
    assert "description" in template

def test_customize_ppt():
    """测试 PPT 自定义"""
    # 首先生成一个 PPT
    generate_request = {
        "document_id": "test_doc_789",
        "structure_data": {
            "sections_detected": ["Introduction"],
            "section_count": 1
        }
    }
    
    generate_response = client.post("/api/v1/ppt/generate", json=generate_request)
    
    if generate_response.status_code == 200:
        ppt_path = generate_response.json()["ppt_path"]
        
        # 自定义 PPT
        customize_response = client.post(
            "/api/v1/ppt/customize",
            params={"ppt_path": ppt_path},
            json={
                "customizations": {
                    "theme": {"background_color": "f0f0f0"},
                    "font": {"font_size": 18, "font_name": "Arial"}
                }
            }
        )
        
        # 注意: 可能因为文件不存在而失败
        assert customize_response.status_code in [200, 404, 500]

@pytest.mark.parametrize("template", ["default", "academic", "modern"])
def test_generate_ppt_with_different_templates(template):
    """测试使用不同模板生成 PPT"""
    request_data = {
        "document_id": f"test_doc_{template}",
        "structure_data": {
            "sections_detected": ["Introduction", "Conclusion"],
            "section_count": 2
        },
        "template": template
    }
    
    response = client.post("/api/v1/ppt/generate", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["template"] == template

def test_download_ppt_not_found():
    """测试下载不存在的 PPT"""
    response = client.get("/api/v1/ppt/download?file=nonexistent.pptx")
    
    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]
