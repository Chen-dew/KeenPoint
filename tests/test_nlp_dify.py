"""测试 NLP 服务 - 使用 Dify 进行文本分析"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import json
from app.services.parse_service import parse_markdown_for_summary
from app.services.nlp_service import extract_and_split_sections, analyze_segments_with_abstract

# 测试文件路径
MD_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\full.md"
JSON_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\9eafd4f2-7e84-4bf8-b8ae-7fd19e07a68b_content_list.json"

print("=" * 70)
print("NLP 服务测试 - Dify 文本分析")
print("=" * 70)

try:
    # 第一步：解析 Markdown 文件
    print("\n步骤 1: 解析 Markdown 文件...")
    parse_result = parse_markdown_for_summary(MD_FILE, JSON_FILE)
    sections = parse_result.get("sections", [])
    print(f"✓ 解析完成，共 {len(sections)} 个章节")
    
    # 第二步：提取并拆分章节
    print("\n步骤 2: 提取并拆分超长章节...")
    segments = extract_and_split_sections(parse_result)
    print(f"✓ 拆分完成，共 {len(segments)} 个片段")
    
    # 显示拆分信息
    split_sections = [s for s in segments if s.get('is_split')]
    if split_sections:
        print(f"  - 有 {len(split_sections)} 个片段是拆分的")
    
    # 只选择第一个非Abstract章节进行测试
    print("\n选择测试章节...")
    test_segments = []
    for segment in segments:
        segment_name = segment.get('name', '').lower()
        if 'abstract' not in segment_name and '摘要' not in segment_name:
            test_segments = [segment]
            print(f"✓ 选择章节: {segment.get('name')}")
            break
    
    if not test_segments:
        test_segments = [segments[0]] if segments else []
        print(f"✓ 未找到非Abstract章节，使用第一个章节")
    
    segments = test_segments
    
    # 第三步：提取摘要（从第一个章节或 Abstract 章节）
    print("\n步骤 3: 提取摘要...")
    abstract = ""
    for section in sections:
        name_lower = section.get('name', '').lower()
        if 'abstract' in name_lower or '摘要' in section.get('name', ''):
            abstract = section.get('content', '')
            print(f"✓ 找到 Abstract 章节，长度: {len(abstract)} 字符")
            break
    
    if not abstract and sections:
        # 如果没有 Abstract，使用第一个章节的内容
        abstract = sections[0].get('content', '')[:500]
        print(f"✓ 未找到 Abstract，使用第一个章节前 500 字符")
    
    # 第四步：使用 Dify 进行文本分析（只测试一个章节）
    print("\n步骤 4: 使用 Dify 进行文本分析...")
    print(f"准备分析 1 个章节: {segments[0].get('name')}\n")
    
    analysis_results = analyze_segments_with_abstract(
        segments=segments,
        abstract=abstract,
        skip_abstract_section=True
    )
    
    print(f"\n✓ 分析完成，共 {len(analysis_results)} 个结果")
    
    # 显示分析结果
    print("\n" + "=" * 70)
    print("分析结果:")
    print("=" * 70)
    
    for i, result in enumerate(analysis_results, 1):
        print(f"\n--- 结果 #{i} ---")
        print(f"ID: {result.get('id')}")
        print(f"章节: {result.get('section_name')}")
        
        summary = result.get('summary', '')
        print(f"\n摘要 ({len(summary)} 字符):")
        print(summary[:200] + "..." if len(summary) > 200 else summary)
        
        key_points = result.get('key_points', [])
        if key_points:
            print(f"\n关键点 ({len(key_points)} 个):")
            for j, point in enumerate(key_points[:3], 1):
                print(f"  {j}. {point}")
        
        if result.get('error'):
            print(f"\n⚠ 错误: {result.get('error')}")
    
    # 保存结果
    output_file = r"D:\MyFiles\AIPPT\Code\keenPoint\outputs\test_nlp_dify_output.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "segments": segments,
            "analysis_results": analysis_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 70}")
    print(f"完整结果已保存到: {output_file}")
    print(f"{'=' * 70}")
    
    # 统计信息
    success_count = len([r for r in analysis_results if not r.get('error')])
    error_count = len([r for r in analysis_results if r.get('error')])
    
    print(f"\n统计:")
    print(f"- 成功分析: {success_count}")
    print(f"- 分析失败: {error_count}")
    print(f"- 总计: {len(analysis_results)}")
    
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
