"""测试 layout_service - 标题页模板渲染"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.document.parse_service import parse_markdown
from app.services.PowerPoint.layout_service import (
    render_title_page,
    render_title_page_from_parse_result,
    save_title_page
)

# 测试数据
MD_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\full.md"
JSON_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\9eafd4f2-7e84-4bf8-b8ae-7fd19e07a68b_content_list.json"
OUTPUT_DIR = r"D:\MyFiles\AIPPT\Code\keenPoint\outputs"


def test_render_title_page():
    """测试标题页渲染"""
    print("=" * 60)
    print("TEST: layout_service.render_title_page")
    print("=" * 60)
    
    # 模拟基础信息
    basic_info = {
        "title": "Hierarchy-Aware Global Model for Hierarchical Text Classification",
        "subtitle": "A Novel Approach to Multi-Level Document Analysis",
        "authors": ["Jie Zhou", "Chunping Ma", "Dingkun Long", "Guangwei Xu"],
        "affiliation": "Shanghai Jiao Tong University, Alibaba Group",
        "date": "2023-12-19"
    }
    
    print(f"[输入数据]")
    print(f"  标题: {basic_info['title'][:50]}...")
    print(f"  作者: {len(basic_info['authors'])} 人")
    print(f"  机构: {basic_info['affiliation'][:50]}...")
    
    html_content = render_title_page(basic_info)
    
    print(f"\n[渲染结果]")
    print(f"  HTML长度: {len(html_content)} 字符")
    print(f"  包含标题: {'{{ title }}' not in html_content}")
    print(f"  包含作者: {basic_info['authors'][0] in html_content}")
    
    # 保存到文件
    output_file = f"{OUTPUT_DIR}/test_title_page.html"
    save_title_page(basic_info, output_file)
    print(f"\n[保存] {output_file}")
    
    return html_content


def test_render_from_parse_result():
    """测试从解析结果渲染标题页"""
    print("\n" + "=" * 60)
    print("TEST: layout_service.render_title_page_from_parse_result")
    print("=" * 60)
    
    # 解析文档
    parse_result = parse_markdown(MD_FILE, JSON_FILE)
    print(f"[解析结果] {len(parse_result.get('sections', []))} 个章节")
    
    # 渲染标题页
    html_content = render_title_page_from_parse_result(parse_result)
    
    print(f"\n[渲染结果]")
    print(f"  HTML长度: {len(html_content)} 字符")
    
    # 检查关键内容
    if "Hierarchy-Aware" in html_content:
        print("  ✅ 包含正确标题")
    else:
        print("  ❌ 标题渲染失败")
    
    if "Jie Zhou" in html_content:
        print("  ✅ 包含作者信息")
    else:
        print("  ❌ 作者渲染失败")
    
    # 保存到文件
    output_file = f"{OUTPUT_DIR}/test_title_page_from_parse.html"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"\n[保存] {output_file}")
    
    return html_content


if __name__ == "__main__":
    print("\n选择测试:")
    print("  1. 测试基础渲染 (模拟数据)")
    print("  2. 测试从解析结果渲染")
    print("  3. 运行全部测试")
    print("  0. 退出")
    
    choice = input("\n请输入选项 [0-3]: ").strip()
    
    if choice == "1":
        test_render_title_page()
    elif choice == "2":
        test_render_from_parse_result()
    elif choice == "3":
        test_render_title_page()
        test_render_from_parse_result()
    elif choice == "0":
        print("退出")
    else:
        print("无效选项")