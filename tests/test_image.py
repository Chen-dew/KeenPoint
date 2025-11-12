"""
测试图像服务中的视觉元素提取功能
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径（修正为父目录）
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.image_service import (
    extract_visual_elements,
    extract_visual_elements_from_folder,
    save_visual_elements,
    get_visual_element_paths,
    generate_visual_summary
)


async def test_single_file():
    """测试单个文件的视觉元素提取"""
    print("=" * 80)
    print("Test 1: Extract from single content_list.json")
    print("=" * 80)
    
    # 测试文件路径
    test_file = "downloads/test/3396fb95-d363-4e84-be95-ec3436b6324b_content_list.json"
    
    if not os.path.exists(test_file):
        print(f"\n[ERROR] Test file not found: {test_file}")
        return
    
    print(f"\nProcessing: {test_file}")
    
    # 提取视觉元素
    elements = await extract_visual_elements(test_file)
    
    print(f"\n[Results]")
    print(f"  Total elements extracted: {len(elements)}")
    
    # 显示前几个元素
    if elements:
        print(f"\n[Sample Elements] (first 3):")
        for i, element in enumerate(elements[:3], 1):
            print(f"\n  Element {i}:")
            print(f"    Type: {element.get('type')}")
            print(f"    Page: {element.get('page_idx')}")
            print(f"    Path: {element.get('img_path', 'N/A')}")
            
            # 显示额外信息
            if element['type'] == 'image':
                caption = element.get('image_caption', [])
                print(f"    Caption: {caption[0] if caption else 'N/A'}")
            elif element['type'] == 'table':
                caption = element.get('table_caption', [])
                print(f"    Caption: {caption[0] if caption else 'N/A'}")
            elif element['type'] == 'equation':
                text = element.get('text', '')
                print(f"    Text: {text[:50]}..." if len(text) > 50 else f"    Text: {text}")
        
        if len(elements) > 3:
            print(f"\n  ... and {len(elements) - 3} more elements")
    
    # 保存到文件
    output_file = "downloads/test/visual_elements.json"
    success = await save_visual_elements(elements, output_file)
    
    if success:
        print(f"\n[Saved] Visual elements saved to: {output_file}")
    
    return elements


async def test_folder_extraction():
    """测试文件夹中所有文件的提取"""
    print("\n\n" + "=" * 80)
    print("Test 2: Extract from entire folder")
    print("=" * 80)
    
    folder = "downloads"
    
    if not os.path.exists(folder):
        print(f"\n[ERROR] Folder not found: {folder}")
        return
    
    print(f"\nScanning folder: {folder}")
    
    # 提取所有文件
    results = await extract_visual_elements_from_folder(folder)
    
    print(f"\n[Results]")
    print(f"  Total files processed: {len(results)}")
    
    total_elements = 0
    for filename, elements in results.items():
        print(f"\n  File: {filename}")
        print(f"    Elements: {len(elements)}")
        total_elements += len(elements)
    
    print(f"\n  Total elements across all files: {total_elements}")
    
    return results


async def test_visual_summary(elements):
    """测试生成视觉元素摘要"""
    print("\n\n" + "=" * 80)
    print("Test 3: Generate visual summary")
    print("=" * 80)
    
    summary = await generate_visual_summary(elements)
    
    print(f"\n[Summary Statistics]")
    print(f"  Total Elements: {summary['total_count']}")
    
    print(f"\n  By Type:")
    for type_name, count in summary['by_type'].items():
        print(f"    {type_name}: {count}")
    
    print(f"\n  By Page:")
    for page, count in sorted(summary['by_page'].items()):
        print(f"    Page {page}: {count} element(s)")
    
    print(f"\n  With Caption: {summary['with_caption']}")
    print(f"  With Footnote: {summary['with_footnote']}")
    
    # 保存摘要
    summary_file = "downloads/test/visual_summary.json"
    await save_visual_elements([summary], summary_file)
    print(f"\n[Saved] Summary saved to: {summary_file}")
    
    return summary


async def test_file_paths(elements):
    """测试获取文件路径"""
    print("\n\n" + "=" * 80)
    print("Test 4: Get visual element file paths")
    print("=" * 80)
    
    base_folder = "downloads/test"
    
    paths = await get_visual_element_paths(elements, base_folder)
    
    print(f"\n[File Paths]")
    
    for category, file_list in paths.items():
        print(f"\n  {category.upper()} ({len(file_list)}):")
        for i, path in enumerate(file_list[:3], 1):
            print(f"    {i}. {Path(path).name}")
        
        if len(file_list) > 3:
            print(f"    ... and {len(file_list) - 3} more")
    
    return paths


async def test_detailed_analysis(elements):
    """详细分析视觉元素"""
    print("\n\n" + "=" * 80)
    print("Test 5: Detailed analysis")
    print("=" * 80)
    
    # 按类型分组
    by_type = {'image': [], 'table': [], 'equation': []}
    
    for element in elements:
        element_type = element.get('type')
        if element_type in by_type:
            by_type[element_type].append(element)
    
    # 分析每种类型
    for element_type, items in by_type.items():
        if not items:
            continue
        
        print(f"\n[{element_type.upper()} Analysis]")
        print(f"  Count: {len(items)}")
        
        # 统计有 caption 的数量
        with_caption = 0
        caption_key = f'{element_type}_caption' if element_type in ['image', 'table'] else None
        
        if caption_key:
            with_caption = sum(1 for item in items if item.get(caption_key))
            print(f"  With caption: {with_caption}")
        
        # 显示示例
        if items:
            print(f"\n  Example:")
            item = items[0]
            print(f"    Page: {item.get('page_idx')}")
            print(f"    Path: {item.get('img_path')}")
            
            if element_type == 'image' and item.get('image_caption'):
                print(f"    Caption: {item['image_caption'][0][:100]}...")
            elif element_type == 'table' and item.get('table_caption'):
                print(f"    Caption: {item['table_caption'][0][:100]}...")
            elif element_type == 'equation' and item.get('text'):
                print(f"    Formula: {item['text'][:100]}...")


async def main():
    """主测试函数"""
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 22 + "Visual Elements Extraction Test" + " " * 25 + "║")
    print("╚" + "═" * 78 + "╝")
    
    try:
        # 测试 1: 单文件提取
        elements = await test_single_file()
        
        if not elements:
            print("\n[WARNING] No elements extracted, skipping remaining tests")
            return
        
        # 测试 2: 文件夹提取
        await test_folder_extraction()
        
        # 测试 3: 生成摘要
        await test_visual_summary(elements)
        
        # 测试 4: 获取文件路径
        await test_file_paths(elements)
        
        # 测试 5: 详细分析
        await test_detailed_analysis(elements)
        
        print("\n" + "=" * 80)
        print("✓ All tests completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())