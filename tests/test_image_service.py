"""测试 image_service"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.document.parse_service import parse_markdown
from app.services.document.image_service import extract_elements, analyze_elements

# 测试数据
MD_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\full.md"
JSON_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\9eafd4f2-7e84-4bf8-b8ae-7fd19e07a68b_content_list.json"
BASE_PATH = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104")
OUTPUT_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\outputs\test_image.json"


def test_extract_elements():
    """测试元素提取"""
    print("=" * 60)
    print("TEST: image_service.extract_elements")
    print("=" * 60)
    
    parse_result = parse_markdown(MD_FILE, JSON_FILE)
    elements = extract_elements(parse_result)
    
    # 统计类型
    types = {}
    for elem in elements:
        t = elem.get("element", {}).get("type", "unknown")
        types[t] = types.get(t, 0) + 1
    
    print(f"\n[结果] 共 {len(elements)} 个元素")
    for t, count in types.items():
        print(f"  {t}: {count}")
    
    return elements


def test_analyze_elements():
    """测试元素分析（全部图表公式）
    
    注意: equation类型没有img_path是正常的，使用纯文本分析
    """
    print("\n" + "=" * 60)
    print("TEST: image_service.analyze_elements")
    print("=" * 60)
    
    parse_result = parse_markdown(MD_FILE, JSON_FILE)
    elements = extract_elements(parse_result)
    
    # 按类型分组统计
    type_counts = {}
    has_img_path = {"image": 0, "table": 0, "equation": 0}
    
    for e in elements:
        elem = e.get("element", {})
        elem_type = elem.get("type", "unknown")
        type_counts[elem_type] = type_counts.get(elem_type, 0) + 1
        
        if elem.get("img_path"):
            has_img_path[elem_type] = has_img_path.get(elem_type, 0) + 1
    
    print(f"\n[元素统计] 共 {len(elements)} 个元素:")
    for elem_type, count in type_counts.items():
        with_img = has_img_path.get(elem_type, 0)
        print(f"  {elem_type}: {count} 个 (含图片: {with_img})")
    
    if not elements:
        print("\n[跳过] 无元素")
        return []
    
    print(f"\n[开始分析] 调用Dify API分析所有元素...")
    results = analyze_elements(elements, BASE_PATH)
    
    # 统计结果
    success = len([r for r in results if r.get("analysis")])
    failed = len(results) - success
    
    print(f"\n[统计结果]")
    print(f"  总计: {len(results)}")
    print(f"  成功: {success}")
    print(f"  失败: {failed}")
    
    # 按类型显示分析结果
    print(f"\n[详细结果]")
    for elem_type in ["image", "table", "equation"]:
        type_results = [r for r in results if r.get("element", {}).get("type") == elem_type]
        if not type_results:
            continue
        
        print(f"\n  === {elem_type.upper()} ({len(type_results)} 个) ===")
        for i, r in enumerate(type_results, 1):
            elem = r.get("element", {})
            elem_id = elem.get("id", "?")
            
            if r.get("analysis"):
                analysis = r.get("analysis", {})
                desc = analysis.get("description", "")[:50]
                print(f"  {i}. {elem_type}-{elem_id} ✅")
                
                if elem_type == "image":
                    img_path = elem.get("img_path", "")
                    print(f"     路径: {img_path}")
                    print(f"     描述: {desc}...")
                elif elem_type == "table":
                    print(f"     描述: {desc}...")
                    caption = analysis.get("caption", "")[:40]
                    if caption:
                        print(f"     标题: {caption}...")
                elif elem_type == "equation":
                    eq_text = elem.get("text", "")[:50]
                    print(f"     公式: {eq_text}...")
                    print(f"     描述: {desc}...")
            else:
                error = r.get("error", "未知错误")
                print(f"  {i}. {elem_type}-{elem_id} ❌ {error}")
    
    # 保存结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 完成! 结果已保存: {OUTPUT_FILE}")
    print(f"   文件大小: {Path(OUTPUT_FILE).stat().st_size / 1024:.1f} KB")
    
    return results


if __name__ == "__main__":
    test_extract_elements()
    test_analyze_elements()
