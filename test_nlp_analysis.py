"""
测试 NLP Service 的章节分析功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.parse_service import parse_markdown_file
from app.services.nlp_service import extract_and_split_sections, analyze_segments_with_abstract
import json


def test_segment_analysis():
    """测试章节分析功能"""
    
    print("=" * 80)
    print("NLP Service - 章节分析功能测试")
    print("=" * 80)
    print()
    
    # 测试文件路径
    test_md_files = [
        r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\Lin_HRank_Filter_Pruning_Using_High-Rank_Feature_Map_CVPR_2020_paper\full.md"
    ]
    
    md_file = None
    for test_file in test_md_files:
        if Path(test_file).exists():
            md_file = test_file
            break
    
    if not md_file:
        print("❌ 未找到测试 Markdown 文件")
        print("请创建测试文件或修改 test_md_files 列表")
        return
    
    print(f"📄 使用测试文件: {md_file}")
    print()
    
    try:
        # 步骤 1: 解析 Markdown 文件
        print("步骤 1: 解析 Markdown 文件...")
        parse_result = parse_markdown_file(md_file)
        sections = parse_result.get("sections", [])
        print(f"✅ 解析完成，共 {len(sections)} 个章节")
        print()
        
        # 步骤 2: 提取摘要
        print("步骤 2: 提取论文摘要...")
        abstract = ""
        for section in sections:
            name = section.get("name", "").lower()
            if "abstract" in name or "摘要" in section.get("name", ""):
                abstract = section.get("content", "")
                print(f"✅ 找到摘要章节: {section.get('name')}")
                print(f"   摘要长度: {len(abstract)} 字符")
                break
        
        if not abstract:
            print("⚠️  未找到摘要章节，使用空摘要")
            abstract = "No abstract available."
        print()
        
        # 步骤 3: 提取并拆分章节
        print("步骤 3: 提取并拆分章节...")
        segments = extract_and_split_sections(parse_result)
        print(f"✅ 拆分完成，共生成 {len(segments)} 个片段")
        
        # 显示拆分信息
        split_sections = {}
        for seg in segments:
            if seg.get('is_split'):
                idx = seg.get('original_section_index')
                if idx not in split_sections:
                    split_sections[idx] = []
                split_sections[idx].append(seg)
        
        if split_sections:
            print(f"   其中 {len(split_sections)} 个章节被拆分:")
            for idx, parts in split_sections.items():
                print(f"     - 章节 {idx}: 拆分为 {len(parts)} 个部分")
        print()
        
        # 步骤 4: 使用 NLP 模型分析章节
        print("步骤 4: 使用 NLP 模型分析章节...")
        print("⏳ 正在调用 NLP API（可能需要较长时间）...")
        print("📌 注意: 拆分章节的后续部分会利用前面部分的分析结果")
        print("-" * 80)
        
        # 分析所有片段
        print(f"📊 将分析全部 {len(segments)} 个片段")
        print()
        
        analysis_results = analyze_segments_with_abstract(
            segments=segments,
            abstract=abstract,
            skip_abstract_section=True
        )
        
        print()
        print(f"✅ 分析完成，共 {len(analysis_results)} 个结果")
        print()
        
        # 步骤 5: 显示分析结果
        print("步骤 5: 分析结果详情")
        print("=" * 80)
        
        for i, result in enumerate(analysis_results, 1):
            print(f"\n[结果 {i}]")
            print(f"ID: {result.get('id')}")
            print(f"章节名称: {result.get('section_name')}")
            
            # 如果有前面部分的摘要，显示
            if result.get('previous_part_summary'):
                print(f"\n📋 前面部分的摘要:")
                prev_summary = result.get('previous_part_summary', '')
                if len(prev_summary) > 200:
                    print(f"  {prev_summary[:200]}...")
                else:
                    print(f"  {prev_summary}")
            
            print(f"\n摘要:")
            summary = result.get('summary', '')
            if len(summary) > 300:
                print(f"  {summary[:300]}...")
            else:
                print(f"  {summary}")
            
            key_points = result.get('key_points', [])
            if key_points:
                print(f"\n关键要点 ({len(key_points)} 个):")
                for idx, point in enumerate(key_points, 1):
                    print(f"  {idx}. {point}")
            else:
                print("\n关键要点: (无)")
            
            if result.get('error'):
                print(f"\n⚠️  错误: {result['error']}")
            
            print("-" * 80)
        
        # 步骤 6: 保存结果到 JSON 文件
        output_file = project_root / "test_analysis_output.json"
        print()
        print("步骤 6: 保存结果到文件")
        print("-" * 80)
        
        output_data = {
            "abstract": abstract[:500] + "..." if len(abstract) > 500 else abstract,
            "total_segments": len(segments),
            "analyzed_segments": len(analysis_results),
            "results": analysis_results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        test_segment_analysis()
        
        print()
        print("=" * 80)
        print("✅ 测试完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n按任意键退出...")
    input()
