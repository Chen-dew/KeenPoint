"""测试 nlp_service - 完整文档分析"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.document.parse_service import parse_markdown
from app.services.document.nlp_service import analyze_full_document

# 测试数据
MD_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\full.md"
JSON_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\9eafd4f2-7e84-4bf8-b8ae-7fd19e07a68b_content_list.json"
OUTPUT_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\outputs\test_nlp.json"


def test_analyze_full_document():
    """测试完整文档分析"""
    print("=" * 60)
    print("NLP Service - 完整文档分析")
    print("=" * 60)
    
    # 解析文档
    print("\n[步骤1] 解析文档...")
    parse_result = parse_markdown(MD_FILE, JSON_FILE)
    sections = parse_result.get("sections", [])
    print(f"  章节总数: {len(sections)}")
    
    # 获取摘要
    abstract = ""
    for sec in sections:
        if "abstract" in sec.get("name", "").lower():
            abstract = sec.get("content", "")
            break
    print(f"  摘要长度: {len(abstract)} 字符")
    
    # 分析全部文档
    print("\n[步骤2] 调用NLP分析...")
    result = analyze_full_document(parse_result, abstract)
    
    # 显示统计
    stats = result.get("statistics", {})
    print(f"\n[统计结果]")
    print(f"  总章节: {stats.get('total', 0)}")
    print(f"  已分析: {stats.get('analyzed', 0)}")
    print(f"  成功: {stats.get('success', 0)}")
    print(f"  失败: {stats.get('failed', 0)}")
    print(f"  跳过: {stats.get('skipped', 0)}")
    
    # 显示基础信息
    basic_info = result.get("basic_info", {})
    print(f"\n[基础信息]")
    print(f"  标题: {basic_info.get('title', '(无)')[:60]}")
    print(f"  作者: {len(basic_info.get('authors', []))} 人")
    print(f"  机构: {basic_info.get('affiliation', '(无)')[:60]}")
    
    # 显示分析结果摘要
    analyzed = result.get("sections_analysis", [])
    if analyzed:
        print(f"\n[章节分析] 共 {len(analyzed)} 个:")
        for i, seg in enumerate(analyzed[:5], 1):
            name = seg.get("section_name", "")[:40]
            summary = seg.get("summary", "")[:50] if seg.get("summary") else "(无)"
            print(f"  {i}. {name}")
            print(f"     {summary}...")
        if len(analyzed) > 5:
            print(f"  ... 还有 {len(analyzed) - 5} 个章节")
    
    # 保存结果
    print(f"\n[步骤3] 保存结果...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 完成! 结果已保存: {OUTPUT_FILE}")
    print(f"   文件大小: {Path(OUTPUT_FILE).stat().st_size / 1024:.1f} KB")
    
    return result


if __name__ == "__main__":
    test_analyze_full_document()
