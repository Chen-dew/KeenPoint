"""
Dify 客户端测试
演示如何使用 Dify API 上传文件
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.clients.dify_client import DifyClient, upload_file_to_dify
from app.core.logger import logger


def test_upload_single_file():
    """测试上传单个文件"""
    print("\n=== 测试上传单个文件 ===")
    
    # 方式1: 使用全局函数
    try:
        # 请替换为实际的文件路径
        test_file = r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\Lin_HRank_Filter_Pruning_Using_High-Rank_Feature_Map_CVPR_2020_paper\images\1cf2462460df74cf363b5722200303ebc33ae885874e4c930aafe237327cc128.jpg"
        
        if not Path(test_file).exists():
            print(f"❌ 测试文件不存在: {test_file}")
            print("请创建测试文件或修改文件路径")
            return
        
        result = upload_file_to_dify(
            file_path=test_file,
            user="test-user-123"
        )
        
        print("✅ 上传成功！")
        print(f"文件 ID: {result.get('id')}")
        print(f"文件名: {result.get('name')}")
        print(f"文件大小: {result.get('size')} bytes")
        print(f"MIME 类型: {result.get('mime_type')}")
        print(f"完整响应: {result}")
        
    except Exception as e:
        print(f"❌ 上传失败: {e}")


def test_upload_with_custom_client():
    """测试使用自定义客户端上传"""
    print("\n=== 测试使用自定义客户端 ===")
    
    try:
        # 使用自定义 API key 创建客户端
        # 注意：需要替换为实际的 API key
        custom_api_key = "your-custom-api-key"
        
        client = DifyClient(
            api_key=custom_api_key,
            user="custom-user"
        )
        
        test_file = "./test_document.pdf"
        
        if not Path(test_file).exists():
            print(f"❌ 测试文件不存在: {test_file}")
            return
        
        result = client.upload_file(test_file)
        print("✅ 上传成功！")
        print(f"文件 ID: {result.get('id')}")
        
    except ValueError as e:
        print(f"⚠️  配置错误: {e}")
        print("请在 config.py 中设置 DIFY_API_KEY 或在代码中提供 API key")
    except Exception as e:
        print(f"❌ 上传失败: {e}")

def test_supported_file_types():
    """测试支持的文件类型"""
    print("\n=== 支持的文件类型 ===")
    
    print("图片类型: png, jpeg, jpg, webp, gif")
    print("文档类型: txt, md, pdf, doc, docx")
    print("\n使用示例:")
    print("  result = upload_file_to_dify('image.png')")
    print("  result = upload_file_to_dify('document.pdf')")


def main():
    """主函数"""
    print("=== Dify 文件上传测试 ===")
    print("\n⚠️  使用前请确保:")
    print("1. 已在 config.py 中设置 DIFY_API_KEY")
    print("2. 已准备好测试文件")
    print("3. 网络连接正常\n")
    
    # 显示支持的文件类型
    test_supported_file_types()
    
    # 取消注释以下行来运行实际测试
    test_upload_single_file()
    
    print("\n提示: 取消注释 main() 函数中的测试函数来运行实际测试")


if __name__ == "__main__":
    main()
