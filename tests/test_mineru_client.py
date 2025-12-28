"""测试 mineru_client"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.clients.mineru_client import process_sync

OUTPUT_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\outputs\test_mineru.json"


def test_process_files():
    """测试PDF处理（需要有PDF文件）"""
    print("=" * 60)
    print("TEST: mineru_client.process_sync")
    print("=" * 60)
    
    # 查找测试PDF
    test_pdfs = list(Path(r"D:\MyFiles\AIPPT\Code\keenPoint\uploads").rglob("*.pdf"))
    
    if not test_pdfs:
        print("\n[跳过] 无测试PDF文件")
        print("  请在 uploads/ 目录放置PDF文件后重试")
        return {"status": "skipped", "reason": "No PDF files"}
    
    test_file = str(test_pdfs[0])
    print(f"\n[测试文件] {test_file}")
    print("\n[警告] 此测试会调用MinerU API并下载结果，可能需要较长时间")
    
    confirm = input("是否继续? (y/n): ")
    if confirm.lower() != 'y':
        print("[取消]")
        return {"status": "cancelled"}
    
    print("\n[开始处理]...")
    results = process_sync([test_file])
    
    print(f"\n[结果] {len(results)} 个文件")
    for r in results:
        print(f"  - {r.get('file_name')}: {r.get('state')}")
    
    # 保存结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[输出] {OUTPUT_FILE}")
    
    return results


if __name__ == "__main__":
    test_process_files()
