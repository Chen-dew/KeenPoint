"""
测试 MinerU API 客户端
用于测试 PDF 文件上传、解析和下载功能
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.clients.mineru_client import main as mineru_main


async def test_mineru_single_file():
    """测试单个 PDF 文件的解析"""
    
    # 测试文件路径
    test_pdf = r"D:\MyFiles\AIPPT\Data\Lin_HRank_Filter_Pruning_Using_High-Rank_Feature_Map_CVPR_2020_paper.pdf"
    
    if not Path(test_pdf).exists():
        print(f"❌ 测试文件不存在: {test_pdf}")
        print("请修改 test_pdf 变量为您本地的 PDF 文件路径")
        return
    
    print("=" * 60)
    print("测试 MinerU API 客户端")
    print("=" * 60)
    print(f"测试文件: {test_pdf}")
    print()
    
    try:
        # 调用 MinerU 客户端
        await mineru_main([test_pdf])
        
        print("\n" + "=" * 60)
        print("✅ MinerU 解析完成！")
        print("=" * 60)
        print(f"解析结果保存在: downloads/{Path(test_pdf).stem}/")
        print("包含以下文件:")
        print("  - full.md (完整的 Markdown 文档)")
        print("  - images/ (提取的图片)")
        print("  - *.json (结构化数据)")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_mineru_multiple_files():
    """测试多个 PDF 文件的批量解析"""
    
    # 测试文件列表
    test_pdfs = [
        r"D:\MyFiles\AIPPT\Data\paper1.pdf",
        r"D:\MyFiles\AIPPT\Data\paper2.pdf",
    ]
    
    # 过滤出存在的文件
    existing_files = [f for f in test_pdfs if Path(f).exists()]
    
    if not existing_files:
        print("❌ 没有找到可用的测试文件")
        print("请修改 test_pdfs 列表为您本地的 PDF 文件路径")
        return
    
    print("=" * 60)
    print("测试 MinerU API 批量解析")
    print("=" * 60)
    print(f"待解析文件数: {len(existing_files)}")
    for f in existing_files:
        print(f"  - {Path(f).name}")
    print()
    
    try:
        # 调用 MinerU 客户端
        await mineru_main(existing_files)
        
        print("\n" + "=" * 60)
        print("✅ 批量解析完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """主测试函数"""
    print("\n选择测试模式:")
    print("1. 单文件测试")
    print("2. 多文件批量测试")
    
    choice = input("\n请输入选择 (1/2，默认为1): ").strip() or "1"
    
    if choice == "1":
        asyncio.run(test_mineru_single_file())
    elif choice == "2":
        asyncio.run(test_mineru_multiple_files())
    else:
        print("无效选择")


if __name__ == "__main__":
    # 直接运行单文件测试
    asyncio.run(test_mineru_single_file())
    
    # 或使用交互式选择
    # main()
