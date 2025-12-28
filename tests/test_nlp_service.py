"""测试 nlp_service - 交互式测试"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.document.parse_service import parse_markdown
from app.services.document.nlp_service import (
    analyze_full_document,
    extract_article_basic_info,
    extract_and_split_sections,
    _service
)

# 测试数据
MD_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\full.md"
JSON_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\9eafd4f2-7e84-4bf8-b8ae-7fd19e07a68b_content_list.json"
OUTPUT_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\outputs\test_nlp.json"


def test_extract_basic_info():
    """测试提取基础信息"""
    print("=" * 60)
    print("TEST: nlp_service.extract_article_basic_info")
    print("=" * 60)
    
    parse_result = parse_markdown(MD_FILE, JSON_FILE)
    
    # 先直接调用Dify API获取原始响应
    print("\n[Dify Raw Response]")
    from app.services.clients.dify_workflow_client import analyze_basic
    first_section = parse_result.get("sections", [])[0]
    query = f"{first_section.get('name', '')}\n\n{first_section.get('content', '')}"
    
    try:
        raw_response = analyze_basic(query=query)
        print(f"类型: {type(raw_response)}")
        import json
        print("内容:")
        print(json.dumps(raw_response, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"获取原始响应失败: {e}")
    
    # 调用NLP服务
    print(f"\n[NLP Service 结果]")
    result = extract_article_basic_info(parse_result)
    
    for k, v in result.items():
        if isinstance(v, str) and len(v) > 50:
            print(f"  {k}: {v[:50]}...")
        else:
            print(f"  {k}: {v}")
    
    return result


def test_extract_sections():
    """测试章节拆分"""
    print("\n" + "=" * 60)
    print("TEST: nlp_service.extract_and_split_sections")
    print("=" * 60)
    
    parse_result = parse_markdown(MD_FILE, JSON_FILE)
    segments = extract_and_split_sections(parse_result)
    
    print(f"\n[结果] 共 {len(segments)} 个片段")
    split_count = len([s for s in segments if s.get('is_split')])
    print(f"  拆分片段: {split_count}")
    
    for i, seg in enumerate(segments[:5], 1):
        name = seg.get('name', '')[:40]
        print(f"  {i}. {name} (split={seg.get('is_split', False)})")
    
    return segments


def test_analyze_full_document(section_range=None):
    """测试完整文档分析
    
    Args:
        section_range: 章节范围，如 "3" 或 "2-5" 或 None(全部)
    """
    print("\n" + "=" * 60)
    print("TEST: nlp_service.analyze_full_document")
    print("=" * 60)
    
    parse_result = parse_markdown(MD_FILE, JSON_FILE)
    sections = parse_result.get("sections", [])
    
    # 获取摘要
    abstract = ""
    for sec in sections:
        if "abstract" in sec.get("name", "").lower():
            abstract = sec.get("content", "")
            break
    
    # 解析章节范围
    start_idx, end_idx = 0, len(sections)
    if section_range:
        if "-" in section_range:
            parts = section_range.split("-")
            start_idx = int(parts[0]) - 1
            end_idx = int(parts[1])
        else:
            start_idx = int(section_range) - 1
            end_idx = start_idx + 1
        
        # 边界检查
        start_idx = max(0, min(start_idx, len(sections) - 1))
        end_idx = max(start_idx + 1, min(end_idx, len(sections)))
        
        print(f"\n[范围] 分析第 {start_idx + 1} - {end_idx} 章节 (共{len(sections)}个)")
        
        # 过滤章节
        filtered_sections = sections[start_idx:end_idx]
        parse_result = {**parse_result, "sections": filtered_sections}
    
    print(f"[摘要长度] {len(abstract)} 字符")
    print(f"[章节数量] {len(parse_result.get('sections', []))} 个")
    print("[开始分析] 调用Dify API...")
    
    result = analyze_full_document(parse_result, abstract)
    
    stats = result.get("statistics", {})
    print(f"\n[统计]")
    print(f"  总计: {stats.get('total', 0)}")
    print(f"  分析: {stats.get('analyzed', 0)}")
    print(f"  成功: {stats.get('success', 0)}")
    print(f"  失败: {stats.get('failed', 0)}")
    print(f"  跳过: {stats.get('skipped', 0)}")
    
    # 显示分析结果概要
    analyzed = result.get("analyzed_segments", [])
    if analyzed:
        print(f"\n[分析结果]")
        for seg in analyzed:
            name = seg.get("name", "")[:35]
            summary = seg.get("summary", "")[:40] if seg.get("summary") else "(无)"
            print(f"  - {name}: {summary}...")
    
    # 保存结果（包含raw_response）
    output_file = OUTPUT_FILE
    if section_range:
        output_file = OUTPUT_FILE.replace(".json", f"_sec{section_range}.json")
    
    # 构造完整输出数据
    output_data = {
        "analyzed_segments": result.get("sections_analysis", []),
        "metadata": result.get("metadata", {}),
        "debug_info": {
            "section_range": section_range or "all",
            "total_sections_analyzed": len(result.get("sections_analysis", [])),
            "has_dify_raw_data": "basic_info" in result and "error" not in result.get("basic_info", {})
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\n[输出] {output_file}")
    
    return result


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("NLP Service 测试")
    print("=" * 60)
    print("\n选择测试:")
    print("  1. 提取基础信息 (extract_article_basic_info)")
    print("  2. 章节拆分 (extract_and_split_sections)")
    print("  3. 完整文档分析 (analyze_full_document)")
    print("  4. 运行全部测试")
    print("  0. 退出")
    
    choice = input("\n请输入选项 [0-4]: ").strip()
    
    if choice == "1":
        test_extract_basic_info()
    elif choice == "2":
        test_extract_sections()
    elif choice == "3":
        # 先显示章节列表
        parse_result = parse_markdown(MD_FILE, JSON_FILE)
        sections = parse_result.get("sections", [])
        print(f"\n[章节列表] 共 {len(sections)} 个:")
        for i, sec in enumerate(sections, 1):
            name = sec.get("name", "")[:50]
            print(f"  {i:2d}. {name}")
        
        range_input = input("\n输入章节范围 (如 '3' 或 '2-5', 直接回车=全部): ").strip()
        section_range = range_input if range_input else None
        test_analyze_full_document(section_range)
    elif choice == "4":
        test_extract_basic_info()
        test_extract_sections()
        test_analyze_full_document()
    elif choice == "0":
        print("退出")
    else:
        print("无效选项")
