"""测试大纲分析服务 - 使用真实数据（ACL20_104）"""

import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.services.parse_service import parse_markdown_for_summary
from app.services.nlp_service import extract_and_split_sections, analyze_segments_with_abstract
from app.services.image_service import extract_elements_with_context, analyze_elements_with_dify
from app.services.outline_service import build_outline_prompt, analyze_outline_with_dify
from app.core.logger import logger


def test_outline_with_real_data():
    """测试大纲分析服务 - 真实数据（限制3个章节）"""
    print("=" * 80)
    print("大纲分析服务测试 - 真实数据（ACL20_104）")
    print("=" * 80)
    
    # 设置测试数据路径
    test_dir = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104")
    md_file = test_dir / "full.md"
    json_file = test_dir / "9eafd4f2-7e84-4bf8-b8ae-7fd19e07a68b_content_list.json"
    
    if not md_file.exists():
        print(f"Markdown文件不存在: {md_file}")
        return
    
    if not json_file.exists():
        print(f"JSON文件不存在: {json_file}")
        return
    
    # 初始化汇总输出
    summary_output = {
        "test_info": {
            "test_name": "大纲分析服务测试",
            "data_source": "ACL20_104",
            "test_date": "2025-12-15",
            "max_sections": 3
        },
        "step1_parse_result": None,
        "step2_text_analysis": None,
        "step3_visual_analysis": None,
        "step4_outline_inputs": None,
        "step5_outline_results": None,
        "statistics": {}
    }
    
    try:
        # 步骤1: 解析文档
        print("\n[步骤1] 解析Markdown文档...")
        parse_result = parse_markdown_for_summary(str(md_file), str(json_file))
        total_sections = len(parse_result.get('sections', []))
        print(f"  解析完成: {total_sections} 个章节")
        
        # 显示所有章节名称
        print("\n所有章节:")
        for idx, section in enumerate(parse_result.get('sections', []), 1):
            print(f"  {idx}. {section.get('name', 'Unknown')}")
        
        # 限制处理前3个非Abstract章节
        print("\n选择处理前3个非Abstract章节...")
        selected_sections = []
        for section in parse_result.get('sections', []):
            section_name = section.get('name', '').lower()
            if 'abstract' not in section_name and '摘要' not in section_name:
                selected_sections.append(section)
                if len(selected_sections) >= 3:
                    break
        
        if len(selected_sections) < 3:
            print(f"警告: 只找到 {len(selected_sections)} 个非Abstract章节")
        
        print(f"\n选中的章节:")
        for idx, section in enumerate(selected_sections, 1):
            print(f"  {idx}. {section.get('name', 'Unknown')}")
        
        # 创建限制后的parse_result
        limited_parse_result = {
            'sections': selected_sections,
            'metadata': parse_result.get('metadata', {})
        }
        
        # 保存到汇总输出
        summary_output["step1_parse_result"] = {
            "total_sections": total_sections,
            "selected_sections": [s.get('name', 'Unknown') for s in selected_sections],
            "metadata": limited_parse_result['metadata']
        }
        
        # 步骤2: 文本分析
        print("\n[步骤2] 文本章节分析...")
        
        # 提取摘要
        abstract = ""
        for section in parse_result.get('sections', []):
            section_name = section.get('name', '').lower()
            if 'abstract' in section_name or '摘要' in section_name:
                abstract = section.get('content', '')
                print(f"  找到摘要，长度: {len(abstract)}")
                break
        
        if not abstract:
            print("  未找到Abstract章节，使用空摘要")
        
        # 拆分章节
        segments = extract_and_split_sections(limited_parse_result)
        print(f"  拆分章节: {len(segments)} 个片段")
        
        # 分析文本
        print("  开始文本分析（这可能需要一些时间）...")
        text_analysis = analyze_segments_with_abstract(segments, abstract, skip_abstract_section=True)
        print(f"  文本分析完成: {len(text_analysis)} 个结果")
        
        # 保存到汇总输出
        summary_output["step2_text_analysis"] = text_analysis
        
        # 步骤3: 视觉元素分析
        print("\n[步骤3] 图表公式分析...")
        elements = extract_elements_with_context(limited_parse_result)
        print(f"  提取元素: {len(elements)} 个")
        
        if elements:
            # 显示元素类型统计
            element_types = {}
            for elem in elements:
                elem_type = elem.get('element', {}).get('type', 'unknown')
                element_types[elem_type] = element_types.get(elem_type, 0) + 1
            
            print("  元素类型分布:")
            for elem_type, count in element_types.items():
                print(f"    {elem_type}: {count}")
            
            print("  开始视觉分析（这可能需要一些时间）...")
            visual_analysis = analyze_elements_with_dify(elements, base_path=test_dir)
            print(f"  视觉分析完成: {len(visual_analysis)} 个结果")
            
            # 统计成功和失败
            success_count = sum(1 for v in visual_analysis if v.get('analysis') and not v.get('error'))
            fail_count = len(visual_analysis) - success_count
            print(f"  分析统计: 成功 {success_count}, 失败 {fail_count}")
        else:
            print("  没有找到视觉元素")
            visual_analysis = []
        
        # 保存到汇总输出
        summary_output["step3_visual_analysis"] = visual_analysis
        
        # 步骤4: 构建大纲输入
        print("\n[步骤4] 构建大纲分析输入...")
        outline_inputs = build_outline_prompt(limited_parse_result, text_analysis, visual_analysis)
        print(f"  构建完成: {len(outline_inputs)} 个章节输入")
        
        # 显示每个章节的数据统计
        for idx, section_input in enumerate(outline_inputs, 1):
            section_name = section_input.get('section_name', 'Unknown')
            refs = section_input.get('refs', {})
            img_count = len(refs.get('images', []))
            eq_count = len(refs.get('equations', []))
            tbl_count = len(refs.get('tables', []))
            
            print(f"  章节 {idx}: {section_name}")
            print(f"    图片: {img_count}, 公式: {eq_count}, 表格: {tbl_count}")
        
        # 保存到汇总输出
        summary_output["step4_outline_inputs"] = outline_inputs
        
        # 步骤5: 大纲分析
        print("\n[步骤5] 调用Dify进行大纲分析...")
        print("  这可能需要较长时间，请耐心等待...")
        outline_results = analyze_outline_with_dify(outline_inputs, skip_abstract=True)
        print(f"  大纲分析完成: {len(outline_results)} 个结果")
        
        # 统计结果
        success_count = sum(1 for r in outline_results if not r.get('error'))
        fail_count = len(outline_results) - success_count
        print(f"  分析统计: 成功 {success_count}, 失败 {fail_count}")
        
        # 保存到汇总输出
        summary_output["step5_outline_results"] = outline_results
        
        # 统计信息
        summary_output["statistics"] = {
            "total_sections_in_document": total_sections,
            "sections_processed": len(selected_sections),
            "text_analysis_count": len(text_analysis),
            "visual_elements_count": len(elements) if elements else 0,
            "visual_analysis_count": len(visual_analysis),
            "outline_inputs_count": len(outline_inputs),
            "outline_results_success": sum(1 for r in outline_results if not r.get('error')),
            "outline_results_failed": sum(1 for r in outline_results if r.get('error')),
            "total_slides": sum(len(r.get('ppt_outline', [])) for r in outline_results if not r.get('error'))
        }
        
        # 保存汇总文件
        summary_file = r"D:\MyFiles\AIPPT\Code\keenPoint\outputs\test_outline_output.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_output, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 所有测试结果已汇总到: {summary_file}")
        # 显示统计信息
        print("\n" + "=" * 80)
        print("测试统计:")
        print("=" * 80)
        stats = summary_output["statistics"]
        print(f"文档总章节数: {stats['total_sections_in_document']}")
        print(f"处理章节数: {stats['sections_processed']}")
        print(f"文本分析结果: {stats['text_analysis_count']}")
        print(f"视觉元素总数: {stats['visual_elements_count']}")
        print(f"视觉分析结果: {stats['visual_analysis_count']}")
        print(f"大纲输入数: {stats['outline_inputs_count']}")
        print(f"大纲分析成功: {stats['outline_results_success']}")
        print(f"大纲分析失败: {stats['outline_results_failed']}")
        print(f"生成幻灯片总数: {stats['total_slides']}")
        
        # 显示各章节详情
        print("\n章节详情:")
        total_slides = 0
        for result in outline_results:
            section_name = result.get("section_name", "Unknown")
            slides = result.get("ppt_outline", [])
            error = result.get("error")
            
            if error:
                print(f"  {section_name}: 失败 - {error}")
            else:
                total_slides += len(slides)
                print(f"  {section_name}: {len(slides)} 个幻灯片")
                
                # 显示每个幻灯片的标题
                for idx, slide in enumerate(slides, 1):
                    slide_title = slide.get("slide_title", "无标题")
                    visual_refs = slide.get("visual_refs", {})
                    ref_count = (
                        len(visual_refs.get("images", [])) +
                        len(visual_refs.get("equations", [])) +
                        len(visual_refs.get("tables", []))
                    )
                    print(f"    {idx}. {slide_title} (引用 {ref_count} 个视觉元素)")
        
        print(f"\n总计: {total_slides} 个幻灯片")
        
        # 显示第一个成功的章节的详细输出
        print("\n" + "=" * 80)
        print("示例输出（第一个成功的章节）:")
        print("=" * 80)
        
        first_success = next((r for r in outline_results if not r.get('error')), None)
        if first_success:
            print(json.dumps(first_success, ensure_ascii=False, indent=2))
        else:
            print("没有成功的分析结果")
        
        print("\n" + "=" * 80)
        print("测试完成！")
        print("=" * 80)
        print(f"\n完整测试结果已保存到: {summary_file}")
        
    except Exception as e:
        print(f"\n测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_outline_with_real_data()
