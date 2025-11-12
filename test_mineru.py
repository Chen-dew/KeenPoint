"""
完整测试 MinerU API 解析功能
测试 PDF 上传、解析、Markdown 提取、标题树生成
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.parser_service import (
    parse_pdf_with_mineru,
    extract_heading_tree_from_file,
    get_tree_structure,
    count_markdown_chunks
)
from app.core.config import settings
from app.core.logger import logger


async def test_mineru_api():
    """测试 MinerU API 完整流程"""
    
    print("=" * 80)
    print("MinerU API Complete Test")
    print("=" * 80)
    
    # 步骤 1: 检查配置
    print("\n[Step 1] Checking configuration...")
    print(f"  MINERU_API: {settings.MINERU_API}")
    print(f"  MINERU_TOKEN: {settings.MINERU_TOKEN[:50]}..." if settings.MINERU_TOKEN else "  MINERU_TOKEN: Not set")
    print(f"  OUTPUT_DIR: {settings.OUTPUT_DIR}")
    
    if not settings.MINERU_API or not settings.MINERU_TOKEN:
        print("\n[ERROR] MinerU API or Token not configured!")
        return
    
    # 步骤 2: 准备测试 PDF 文件
    print("\n[Step 2] Preparing test PDF file...")
    
    # 方式 1: 使用示例 PDF（如果有）
    test_pdf_path = "test.pdf"
    
    if not test_pdf_path or not os.path.exists(test_pdf_path):
        print("\n[INFO] No valid PDF file provided. Creating a dummy test...")
        print("Please provide a real PDF file to test the full functionality.")
        return
    
    print(f"  Using PDF: {test_pdf_path}")
    print(f"  File size: {os.path.getsize(test_pdf_path) / 1024:.2f} KB")
    
    # 步骤 3: 调用 MinerU API 解析
    print("\n[Step 3] Calling MinerU API to parse PDF...")
    
    output_folder = os.path.join(settings.OUTPUT_DIR, "test_mineru_output")
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        extracted_folder = await parse_pdf_with_mineru(test_pdf_path, output_folder)
        print(f"  [SUCCESS] PDF parsed successfully!")
        print(f"  Output folder: {extracted_folder}")
    except Exception as e:
        print(f"  [ERROR] PDF parsing failed: {str(e)}")
        return
    
    # 步骤 4: 检查解析结果
    print("\n[Step 4] Checking extracted files...")
    
    if not os.path.exists(extracted_folder):
        print(f"  [ERROR] Output folder not found: {extracted_folder}")
        return
    
    files = os.listdir(extracted_folder)
    print(f"  Total files extracted: {len(files)}")
    
    # 查找 Markdown 文件
    md_files = [f for f in files if f.endswith('.md')]
    print(f"  Markdown files: {len(md_files)}")
    for md_file in md_files:
        md_path = os.path.join(extracted_folder, md_file)
        file_size = os.path.getsize(md_path)
        print(f"    - {md_file} ({file_size / 1024:.2f} KB)")
    
    # 查找图像文件夹
    images_folder = os.path.join(extracted_folder, "images")
    if os.path.exists(images_folder):
        image_files = [f for f in os.listdir(images_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        print(f"  Image files: {len(image_files)}")
        for i, img_file in enumerate(image_files[:5]):  # 只显示前 5 个
            print(f"    - {img_file}")
        if len(image_files) > 5:
            print(f"    ... and {len(image_files) - 5} more images")
    else:
        print(f"  Image folder not found")
    
    # 步骤 5: 读取并分析 Markdown 内容
    if md_files:
        print("\n[Step 5] Analyzing Markdown content...")
        
        md_path = os.path.join(extracted_folder, md_files[0])
        
        with open(md_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        print(f"  Total characters: {len(markdown_content)}")
        print(f"  Total lines: {markdown_content.count(chr(10)) + 1}")
        
        # 显示前 500 字符预览
        print("\n  Content preview (first 500 chars):")
        print("  " + "-" * 70)
        preview = markdown_content[:500].replace('\n', '\n  ')
        print(f"  {preview}")
        if len(markdown_content) > 500:
            print("  ...")
        print("  " + "-" * 70)
        
        # 步骤 6: 统计标题
        print("\n[Step 6] Counting headings...")
        
        chunks = count_markdown_chunks(markdown_content)
        print(f"  Total headings: {len(chunks)}")
        
        if chunks:
            level_counts = {}
            for chunk in chunks:
                level = chunk['level']
                level_counts[level] = level_counts.get(level, 0) + 1
            
            print("  Heading distribution:")
            for level in sorted(level_counts.keys()):
                print(f"    Level {level} ({'#' * level}): {level_counts[level]} headings")
        
        # 步骤 7: 生成标题树
        print("\n[Step 7] Generating heading tree structure...")
        
        tree_with_tags = await get_tree_structure(markdown_content, add_tag=True)
        print("\n  Tree structure (with tags):")
        print("  " + "-" * 70)
        for line in tree_with_tags.split('\n')[:15]:  # 只显示前 15 行
            print(f"  {line}")
        if tree_with_tags.count('\n') > 15:
            print(f"  ... and {tree_with_tags.count(chr(10)) - 14} more lines")
        print("  " + "-" * 70)
        
        tree_plain = await get_tree_structure(markdown_content, add_tag=False)
        print("\n  Tree structure (plain):")
        print("  " + "-" * 70)
        for line in tree_plain.split('\n')[:15]:
            print(f"  {line}")
        if tree_plain.count('\n') > 15:
            print(f"  ... and {tree_plain.count(chr(10)) - 14} more lines")
        print("  " + "-" * 70)
        
        # 步骤 8: 提取嵌套树形结构
        print("\n[Step 8] Extracting nested heading tree...")
        
        heading_tree = await extract_heading_tree_from_file(md_path)
        print(f"  Root nodes: {len(heading_tree)}")
        
        def print_tree(nodes, indent=0):
            """递归打印树形结构"""
            for node in nodes:
                prefix = "  " * indent
                print(f"  {prefix}- Level {node['level']}: {node['title']} "
                      f"(Line {node['line']}, {node['char_count']} chars)")
                if node['children']:
                    print_tree(node['children'], indent + 1)
        
        print("\n  Nested tree structure:")
        print("  " + "-" * 70)
        print_tree(heading_tree)
        print("  " + "-" * 70)
    
    # 步骤 9: 生成测试报告
    print("\n[Step 9] Test Summary")
    print("=" * 80)
    print(f"  PDF File: {os.path.basename(test_pdf_path)}")
    print(f"  Output Folder: {extracted_folder}")
    print(f"  Markdown Files: {len(md_files)}")
    
    if os.path.exists(images_folder):
        image_count = len([f for f in os.listdir(images_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        print(f"  Images Extracted: {image_count}")
    
    if md_files:
        print(f"  Total Headings: {len(chunks)}")
        print(f"  Root Sections: {len(heading_tree)}")
        print(f"  Content Length: {len(markdown_content)} characters")
    
    print("\n" + "=" * 80)
    print("Test completed successfully!")
    print("=" * 80)

def main():
    """主函数 - 运行异步测试"""
    try:
        asyncio.run(test_mineru_api())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
