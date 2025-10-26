"""
结构分析功能测试
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_analyze_structure_success():
    """测试结构分析成功"""
    sample_text = """
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
    
    response = client.post(
        "/api/v1/analysis/structure",
        json={"text": sample_text, "options": {}}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "sections_detected" in data
    assert data["section_count"] > 0
    
    # 检查是否检测到了主要章节
    sections = data["sections_detected"]
    assert any("Introduction" in s for s in sections)
    assert any("Method" in s or "Conclusion" in s for s in sections)

def test_analyze_structure_short_text():
    """测试文本过短的情况"""
    short_text = "This is too short"
    
    response = client.post(
        "/api/v1/analysis/structure",
        json={"text": short_text, "options": {}}
    )
    
    assert response.status_code == 400
    assert "过短" in response.json()["detail"]

def test_analyze_structure_empty_text():
    """测试空文本"""
    response = client.post(
        "/api/v1/analysis/structure",
        json={"text": "", "options": {}}
    )
    
    assert response.status_code == 422  # 验证错误

def test_extract_keywords():
    """测试关键词提取"""
    sample_text = """
    Machine learning is a subset of artificial intelligence. 
    Deep learning models are used for complex pattern recognition.
    Neural networks are trained using large datasets.
    """
    
    response = client.post(
        "/api/v1/analysis/keywords",
        params={"text": sample_text, "top_n": 5}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "keywords" in data
    assert len(data["keywords"]) > 0

def test_generate_summary():
    """测试摘要生成"""
    sample_text = """
    This research introduces a new method for natural language processing.
    We developed an innovative algorithm that improves accuracy.
    Our experiments demonstrate significant improvements over baseline methods.
    The results suggest that this approach is highly effective.
    Future work will focus on extending this method to other domains.
    """
    
    response = client.post(
        "/api/v1/analysis/summary",
        params={"text": sample_text, "max_length": 100}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "summary" in data
    assert len(data["summary"]) > 0
    assert data["length"] <= 200  # 允许一些误差

@pytest.mark.parametrize("section_keyword", [
    "introduction",
    "methods",
    "results",
    "discussion",
    "conclusion"
])
def test_detect_specific_sections(section_keyword):
    """测试检测特定章节"""
    text = f"""
    {section_keyword.capitalize()}
    This is the {section_keyword} section of the paper.
    It contains important information about the research.
    """
    
    response = client.post(
        "/api/v1/analysis/structure",
        json={"text": text, "options": {}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # 检查是否检测到了该章节
    detected = any(section_keyword.lower() in s.lower() for s in data["sections_detected"])
    assert detected, f"Failed to detect {section_keyword} section"
