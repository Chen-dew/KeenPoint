"""测试 dify_workflow_client"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.clients.dify_workflow_client import (
    analyze_basic,
    analyze_summary,
    upload_files
)

OUTPUT_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\outputs\test_dify_client.json"


def test_analyze_basic():
    """测试基础信息提取"""
    print("=" * 60)
    print("TEST: dify_workflow_client.analyze_basic")
    print("=" * 60)
    
    query = """
    HRank: Filter Pruning using High-Rank Feature Map
    
    Mingbao Lin, Rongrong Ji, Yan Wang, Yichen Zhang, Baochang Zhang, Yonghong Tian, Ling Shao
    
    Abstract
    Neural network pruning offers a promising prospect to facilitate deploying 
    deep neural networks on resource-limited devices.
    """
    
    print(f"\n[输入] {len(query)} 字符")
    result = analyze_basic(query)
    
    print(f"\n[结果]")
    for k, v in result.items():
        if isinstance(v, str) and len(v) > 50:
            print(f"  {k}: {v[:50]}...")
        elif isinstance(v, list):
            print(f"  {k}: {v[:3]}...")
        else:
            print(f"  {k}: {v}")
    
    return result


def test_analyze_summary():
    """测试文本摘要"""
    print("\n" + "=" * 60)
    print("TEST: dify_workflow_client.analyze_summary")
    print("=" * 60)
    
    prompt = """abstract: Neural network pruning offers a promising prospect.

name: 1. Introduction

content: Deep neural networks have achieved great success in various applications.
However, the deployment of DNNs on resource-limited devices remains challenging
due to their high computational cost and memory consumption."""
    
    print(f"\n[输入] {len(prompt)} 字符")
    result = analyze_summary(prompt)
    
    print(f"\n[结果]")
    summary = result.get("summary", "")
    print(f"  summary: {summary[:100]}..." if len(summary) > 100 else f"  summary: {summary}")
    print(f"  key_points: {len(result.get('key_points', []))} 个")
    
    return result


def test_upload_files():
    """测试文件上传"""
    print("\n" + "=" * 60)
    print("TEST: dify_workflow_client.upload_files")
    print("=" * 60)
    
    test_file = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\images")
    images = list(test_file.glob("*.jpg"))[:1]
    
    if not images:
        print("\n[跳过] 无测试图片")
        return []
    
    print(f"\n[测试] 上传 {len(images)} 个文件...")
    results = upload_files([str(p) for p in images])
    
    success = len([r for r in results if r.get("success")])
    print(f"\n[结果] 成功: {success}, 失败: {len(results) - success}")
    
    for r in results:
        name = Path(r.get("file_path", "")).name
        status = r.get("file_id", "")[:20] if r.get("success") else r.get("error", "FAIL")
        print(f"  - {name}: {status}")
    
    return results


def run_all():
    """运行所有测试"""
    results = {
        "analyze_basic": test_analyze_basic(),
        "analyze_summary": test_analyze_summary(),
        "upload_files": test_upload_files()
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[输出] {OUTPUT_FILE}")
    
    return results


if __name__ == "__main__":
    run_all()
