"""测试 Dify Workflow API - 文本分析和图像分析"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import json
from app.services.clients.dify_workflow_client import (
    analyze_summary,
    analyze_images,
    upload_files,
    build_file_inputs
)

print("=" * 80)
print("Dify Workflow API 测试")
print("=" * 80)


def test_analyze_summary():
    """测试文本摘要分析（默认 llm_id=1）"""
    print("\n" + "=" * 80)
    print("测试 1: analyze_summary - 文本摘要分析")
    print("=" * 80)
    
    # 测试文本
    test_content = """
    Introduction
    
    Deep learning has revolutionized computer vision in recent years. Convolutional Neural Networks (CNNs) 
    have achieved remarkable success in image classification, object detection, and semantic segmentation tasks.
    However, these models often require massive computational resources and large amounts of training data.
    
    In this paper, we propose a novel approach to improve the efficiency of CNNs while maintaining high accuracy.
    Our method combines knowledge distillation with network pruning to create compact models suitable for 
    deployment on edge devices. We demonstrate that our approach achieves 95% of the original model's accuracy 
    while reducing the model size by 75% and inference time by 60%.
    """
    
    user_prompt = f"""abstract: Deep learning and CNNs have transformed computer vision but require significant resources.

name: Introduction

content: {test_content.strip()}"""
    
    try:
        print(f"\n输入文本长度: {len(user_prompt)} 字符")
        print("调用 analyze_summary...")
        
        result = analyze_summary(user_prompt=user_prompt, llm_id=1)
        
        print("\n✓ 分析完成!")
        print("\n返回结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 检查结果结构
        if isinstance(result, dict):
            if "section_name" in result:
                print(f"\n章节名称: {result.get('section_name')}")
            if "summary" in result:
                print(f"摘要: {result.get('summary')[:100]}...")
            if "key_points" in result:
                print(f"关键点数量: {len(result.get('key_points', []))}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_analyze_images():
    """测试图像分析（默认 llm_id=2）"""
    print("\n" + "=" * 80)
    print("测试 2: analyze_images - 图像分析")
    print("=" * 80)
    
    # 查找测试图片
    test_dir = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104")
    
    # 查找所有图片文件
    image_files = []
    if test_dir.exists():
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
            image_files.extend(list(test_dir.glob(ext)))
    
    if not image_files:
        print("✗ 未找到测试图片，跳过图像分析测试")
        print(f"  搜索路径: {test_dir}")
        return False
    
    # 选择前2个图片进行测试
    selected_images = image_files[:2]
    
    try:
        print(f"\n找到 {len(image_files)} 个图片文件")
        print(f"选择 {len(selected_images)} 个图片进行测试:")
        for img in selected_images:
            print(f"  - {img.name}")
        
        user_prompt = "请分析这些图片的内容，描述图片中的主要元素和结构。"
        
        print(f"\n提示词: {user_prompt}")
        print("调用 analyze_images...")
        
        result = analyze_images(
            user_prompt=user_prompt,
            image_paths=[str(img) for img in selected_images],
            llm_id=2
        )
        
        print("\n✓ 分析完成!")
        print("\n返回结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_upload_files():
    """测试文件上传功能"""
    print("\n" + "=" * 80)
    print("测试 3: upload_files - 批量上传文件")
    print("=" * 80)
    
    # 查找测试文件
    test_dir = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104")
    
    # 查找图片文件
    image_files = list(test_dir.glob('*.png'))[:2]
    
    if not image_files:
        print("✗ 未找到测试文件，跳过上传测试")
        return False
    
    try:
        print(f"\n准备上传 {len(image_files)} 个文件:")
        for img in image_files:
            print(f"  - {img.name}")
        
        print("\n开始上传...")
        results = upload_files(file_paths=[str(img) for img in image_files])
        
        print("\n✓ 上传完成!")
        print(f"\n上传结果统计:")
        success_count = sum(1 for r in results if r.get('success'))
        print(f"  成功: {success_count}/{len(results)}")
        
        for idx, result in enumerate(results, 1):
            if result.get('success'):
                print(f"  {idx}. {result.get('file_name')} -> {result.get('file_id')}")
            else:
                print(f"  {idx}. 失败: {result.get('error')}")
        
        return success_count > 0
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_build_file_inputs():
    """测试构建文件输入格式"""
    print("\n" + "=" * 80)
    print("测试 4: build_file_inputs - 构建输入格式")
    print("=" * 80)
    
    # 查找测试文件
    test_dir = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104")
    image_files = list(test_dir.glob('*.png'))[:1]
    
    if not image_files:
        print("✗ 未找到测试文件，跳过测试")
        return False
    
    try:
        print(f"\n使用文件: {image_files[0].name}")
        
        print("\n方式1: 自动上传并构建 inputs...")
        inputs = build_file_inputs(
            variable_name="test_images",
            file_paths=[str(img) for img in image_files],
            document_type="image",
            auto_upload=True
        )
        
        print("\n✓ 构建完成!")
        print("\nInputs 格式:")
        print(json.dumps(inputs, ensure_ascii=False, indent=2))
        
        # 验证格式
        assert "test_images" in inputs, "缺少 variable_name 键"
        assert isinstance(inputs["test_images"], list), "值应该是列表"
        assert len(inputs["test_images"]) > 0, "文件列表为空"
        
        first_file = inputs["test_images"][0]
        assert "transfer_method" in first_file, "缺少 transfer_method"
        assert "upload_file_id" in first_file, "缺少 upload_file_id"
        assert "type" in first_file, "缺少 type"
        assert first_file["transfer_method"] == "local_file", "transfer_method 应为 local_file"
        assert first_file["type"] == "image", "type 应为 image"
        
        print("\n✓ 格式验证通过!")
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n开始运行 Workflow API 测试套件...\n")
    
    results = {
        "文本分析": test_analyze_summary(),
        "图像分析": test_analyze_images(),
        "文件上传": test_upload_files(),
        "构建输入": test_build_file_inputs()
    }
    
    print("\n" + "=" * 80)
    print("测试汇总")
    print("=" * 80)
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")


if __name__ == "__main__":
    main()
