"""测试 MinerU API 客户端
用于测试 PDF 文件上传、解析和下载功能
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.services.clients.mineru_client import main as mineru_main


async def test_mineru_single_file():
    """测试单个 PDF 文件的解析"""
    
    # 测试文件路径
    test_pdf = r"D:\MyFiles\AIPPT\Data\acl20_104.pdf"
    
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

if __name__ == "__main__":
    # 直接运行单文件测试
    asyncio.run(test_mineru_single_file())
