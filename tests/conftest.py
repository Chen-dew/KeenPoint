"""
测试配置文件
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)

@pytest.fixture
def sample_pdf_content():
    """示例 PDF 内容"""
    return b"%PDF-1.4 sample content for testing"

@pytest.fixture
def sample_text():
    """示例论文文本"""
    return """
    Introduction
    This paper presents a novel approach to machine learning.
    
    Methods
    We used a deep learning model with the following architecture.
    
    Results
    Our experiments showed significant improvements.
    
    Discussion
    The results indicate that our approach is effective.
    
    Conclusion
    We have demonstrated the effectiveness of our method.
    """

@pytest.fixture
def sample_structure_data():
    """示例结构数据"""
    return {
        "sections_detected": [
            "Introduction",
            "Methodology",
            "Results",
            "Discussion",
            "Conclusion"
        ],
        "section_count": 5,
        "details": {}
    }
