"""测试修改后的解析功能"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import json
from app.services.parse_service import parse_markdown_for_summary

# 测试文件路径
MD_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\full.md"
JSON_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\9eafd4f2-7e84-4bf8-b8ae-7fd19e07a68b_content_list.json"

print("=" * 70)
print("解析功能测试")
print("=" * 70)

try:
    # 调用解析函数
    result = parse_markdown_for_summary(MD_FILE, JSON_FILE)
    
    sections = result.get("sections", [])
    metadata = result.get("metadata", {})
    
    print(f"\n解析到 {len(sections)} 个章节\n")
    
    # 显示前 3 个章节的详细信息
    for i, section in enumerate(sections[:3], 1):
        print(f"\n{'=' * 70}")
        print(f"章节 #{i}")
        print(f"{'=' * 70}")
        print(f"标题: {section['name']}")
        print(f"层级: {section['level']}")
        print(f"路径: {section['path']}")
        print(f"内容长度: {len(section['content'])} 字符")
        
        # 检查字段
        print(f"\n字段检查:")
        print(f"- 包含 word_count: {'word_count' in section}")
        print(f"- 包含 direct_char_count: {'direct_char_count' in section}")
        print(f"- 包含 total_char_count: {'total_char_count' in section}")
        
        # 显示图表引用数据
        fig_refs = section.get('fig_refs', [])
        table_refs = section.get('table_refs', [])
        formula_refs = section.get('formula_refs', [])
        
        print(f"\n引用数据:")
        print(f"- 图片引用数: {len(fig_refs)}")
        if fig_refs:
            print(f"  示例: {fig_refs[0]}")
        print(f"- 表格引用数: {len(table_refs)}")
        if table_refs:
            print(f"  示例: {table_refs[0]}")
        print(f"- 公式引用数: {len(formula_refs)}")
        if formula_refs:
            print(f"  示例: {formula_refs[0] if formula_refs else 'N/A'}")
        
        # 显示内容预览
        content_preview = section['content'][:200]
        print(f"\n内容预览:")
        print(f"{content_preview}...")
    
    # 检查返回结果结构
    print(f"\n{'=' * 70}")
    print("返回结果结构检查:")
    print(f"{'=' * 70}")
    print(f"- 包含 sections: {'sections' in result}")
    print(f"- 包含 metadata: {'metadata' in result}")
    print(f"- 包含 figures: {'figures' in result}")
    print(f"- 包含 formulas: {'formulas' in result}")
    print(f"- 包含 tables: {'tables' in result}")
    
    # 保存结果
    output_file = r"D:\MyFiles\AIPPT\Code\keenPoint\outputs\test_parse_output.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n完整结果已保存到: {output_file}")
    
    # 统计信息
    print(f"\n{'=' * 70}")
    print("统计信息:")
    print(f"{'=' * 70}")
    print(f"- 总章节数: {len(sections)}")
    print(f"- Metadata: {metadata}")
    
    # 统计包含引用的章节
    sections_with_figs = sum(1 for s in sections if s.get('fig_refs'))
    sections_with_tables = sum(1 for s in sections if s.get('table_refs'))
    sections_with_formulas = sum(1 for s in sections if s.get('formula_refs'))
    
    print(f"\n包含引用的章节:")
    print(f"- 包含图片引用: {sections_with_figs}")
    print(f"- 包含表格引用: {sections_with_tables}")
    print(f"- 包含公式引用: {sections_with_formulas}")
    
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
