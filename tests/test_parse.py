"""
测试 MinerU Parser Service
Run from project root: python test_parser_main.py
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.parser_service import main
from app.core.config import settings
from app.core.logger import logger


async def test_parser():
    """测试解析器主函数"""
    
    print("=" * 80)
    print("MinerU Parser Service Test")
    print("=" * 80)
    
    # 步骤 1: 显示配置
    print("\n[Step 1] Configuration")
    print(f"  Upload URL: {settings.MINERU_UPLOAD_URL}")
    print(f"  Result URL: {settings.MINERU_RESULT_URL}")
    print(f"  Model Version: {settings.MINERU_MODEL_VERSION}")
    print(f"  Poll Interval: {settings.MINERU_POLL_INTERVAL}s")
    print(f"  Download Dir: {settings.MINERU_DOWNLOAD_DIR}")
    print(f"  Token configured: {'✓' if settings.MINERU_API_TOKEN else '✗'}")
    
    # 步骤 2: 获取 PDF 文件路径
    print("\n[Step 2] PDF File Selection")
    print("  Enter PDF file path (or press Enter to use test.pdf):")
    
    pdf_path = input("  > ").strip().strip('"').strip("'")
    
    if not pdf_path:
        pdf_path = "test.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"\n  [ERROR] File not found: {pdf_path}")
        print("\n  Please provide a valid PDF file path.")
        return False
    
    file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
    print(f"\n  [OK] PDF file found")
    print(f"  File: {os.path.basename(pdf_path)}")
    print(f"  Size: {file_size_mb:.2f} MB")
    print(f"  Full path: {os.path.abspath(pdf_path)}")
    
    # 步骤 3: 确认开始处理
    print("\n[Step 3] Processing Confirmation")
    print("  The following operations will be performed:")
    print("    1. Apply for upload URLs from MinerU API")
    print("    2. Upload PDF file to MinerU")
    print("    3. Poll task status until completion")
    print("    4. Download and extract results")
    
    confirm = input("\n  Continue? (y/n, default: y): ").strip().lower() or 'y'
    
    if confirm != 'y':
        print("\n  [CANCELLED] Operation cancelled by user")
        return False
    
    # 步骤 4: 执行解析
    print("\n[Step 4] Parsing PDF")
    print("  " + "-" * 76)
    
    try:
        import time
        start_time = time.time()
        
        # 调用 main 函数
        await main([pdf_path])
        
        elapsed_time = time.time() - start_time
        
        print("  " + "-" * 76)
        print(f"\n  [SUCCESS] Processing completed in {elapsed_time:.2f} seconds")
        
    except Exception as e:
        print(f"\n  [ERROR] Processing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步骤 5: 验证输出
    print("\n[Step 5] Verifying Output")
    
    output_dir = Path(settings.MINERU_DOWNLOAD_DIR)
    
    if not output_dir.exists():
        print(f"  [WARNING] Output directory not found: {output_dir}")
        return True
    
    # 统计文件
    all_files = list(output_dir.rglob("*"))
    files = [f for f in all_files if f.is_file()]
    
    print(f"  Output directory: {output_dir}")
    print(f"  Total files: {len(files)}")
    
    # 文件类型统计
    file_types = {}
    for file in files:
        ext = file.suffix.lower() or "(no extension)"
        file_types[ext] = file_types.get(ext, 0) + 1
    
    print(f"\n  File type distribution:")
    for ext, count in sorted(file_types.items(), key=lambda x: -x[1]):
        print(f"    {ext}: {count} file(s)")
    
    # 列出关键文件
    md_files = list(output_dir.rglob("*.md"))
    json_files = list(output_dir.rglob("*.json"))
    img_dirs = list(output_dir.rglob("images"))
    
    print(f"\n  Key files:")
    print(f"    Markdown files: {len(md_files)}")
    for md in md_files:
        print(f"      - {md.name} ({md.stat().st_size / 1024:.2f} KB)")
    
    print(f"    JSON files: {len(json_files)}")
    for json_file in json_files[:5]:
        print(f"      - {json_file.name}")
    if len(json_files) > 5:
        print(f"      ... and {len(json_files) - 5} more")
    
    print(f"    Image directories: {len(img_dirs)}")
    for img_dir in img_dirs:
        if img_dir.is_dir():
            img_count = len(list(img_dir.glob("*")))
            print(f"      - {img_dir.name}/ ({img_count} images)")
    
    # 步骤 6: 总结
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"  ✓ PDF File: {os.path.basename(pdf_path)}")
    print(f"  ✓ Processing Time: {elapsed_time:.2f}s")
    print(f"  ✓ Output Files: {len(files)}")
    print(f"  ✓ Markdown Files: {len(md_files)}")
    print(f"  ✓ JSON Files: {len(json_files)}")
    
    print("\n" + "=" * 80)
    print("✓ Test completed successfully!")
    print("=" * 80)
    
    return True


async def quick_info():
    """快速显示配置信息"""
    from app.core.config import settings
    
    print("=" * 80)
    print("MinerU Configuration Info")
    print("=" * 80)
    
    print(f"\n[API Configuration]")
    print(f"  Upload URL: {settings.MINERU_UPLOAD_URL}")
    print(f"  Result URL: {settings.MINERU_RESULT_URL}")
    print(f"  Model Version: {settings.MINERU_MODEL_VERSION}")
    print(f"  Poll Interval: {settings.MINERU_POLL_INTERVAL}s")
    
    print(f"\n[Storage Configuration]")
    print(f"  Download Directory: {settings.MINERU_DOWNLOAD_DIR}")
    print(f"  Output Directory: {settings.OUTPUT_DIR}")
    print(f"  Upload Directory: {settings.UPLOAD_DIR}")
    
    print(f"\n[Authentication]")
    if settings.MINERU_API_TOKEN:
        token_preview = settings.MINERU_API_TOKEN[:30] + "..." + settings.MINERU_API_TOKEN[-10:]
        print(f"  Token: {token_preview}")
        print(f"  Token length: {len(settings.MINERU_API_TOKEN)} characters")
        print(f"  Status: ✓ Configured")
    else:
        print(f"  Status: ✗ Not configured")
    
    print(f"\n[Request Headers]")
    headers = settings.MINERU_HEADERS
    for key, value in headers.items():
        if key == "Authorization":
            print(f"  {key}: Bearer {value[7:37]}...{value[-10:]}")
        else:
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 80)


async def menu():
    """主菜单"""
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 24 + "MinerU Parser Service Menu" + " " * 28 + "║")
    print("╚" + "═" * 78 + "╝")
    
    print("\nSelect an option:")
    print("  1. Run full test (parse PDF file)")
    print("  2. View configuration info")
    print("  3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        return await test_parser()
    elif choice == "2":
        await quick_info()
        return True
    elif choice == "3":
        print("\nGoodbye!")
        return None
    else:
        print("\nInvalid choice. Please try again.")
        return True


async def main_loop():
    """主循环"""
    while True:
        result = await menu()
        if result is None:
            break
        
        if result:
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user.")
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()