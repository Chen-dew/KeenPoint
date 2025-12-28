"""测试 content_service - 整合大纲、解析和图表分析数据"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.PowerPoint.content_service import (
    build_slide_content,
    build_all_slides_content,
    build_content_from_process_result
)

# 测试数据路径
PARSE_FILE = Path(__file__).parent.parent / "outputs" / "test_parse.json"
IMAGE_FILE = Path(__file__).parent.parent / "outputs" / "test_image.json"
OUTLINE_FILE = Path(__file__).parent.parent / "outputs" / "test_outline.json"
PROCESS_RESULT_FILE = Path(__file__).parent.parent / "outputs" / "test_process_document_result.json"
OUTPUT_FILE = Path(__file__).parent.parent / "outputs" / "test_slide_content.json"


def load_json(path):
    """加载JSON文件"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  ❌ 加载失败 {path.name}: {e}")
        return None


def test_build_single_slide():
    """测试构建单个章节的幻灯片"""
    print("=" * 70)
    print("测试: build_slide_content (单个章节)")
    print("=" * 70)
    
    # 加载数据
    parse_result = load_json(PARSE_FILE)
    visual_analysis = load_json(IMAGE_FILE)
    outline_result = load_json(OUTLINE_FILE)
    
    if not all([parse_result, visual_analysis, outline_result]):
        print("\n  ❌ 数据文件缺失，请先运行:")
        print("    - test_parse_service.py")
        print("    - test_image_service.py")
        print("    - test_outline_service.py")
        return
    
    # 获取第一个成功的章节
    outline_sections = outline_result.get("sections", [])
    test_section = None
    
    for sec in outline_sections:
        if not sec.get("error"):
            test_section = sec
            break
    
    if not test_section:
        print("\n  ❌ 没有找到成功的大纲章节")
        return
    
    print(f"\n  测试章节: {test_section['section_name']}")
    
    # 构建幻灯片内容
    slides = build_slide_content(test_section, parse_result, visual_analysis)
    
    print(f"\n  结果:")
    print(f"    生成幻灯片数: {len(slides)}")
    
    # 显示第一个幻灯片的详细信息
    if slides:
        first_slide = slides[0]
        print(f"\n  第一个幻灯片:")
        print(f"    标题: {first_slide['slide_title']}")
        print(f"    章节: {first_slide['section_name']}")
        print(f"    目的: {first_slide['slide_purpose'][:60]}...")
        print(f"    要点数: {len(first_slide['content_points'])}")
        print(f"    内容长度: {len(first_slide['content'])} 字符")
        print(f"    图片引用: {len(first_slide['visual_refs']['images'])}")
        print(f"    表格引用: {len(first_slide['visual_refs']['tables'])}")
        print(f"    公式引用: {len(first_slide['visual_refs']['equations'])}")
        
        # 显示引用详情
        if first_slide['visual_refs']['images']:
            img = first_slide['visual_refs']['images'][0]
            print(f"\n  图片引用示例:")
            print(f"    ID: {img['id']}")
            print(f"    路径: {img['img_path'][:50]}...")
            print(f"    说明: {img['caption'][:60]}...")
            print(f"    分析: {img['analysis_text'][:60] if img['analysis_text'] else '(无)'}...")
        
        # 保存单个章节结果
        output = {
            "section_name": test_section['section_name'],
            "slides": slides
        }
        
        single_output = OUTPUT_FILE.parent / "test_single_slide_content.json"
        with open(single_output, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n  ✓ 已保存: {single_output}")


def test_build_all_slides():
    """测试构建所有幻灯片"""
    print("\n" + "=" * 70)
    print("测试: build_all_slides_content (所有章节)")
    print("=" * 70)
    
    # 加载数据
    parse_result = load_json(PARSE_FILE)
    visual_analysis = load_json(IMAGE_FILE)
    outline_result = load_json(OUTLINE_FILE)
    
    if not all([parse_result, visual_analysis, outline_result]):
        print("\n  ❌ 数据文件缺失")
        return
    
    # 构建所有幻灯片
    result = build_all_slides_content(outline_result, parse_result, visual_analysis)
    
    stats = result.get("statistics", {})
    print(f"\n  统计:")
    print(f"    总幻灯片: {stats['total_slides']}")
    print(f"    总章节: {stats['total_sections']}")
    print(f"    成功章节: {stats['success_sections']}")
    print(f"    失败章节: {stats['failed_sections']}")
    
    # 显示每个章节的幻灯片数
    slides = result.get("slides", [])
    section_counts = {}
    for slide in slides:
        sec_name = slide['section_name']
        section_counts[sec_name] = section_counts.get(sec_name, 0) + 1
    
    print(f"\n  各章节幻灯片数:")
    for idx, (sec_name, count) in enumerate(section_counts.items(), 1):
        print(f"    {idx}. {sec_name}: {count} 张")
    
    # 保存结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    file_size = OUTPUT_FILE.stat().st_size / 1024
    print(f"\n  ✓ 已保存: {OUTPUT_FILE}")
    print(f"  ✓ 文件大小: {file_size:.1f} KB")


def test_from_process_result():
    """测试从 process_document 结果构建"""
    print("\n" + "=" * 70)
    print("测试: build_content_from_process_result")
    print("=" * 70)
    
    if not PROCESS_RESULT_FILE.exists():
        print("\n  ❌ 未找到 process_document 结果文件")
        print("  请先运行: test_process_document.py")
        return
    
    # 加载 process_document 结果
    process_result = load_json(PROCESS_RESULT_FILE)
    if not process_result:
        return
    
    print(f"\n  源数据统计:")
    stats = process_result.get("statistics", {})
    print(f"    章节数: {stats.get('sections', 0)}")
    print(f"    元素数: {stats.get('elements', 0)}")
    print(f"    大纲成功: {stats.get('outline_success', 0)}")
    
    # 构建幻灯片内容
    result = build_content_from_process_result(process_result)
    
    slide_stats = result.get("statistics", {})
    print(f"\n  生成结果:")
    print(f"    总幻灯片: {slide_stats['total_slides']}")
    print(f"    成功章节: {slide_stats['success_sections']}")
    print(f"    失败章节: {slide_stats['failed_sections']}")
    
    # 保存结果
    output = OUTPUT_FILE.parent / "test_slide_content_from_process.json"
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    file_size = output.stat().st_size / 1024
    print(f"\n  ✓ 已保存: {output}")
    print(f"  ✓ 文件大小: {file_size:.1f} KB")


def show_sample_output():
    """显示示例输出格式"""
    print("\n" + "=" * 70)
    print("示例输出格式")
    print("=" * 70)
    
    sample = {
        "slide_title": "Hierarchical Text Classification Overview",
        "section_name": "1 Introduction",
        "slide_purpose": "Introduce the concept and importance of hierarchical text classification (HTC) in NLP.",
        "content_points": [
            "HTC is a multi-label text classification problem with a taxonomic hierarchy.",
            "Widely used in sentiment analysis, information retrieval, and document categorization.",
            "Hierarchy is modeled as a tree or directed acyclic graph (Figure 1)."
        ],
        "content": "",
        "visual_refs": {
            "images": [
                {
                    "type": "image",
                    "id": 1,
                    "img_path": "images/b8f39cac1148ea9ff7206aafcc5c8c228f8e1768d6b1f09f571ec4485e6dba74.jpg",
                    "caption": "Input text: [\"David Beckham's new book will be published.\"] Figure 1: This short sample is tagged with news, sports, football, features and books. Note that HTC could be either a single-path or a multi-path problem.",
                    "analysis_text": ""
                }
            ],
            "equations": [],
            "tables": []
        }
    }
    
    print("\n" + json.dumps(sample, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    show_sample_output()
    test_build_single_slide()
    test_build_all_slides()
    test_from_process_result()
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
