"""
测试 NLP Service 的章节拆分功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.parse_service import parse_markdown_file
from app.services.nlp_service import extract_and_split_sections, get_segments_summary
import json


def test_section_splitting():
    """测试章节拆分功能"""
    
    print("=" * 80)
    print("NLP Service - 章节拆分功能测试")
    print("=" * 80)
    print()
    
    # 方式1: 使用实际的 Markdown 文件
    # 请根据实际情况修改文件路径
    test_md_files = [
        r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\Lin_HRank_Filter_Pruning_Using_High-Rank_Feature_Map_CVPR_2020_paper\full.md"
    ]
    
    md_file = None
    for test_file in test_md_files:
        if Path(test_file).exists():
            md_file = test_file
            break
    
    if md_file:
        print(f"📄 使用测试文件: {md_file}")
        print()
        
        # 1. 解析 Markdown 文件
        print("步骤 1: 解析 Markdown 文件...")
        parse_result = parse_markdown_file(md_file)
        
        sections = parse_result.get("sections", [])
        print(f"✅ 解析完成，共 {len(sections)} 个章节")
        print()
        
        # 2. 提取并拆分章节
        print("步骤 2: 提取并拆分章节...")
        segments = extract_and_split_sections(parse_result)
        print(f"✅ 拆分完成，共生成 {len(segments)} 个片段")
        print()
        
        # 3. 显示统计信息
        print("步骤 3: 统计信息")
        print("-" * 80)
        summary = get_segments_summary(segments)
        for key, value in summary.items():
            print(f"  {key}: {value}")
        print()
        
        # 4. 显示前几个片段的详细信息
        print("步骤 4: 片段详情（前5个）")
        print("-" * 80)
        for i, segment in enumerate(segments[:5], 1):
            print(f"\n[片段 {i}]")
            print(f"  ID: {segment['id']}")
            print(f"  名称: {segment['name']}")
            print(f"  原始章节索引: {segment['original_section_index']}")
            print(f"  是否拆分: {segment['is_split']}")
            if segment['is_split']:
                print(f"  部分: {segment['part_index']}/{segment['total_parts']}")
            content_preview = segment['content'][:100].replace('\n', ' ')
            print(f"  内容长度: {len(segment['content'])} 字符")
            print(f"  内容预览: {content_preview}...")
        
        if len(segments) > 5:
            print(f"\n... 还有 {len(segments) - 5} 个片段")
        
        # 5. 保存结果到 JSON 文件
        output_file = project_root / "test_segments_output.json"
        print()
        print("步骤 5: 保存结果到文件")
        print("-" * 80)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": summary,
                "segments": segments
            }, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结果已保存到: {output_file}")

if __name__ == "__main__":
    try:
        test_section_splitting()
        print()
        print("=" * 80) 
        print("✅ 测试完成")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n按任意键退出...")
    input()
