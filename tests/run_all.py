"""运行所有测试"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_parse_service import test_parse_markdown
from tests.test_nlp_service import test_extract_basic_info, test_extract_sections
from tests.test_image_service import test_extract_elements
from tests.test_dify_client import test_analyze_basic, test_upload_files


def run_quick_tests():
    """快速测试（不调用耗时API）"""
    print("\n" + "=" * 70)
    print("KEENPOINT 快速测试")
    print("=" * 70)
    
    results = {}
    
    # 1. 解析测试
    try:
        test_parse_markdown()
        results["parse"] = "PASS"
    except Exception as e:
        results["parse"] = f"FAIL: {e}"
    
    # 2. NLP基础测试
    try:
        test_extract_basic_info()
        test_extract_sections()
        results["nlp_extract"] = "PASS"
    except Exception as e:
        results["nlp_extract"] = f"FAIL: {e}"
    
    # 3. 图像提取测试
    try:
        test_extract_elements()
        results["image_extract"] = "PASS"
    except Exception as e:
        results["image_extract"] = f"FAIL: {e}"
    
    # 4. Dify客户端测试
    try:
        test_analyze_basic()
        results["dify_basic"] = "PASS"
    except Exception as e:
        results["dify_basic"] = f"FAIL: {e}"
    
    # 总结
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v == "PASS")
    total = len(results)
    
    for name, status in results.items():
        mark = "✓" if status == "PASS" else "✗"
        print(f"  {mark} {name}: {status}")
    
    print(f"\n  通过: {passed}/{total}")
    
    return results


if __name__ == "__main__":
    run_quick_tests()
