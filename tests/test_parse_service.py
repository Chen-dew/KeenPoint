"""
测试 Markdown 解析服务
包括数字层级、表格、公式的识别提取
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.parse_service import parse_markdown_file


def test_markdown_parser():
    """测试 Markdown 解析器 - 完整功能测试（含JSON数据）"""
    
    test_md_path = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\Lin_HRank_Filter_Pruning_Using_High-Rank_Feature_Map_CVPR_2020_paper\full.md"
    test_json_path = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\Lin_HRank_Filter_Pruning_Using_High-Rank_Feature_Map_CVPR_2020_paper\0c19b370-543c-41f6-b855-7ac68a1d0773_content_list.json"
    
    print("=" * 80)
    print("测试 Markdown 解析器 - 完整功能（含JSON结构化数据）")
    print("=" * 80)
    print(f"MD文件: {test_md_path}")
    print(f"JSON文件: {test_json_path}\n")
    
    # 解析内容（带JSON文件）
    result = parse_markdown_file(test_md_path, test_json_path)
    
    # 1. 打印元数据
    print("\n" + "=" * 80)
    print("【文档元数据】")
    print("=" * 80)
    metadata = result["metadata"]
    print(f"  📊 总章节数: {metadata['total_sections']}")
    print(f"  📝 顶层章节: {metadata['top_level_sections']}")
    print(f"  ✏️  总字数: {metadata['total_words']}")
    print(f"  🖼️  图片数量: {metadata['total_figures']}")
    print(f"  🧮 公式数量: {metadata['total_formulas']}")
    print(f"  📋 表格数量: {metadata['total_tables']}")
    
    # 2. 打印图片列表
    print("\n" + "=" * 80)
    print("【图片列表】")
    print("=" * 80)
    for fig in result["figures"][:5]:  # 只显示前5个
        fig_type = fig.get('type', 'N/A')
        print(f"  图片 {fig['id']} (type: {fig_type})")
        print(f"    标题: {fig.get('caption', 'N/A')}")
        print(f"    路径: {fig.get('img_path', 'N/A')}")
    if len(result["figures"]) > 5:
        print(f"  ... 还有 {len(result['figures']) - 5} 个图片")
    
    # 3. 打印公式列表
    print("\n" + "=" * 80)
    print("【公式列表】")
    print("=" * 80)
    for formula in result["formulas"][:3]:  # 只显示前3个
        formula_type = formula.get('type', 'N/A')
        print(f"  公式 {formula['id']} (type: {formula_type})")
        text_preview = formula.get('text', '')[:60].replace('\n', ' ')
        if len(formula.get('text', '')) > 60:
            text_preview += "..."
        print(f"    内容: {text_preview}")
        print(f"    格式: {formula.get('text_format', 'N/A')}")
    if len(result["formulas"]) > 3:
        print(f"  ... 还有 {len(result['formulas']) - 3} 个公式")
    
    # 4. 打印表格列表
    print("\n" + "=" * 80)
    print("【表格列表】")
    print("=" * 80)
    for table in result["tables"][:3]:  # 只显示前3个
        table_type = table.get('type', 'N/A')
        print(f"  表格 {table['id']} (type: {table_type})")
        if table.get('caption'):
            print(f"    标题: {table['caption']}")
        if table.get('img_path'):
            print(f"    截图: {table['img_path']}")
        body_len = len(table.get('body', ''))
        print(f"    HTML长度: {body_len} 字符")
    if len(result["tables"]) > 3:
        print(f"  ... 还有 {len(result['tables']) - 3} 个表格")
    
    # 5. 打印章节扁平结构（包含路径和数字层级）
    print("\n" + "=" * 80)
    print("【章节扁平结构】(数字层级识别 + 路径 + 内嵌对象)")
    print("=" * 80)
    print_sections_flat(result["sections"])
    
    # 6. 验证数字层级
    print("\n" + "=" * 80)
    print("【数字层级验证】")
    print("=" * 80)
    verify_number_levels(result["sections"])
    
    # 7. 验证章节中的对象填充
    print("\n" + "=" * 80)
    print("【章节对象填充验证】")
    print("=" * 80)
    verify_section_objects(result["sections"])
    
    # 保存完整结果到 JSON
    output_path = Path(__file__).parent.parent / "downloads" / "test" / "full_parse_result.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print(f"✅ 完整结果已保存到: {output_path}")
    print("=" * 80)


def print_sections_flat(sections):
    """打印扁平章节结构（参照参考代码格式）"""
    for section in sections:
        # 根据层级添加缩进
        indent = "  " * (section['level'] - 1) if section['level'] > 0 else ""
        level_indicator = "├─" if section['level'] > 1 else "■"
        
        # 显示章节名称（已包含数字编号）
        stats_display = f"[Direct:{section['direct_char_count']} | Total:{section['total_char_count']}]"
        
        print(f"{indent}{level_indicator} {section['name']} {stats_display}")
        
        # 显示路径
        if section.get('path'):
            print(f"{indent}   📍 Path: {section['path']}")
        
        # 显示详细统计信息（只显示ID数组）
        details = []
        if section.get('fig_refs'):
            details.append(f"图片ID:{section['fig_refs']}")
        if section.get('table_refs'):
            details.append(f"表格ID:{section['table_refs']}")
        if section.get('formula_refs'):
            details.append(f"公式ID:{section['formula_refs']}")
        
        if details:
            print(f"{indent}   📊 {', '.join(details)}")


def verify_number_levels(sections):
    """验证数字序号层级是否正确"""
    print("检查数字序号层级...")
    
    issues = []
    correct = []
    
    import re
    number_pattern = re.compile(r'^(\d+(?:\.\d+)*)\s+')
    
    for section in sections:
        name = section['name']
        match = number_pattern.match(name)
        
        if match:
            number = match.group(1)
            number_parts = number.split('.')
            expected_level = len(number_parts)
            actual_level = section['level']
            
            if expected_level == actual_level:
                correct.append(f"✅ {name} - Level {actual_level} 正确")
            else:
                issues.append(f"❌ {name} - 期望Level {expected_level}, 实际Level {actual_level}")
    
    # 显示部分结果
    print(f"\n正确: {len(correct)} 个")
    for item in correct[:5]:
        print(f"  {item}")
    if len(correct) > 5:
        print(f"  ... 还有 {len(correct) - 5} 个正确")
    
    if issues:
        print(f"\n问题: {len(issues)} 个")
        for item in issues[:10]:
            print(f"  {item}")
    else:
        print("\n✅ 所有章节层级都正确！")


def verify_section_objects(sections):
    """验证章节中的图片、表格、公式ID填充"""
    print("检查章节ID填充情况...")
    
    total_sections = len(sections)
    sections_with_images = 0
    sections_with_tables = 0
    sections_with_equations = 0
    
    total_image_refs = 0
    total_table_refs = 0
    total_equation_refs = 0
    
    print("\n章节详细信息：")
    print("-" * 80)
    
    for section in sections:
        fig_refs = section.get('fig_refs', [])
        table_refs = section.get('table_refs', [])
        formula_refs = section.get('formula_refs', [])
        
        if fig_refs:
            sections_with_images += 1
            total_image_refs += len(fig_refs)
        if table_refs:
            sections_with_tables += 1
            total_table_refs += len(table_refs)
        if formula_refs:
            sections_with_equations += 1
            total_equation_refs += len(formula_refs)
        
        # 只显示有内容的章节
        if fig_refs or table_refs or formula_refs:
            print(f"\n📑 {section['name']}")
            
            if fig_refs:
                print(f"  🖼️  图片ID: {fig_refs}")
            
            if table_refs:
                print(f"  📊 表格ID: {table_refs}")
            
            if formula_refs:
                print(f"  🧮 公式ID: {formula_refs}")
    
    # 统计摘要
    print("\n" + "=" * 80)
    print("统计摘要：")
    print(f"  总章节数: {total_sections}")
    print(f"  包含图片的章节: {sections_with_images} 个（共 {total_image_refs} 个引用）")
    print(f"  包含表格的章节: {sections_with_tables} 个（共 {total_table_refs} 个引用）")
    print(f"  包含公式的章节: {sections_with_equations} 个（共 {total_equation_refs} 个引用）")
    
    if total_image_refs == 0 and total_table_refs == 0 and total_equation_refs == 0:
        print("\n⚠️  警告：所有章节的 fig_refs/table_refs/formula_refs 数组都为空！")
        print("   可能原因：")
        print("   1. JSON文件未正确加载")
        print("   2. 章节匹配逻辑有问题")
        print("   3. JSON数据格式不符合预期")
    else:
        print("\n✅ 章节ID填充验证完成！")


if __name__ == "__main__":
    test_markdown_parser()

