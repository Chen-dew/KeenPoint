"""测试 process_document 函数 - 使用真实数据完整流程"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.document.outline_service import process_document
from app.core.logger import logger

# 真实数据路径
MD_FILE = Path(__file__).parent.parent / "downloads" / "acl20_104" / "full.md"
JSON_FILE = Path(__file__).parent.parent / "downloads" / "acl20_104" / "9eafd4f2-7e84-4bf8-b8ae-7fd19e07a68b_content_list.json"
OUTPUT_FILE = Path(__file__).parent.parent / "outputs" / "test_process_document_result.json"


def check_input_files():
    """检查输入文件是否存在"""
    print("=" * 70)
    print("检查输入文件")
    print("=" * 70)
    
    md_exists = MD_FILE.exists()
    json_exists = JSON_FILE.exists()
    
    print(f"\n  Markdown文件: {MD_FILE}")
    print(f"    状态: {'✓ 存在' if md_exists else '✗ 不存在'}")
    if md_exists:
        size_mb = MD_FILE.stat().st_size / 1024 / 1024
        print(f"    大小: {size_mb:.2f} MB")
    
    print(f"\n  JSON文件: {JSON_FILE}")
    print(f"    状态: {'✓ 存在' if json_exists else '✗ 不存在'}")
    if json_exists:
        size_kb = JSON_FILE.stat().st_size / 1024
        print(f"    大小: {size_kb:.1f} KB")
        
        # 显示JSON内容概览
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                print(f"    元素数: {len(data)}")
                # 统计类型
                types = {}
                for item in data:
                    t = item.get("type", "unknown")
                    types[t] = types.get(t, 0) + 1
                print(f"    类型分布: {types}")
        except Exception as e:
            print(f"    解析错误: {e}")
    
    return md_exists and json_exists


def test_process_document():
    """测试完整的文档处理流程"""
    print("\n" + "=" * 70)
    print("测试: process_document (完整流程)")
    print("=" * 70)
    
    # 检查文件
    if not check_input_files():
        print("\n  ❌ 输入文件不完整，无法继续")
        print("\n  提示:")
        print("    1. 确保 downloads/acl20_104/full.md 存在")
        print("    2. 确保 downloads/acl20_104/9eafd4f2-..._content_list.json 存在")
        return None
    
    # 确认执行
    print("\n" + "=" * 70)
    print("准备执行完整流程")
    print("=" * 70)
    print("\n  流程包括:")
    print("    1. 解析 Markdown 文档")
    print("    2. 提取图表公式元素")
    print("    3. 调用 Dify API 分析图表公式")
    print("    4. 调用 Dify API 生成大纲")
    print("\n  ⚠️  注意:")
    print("    - 此过程会调用多次 Dify API")
    print("    - 可能需要 10-30 分钟（取决于文档大小）")
    print("    - 会产生 API 使用费用")
    
    confirm = input("\n  是否继续？(y/n): ").strip().lower()
    if confirm != 'y':
        print("\n  已取消")
        return None
    
    # 开始处理
    print("\n" + "=" * 70)
    print("开始处理...")
    print("=" * 70)
    
    start_time = time.time()
    
    try:
        result = process_document(
            md_path=str(MD_FILE),
            json_path=str(JSON_FILE)
        )
        
        elapsed = time.time() - start_time
        
        # 显示结果
        print("\n" + "=" * 70)
        print("处理完成")
        print("=" * 70)
        
        stats = result.get("statistics", {})
        print(f"\n  统计信息:")
        print(f"    总章节数: {stats.get('sections', 0)}")
        print(f"    提取元素: {stats.get('elements', 0)}")
        print(f"    分析成功: {stats.get('analyzed', 0)}")
        print(f"    大纲章节: {stats.get('outline_total', 0)}")
        print(f"    大纲成功: {stats.get('outline_success', 0)}")
        print(f"    大纲失败: {stats.get('outline_failed', 0)}")
        print(f"    总耗时: {elapsed:.1f} 秒 ({elapsed/60:.1f} 分钟)")
        
        # 详细信息
        if stats.get('outline_failed', 0) > 0:
            print(f"\n  失败的章节:")
            outline = result.get("outline", {})
            for sec in outline.get("sections", []):
                if sec.get("error"):
                    print(f"    - {sec['section_name']}: {sec['error'][:60]}")
        
        # 成功的章节示例
        outline = result.get("outline", {})
        success_sections = [s for s in outline.get("sections", []) if not s.get("error")]
        if success_sections:
            print(f"\n  成功章节示例（前3个）:")
            for idx, sec in enumerate(success_sections[:3], 1):
                print(f"    {idx}. {sec['section_name'][:50]}")
                raw = sec.get("raw_result")
                if isinstance(raw, dict):
                    keys = list(raw.keys())[:3]
                    print(f"       结果键: {keys}")
        
        # 保存结果
        print(f"\n  保存结果...")
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        file_size = OUTPUT_FILE.stat().st_size / 1024 / 1024
        print(f"    ✓ 文件: {OUTPUT_FILE}")
        print(f"    ✓ 大小: {file_size:.2f} MB")
        
        # 保存简化版本（只包含统计信息）
        summary_file = OUTPUT_FILE.parent / "test_process_document_summary.json"
        summary = {
            "md_file": str(MD_FILE),
            "json_file": str(JSON_FILE),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_seconds": elapsed,
            "statistics": stats,
            "outline_sections": [
                {
                    "section_name": s["section_name"],
                    "status": "error" if s.get("error") else "success",
                    "error": s.get("error", None)
                }
                for s in outline.get("sections", [])
            ]
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"    ✓ 摘要: {summary_file}")
        
        print("\n" + "=" * 70)
        print("测试完成")
        print("=" * 70)
        
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        print("\n" + "=" * 70)
        print("处理失败")
        print("=" * 70)
        print(f"\n  错误: {e}")
        print(f"  耗时: {elapsed:.1f} 秒")
        
        import traceback
        print(f"\n  详细错误:")
        traceback.print_exc()
        
        return None


def test_parse_only():
    """仅测试解析部分（不调用API）"""
    print("\n" + "=" * 70)
    print("测试: 仅解析文档（不调用API）")
    print("=" * 70)
    
    from app.services.document.parse_service import parse_markdown
    
    try:
        result = parse_markdown(str(MD_FILE), str(JSON_FILE))
        
        print(f"\n  解析成功:")
        meta = result.get("metadata", {})
        print(f"    总章节: {meta.get('total_sections', 0)}")
        print(f"    总图片: {meta.get('total_figures', 0)}")
        print(f"    总表格: {meta.get('total_tables', 0)}")
        print(f"    总公式: {meta.get('total_formulas', 0)}")
        
        # 显示章节列表
        sections = result.get("sections", [])
        print(f"\n  章节列表:")
        for idx, sec in enumerate(sections[:10], 1):
            print(f"    {idx}. {sec.get('name', 'Unknown')}")
        
        if len(sections) > 10:
            print(f"    ... 还有 {len(sections) - 10} 个章节")
        
        return result
        
    except Exception as e:
        print(f"\n  ❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("process_document 测试工具")
    print("=" * 70)
    print("\n选择测试模式:")
    print("  1. 完整测试 (解析 + 图表分析 + 大纲生成)")
    print("  2. 仅解析测试 (快速验证文档结构)")
    print("  3. 退出")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == "1":
        test_process_document()
    elif choice == "2":
        test_parse_only()
    else:
        print("\n已退出")
