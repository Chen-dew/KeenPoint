"""测试批量文件上传功能"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.services.clients.dify_client import upload_files_batch, get_image_client
from app.core.logger import logger


def test_batch_upload():
    """测试批量上传图片文件"""
    print("=" * 70)
    print("批量文件上传测试")
    print("=" * 70)
    
    # 设置测试文件路径（请根据实际情况修改）
    base_dir = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\Lin_HRank_Filter_Pruning_Using_High-Rank_Feature_Map_CVPR_2020_paper\images")
    
    if not base_dir.exists():
        print(f"测试目录不存在: {base_dir}")
        print("请修改 base_dir 为您本地的图片目录路径")
        return
    
    # 获取目录下的所有图片文件
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    image_files = [f for f in base_dir.iterdir() if f.suffix.lower() in image_extensions]
    
    if not image_files:
        print(f"未找到图片文件: {base_dir}")
        return
    
    # 限制测试数量（避免上传太多）
    max_test_files = 5
    test_files = image_files[:max_test_files]
    
    print(f"\n找到 {len(image_files)} 个图片文件")
    print(f"测试上传前 {len(test_files)} 个文件:\n")
    
    for idx, file_path in enumerate(test_files, 1):
        print(f"  {idx}. {file_path.name}")
    
    print("\n开始批量上传...\n")
    
    try:
        # 使用全局函数
        results = upload_files_batch(
            file_paths=test_files,
            use_image_client=True,
            continue_on_error=True
        )
        
        # 显示结果
        print("\n" + "=" * 70)
        print("上传结果汇总")
        print("=" * 70)
        
        success_count = 0
        failed_count = 0
        
        for idx, result in enumerate(results, 1):
            print(f"\n{idx}. {Path(result['file_path']).name}")
            
            if result['success']:
                success_count += 1
                print(f"   成功")
                print(f"   文件 ID: {result['file_id']}")
                print(f"   文件名: {result['file_name']}")
            else:
                failed_count += 1
                print(f"   ❌ 失败")
                print(f"   错误: {result['error']}")
        
        print("\n" + "=" * 70)
        print(f"总计: {len(results)} 个文件")
        print(f"成功: {success_count}")
        print(f"失败: {failed_count}")
        print("=" * 70)
        
        # 返回成功上传的文件ID列表
        file_ids = [r['file_id'] for r in results if r['success']]
        if file_ids:
            print(f"\n成功上传的文件 ID:")
            for file_id in file_ids:
                print(f"  - {file_id}")
        
    except Exception as e:
        print(f"\n❌ 批量上传失败: {e}")
        import traceback
        traceback.print_exc()


def test_batch_upload_with_client():
    """使用客户端直接进行批量上传测试"""
    print("\n" + "=" * 70)
    print("使用客户端直接批量上传测试")
    print("=" * 70)
    
    base_dir = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\Lin_HRank_Filter_Pruning_Using_High-Rank_Feature_Map_CVPR_2020_paper\images")
    
    if not base_dir.exists():
        print(f"❌ 测试目录不存在: {base_dir}")
        return
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    image_files = [f for f in base_dir.iterdir() if f.suffix.lower() in image_extensions][:3]
    
    if not image_files:
        print(f"❌ 未找到图片文件")
        return
    
    print(f"\n测试上传 {len(image_files)} 个文件\n")
    
    try:
        client = get_image_client()
        results = client.upload_files_batch(
            file_paths=image_files,
            continue_on_error=True
        )
        
        print("\n上传完成!")
        for result in results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {Path(result['file_path']).name}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 测试方式1: 使用全局函数
    test_batch_upload()
    
    # 测试方式2: 使用客户端
    # test_batch_upload_with_client()
