"""测试图文页渲染"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.PowerPoint.layout_service import render_picture_page, save_picture_page

# 示例数据
test_data ={
  "section_index": "01",
  "section_title": "Introduction",
  "slide_title": "Hierarchical Text Classification Overview",
  "paragraphs": [
    "Hierarchical text classification (HTC) is a multi-label classification problem where labels are organized in a hierarchy, such as a tree or directed acyclic graph. It is commonly used in document organization and information retrieval tasks."
  ],
  "bullets": [
    "Multi-label text classification setting",
    "Labels organized in hierarchical structures",
    "Applied to document classification tasks"
  ],
   "image": {
        "src": r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\images\b8f39cac1148ea9ff7206aafcc5c8c228f8e1768d6b1f09f571ec4485e6dba74.jpg",
        "alt": "Hierarchy Structure Example",
        "caption": "Figure 1. Example of a hierarchical label structure used in text classification."
    }
}

def test_render_picture_page():
    """测试渲染图文页"""
    print("=" * 60)
    print("测试渲染图文页")
    print("=" * 60)
    
    # 渲染
    html = render_picture_page(test_data)
    print(f"渲染完成, HTML长度: {len(html)}")
    
    # 保存
    output_path = Path(__file__).parent.parent / "outputs" / "test_picture_page.html"
    save_picture_page(test_data, str(output_path))
    print(f"保存到: {output_path}")
    
    print("=" * 60)
    print("测试完成")


if __name__ == "__main__":
    test_render_picture_page()
