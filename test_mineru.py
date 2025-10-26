"""
MinerU PDF 解析示例
演示如何使用新的 MinerU API 解析功能
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.parser_service import parse_pdf_with_mineru
from app.core.config import settings
from app.core.logger import logger


async def test_mineru_parsing():
    """测试 MinerU PDF 解析"""
    
    print("=" * 60)
    print("  MinerU PDF 解析测试")
    print("=" * 60)
    print()
    
    # 检查配置
    print(f"📋 MinerU API: {settings.MINERU_API}")
    print(f"🔑 Token: {settings.MINERU_TOKEN[:20]}...")
    print()
    
    # 测试 PDF 文件路径（请替换为实际文件路径）
    pdf_path = "test.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"⚠️ 测试文件不存在: {pdf_path}")
        print("📝 请将 PDF 文件放在项目根目录并命名为 test.pdf")
        print()
        print("或者使用以下代码指定文件路径:")
        print("  pdf_path = r'D:\\path\\to\\your\\file.pdf'")
        return
    
    # 输出文件夹
    output_folder = os.path.join(settings.OUTPUT_DIR, "test_mineru")
    
    try:
        print(f"🚀 开始解析 PDF: {pdf_path}")
        print(f"📁 输出目录: {output_folder}")
        print()
        
        # 调用解析函数
        result_folder = await parse_pdf_with_mineru(pdf_path, output_folder)
        
        print()
        print("=" * 60)
        print("✅ 解析成功!")
        print("=" * 60)
        print()
        print(f"📂 输出目录: {result_folder}")
        print()
        
        # 列出输出文件
        print("📄 生成的文件:")
        for root, dirs, files in os.walk(result_folder):
            level = root.replace(result_folder, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}📁 {os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                print(f"{subindent}📄 {file} ({file_size} bytes)")
        
        # 读取 Markdown 内容预览
        md_files = [f for f in os.listdir(result_folder) if f.endswith('.md')]
        if md_files:
            md_path = os.path.join(result_folder, md_files[0])
            print()
            print("=" * 60)
            print("📝 Markdown 内容预览:")
            print("=" * 60)
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content[:500])
                if len(content) > 500:
                    print("...")
                    print(f"\n(总共 {len(content)} 字符)")
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 解析失败!")
        print("=" * 60)
        print(f"错误信息: {str(e)}")
        logger.error(f"解析失败: {str(e)}", exc_info=True)


async def test_with_custom_pdf():
    """使用自定义 PDF 文件测试"""
    
    print()
    print("=" * 60)
    print("  使用自定义 PDF 文件")
    print("=" * 60)
    print()
    
    # 输入文件路径
    pdf_path = input("请输入 PDF 文件路径: ").strip().strip('"')
    
    if not os.path.exists(pdf_path):
        print(f"❌ 文件不存在: {pdf_path}")
        return
    
    # 输出文件夹
    output_folder = os.path.join(settings.OUTPUT_DIR, "custom_parse")
    
    try:
        print(f"\n🚀 开始解析...")
        result_folder = await parse_pdf_with_mineru(pdf_path, output_folder)
        
        print(f"\n✅ 解析完成!")
        print(f"📂 结果保存在: {result_folder}")
        
    except Exception as e:
        print(f"\n❌ 解析失败: {str(e)}")


if __name__ == "__main__":
    print()
    print("🎯 选择测试模式:")
    print("  1. 使用默认测试文件 (test.pdf)")
    print("  2. 使用自定义 PDF 文件")
    print()
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        asyncio.run(test_mineru_parsing())
    elif choice == "2":
        asyncio.run(test_with_custom_pdf())
    else:
        print("❌ 无效选择")
