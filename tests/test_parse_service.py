"""测试 parse_service"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.document.parse_service import parse_markdown

# 测试数据
MD_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\full.md"
JSON_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\9eafd4f2-7e84-4bf8-b8ae-7fd19e07a68b_content_list.json"
OUTPUT_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\outputs\test_parse.json"


def test_parse_markdown():
    """测试Markdown解析"""
    print("=" * 60)
    print("TEST: parse_service.parse_markdown")
    print("=" * 60)
    
    result = parse_markdown(MD_FILE, JSON_FILE)
    
    sections = result.get("sections", [])
    metadata = result.get("metadata", {})
    
    print(f"\n[结果]")
    print(f"  章节数: {len(sections)}")
    print(f"  图片数: {metadata.get('total_figures', 0)}")
    print(f"  表格数: {metadata.get('total_tables', 0)}")
    print(f"  公式数: {metadata.get('total_formulas', 0)}")
    
    print(f"\n[章节列表]")
    for i, sec in enumerate(sections[:5], 1):
        print(f"  {i}. {sec.get('name')} (level={sec.get('level')})")
    if len(sections) > 5:
        print(f"  ... 共 {len(sections)} 个章节")
    
    # 保存结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[输出] {OUTPUT_FILE}")
    
    return result


if __name__ == "__main__":
    test_parse_markdown()
