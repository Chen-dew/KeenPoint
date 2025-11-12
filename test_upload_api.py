"""
测试文件上传 API
"""
import requests
import os
from pathlib import Path

# API 配置
API_URL = "http://localhost:8000/api/v1/upload/"

def test_upload_file(file_path: str):
    """
    测试上传文件到 API
    
    Args:
        file_path: 要上传的文件路径
    """
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    print(f"📤 正在上传文件: {file_path}")
    print(f"🔗 API 地址: {API_URL}")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            response = requests.post(API_URL, files=files)
        
        print(f"\n📊 响应状态码: {response.status_code}")
        
        if response.ok:
            result = response.json()
            print("✅ 上传成功!")
            print(f"\n📋 响应内容:")
            print(f"  状态: {result.get('status')}")
            print(f"  消息: {result.get('message')}")
            
            if 'file_info' in result:
                file_info = result['file_info']
                print(f"\n📄 文件信息:")
                print(f"  文件名: {file_info.get('filename')}")
                print(f"  大小: {file_info.get('file_size_formatted')}")
                print(f"  类型: {file_info.get('file_type')}")
                print(f"  保存路径: {file_info.get('file_path')}")
                print(f"  上传目录: {file_info.get('upload_dir')}")
        else:
            print("❌ 上传失败!")
            print(f"错误信息: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 API 服务器")
        print("请确保后端服务器正在运行 (python -m uvicorn app.main:app --reload)")
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")

def main():
    """主函数"""
    print("=" * 60)
    print("文件上传 API 测试工具")
    print("=" * 60)
    print()
    
    # 测试文件路径（请根据实际情况修改）
    test_files = [
        r"D:\MyFiles\AIPPT\Code\keenPoint\test_sample.pdf",  # 示例 PDF
        r"D:\MyFiles\AIPPT\Code\keenPoint\test_sample.txt",  # 示例 TXT
    ]
    
    # 提示用户输入文件路径
    print("请输入要上传的文件路径（或按 Enter 使用默认测试文件）:")
    user_input = input("> ").strip()
    
    if user_input:
        test_upload_file(user_input)
    else:
        # 使用第一个存在的测试文件
        found = False
        for test_file in test_files:
            if os.path.exists(test_file):
                test_upload_file(test_file)
                found = True
                break
        
        if not found:
            print("\n⚠️  未找到测试文件，请手动输入文件路径")
            file_path = input("文件路径: ").strip()
            if file_path:
                test_upload_file(file_path)

if __name__ == "__main__":
    main()
    print("\n按任意键退出...")
    input()
