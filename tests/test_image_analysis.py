"""
测试图表公式分析功能
"""

import json
from pathlib import Path
from app.services.parse_service import parse_markdown_for_summary
from app.services.image_service import extract_elements_with_context, analyze_elements_with_dify
from app.core.logger import logger


def main():
    # 设置路径
    base_dir = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\Lin_HRank_Filter_Pruning_Using_High-Rank_Feature_Map_CVPR_2020_paper")
    md_file = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\Lin_HRank_Filter_Pruning_Using_High-Rank_Feature_Map_CVPR_2020_paper\full.md")
    json_file = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\Lin_HRank_Filter_Pruning_Using_High-Rank_Feature_Map_CVPR_2020_paper\c14e519a-40e7-43a2-a5be-50a9b4182bf5_content_list.json")
    image_base_path = base_dir
    
    logger.info(f"MD文件: {md_file}")
    logger.info(f"JSON文件: {json_file}")
    logger.info(f"图片根目录: {image_base_path}")
    
    # 步骤1: 解析文档
    logger.info("=" * 60)
    logger.info("步骤1: 解析文档")
    logger.info("=" * 60)
    
    parse_result = parse_markdown_for_summary(str(md_file), str(json_file))
    
    logger.info(f"解析完成，章节数: {len(parse_result.get('sections', []))}")
    logger.info(f"元数据: {parse_result.get('metadata')}")
    
    # 步骤2: 提取图表公式元素
    logger.info("=" * 60)
    logger.info("步骤2: 提取图表公式元素")
    logger.info("=" * 60)
    
    elements = extract_elements_with_context(parse_result)
    
    logger.info(f"提取完成，元素数: {len(elements)}")
    
    # 统计各类型数量
    type_counts = {}
    for elem in elements:
        elem_type = elem.get("element", {}).get("type")
        type_counts[elem_type] = type_counts.get(elem_type, 0) + 1
    
    logger.info(f"元素统计: {type_counts}")
    
    # 保存提取结果
    output_file = Path("outputs/test_extracted_elements.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(elements, f, ensure_ascii=False, indent=2)
    
    logger.info(f"提取结果已保存: {output_file}")
    
    # 步骤3: 分析前3个图表元素（测试）
    logger.info("=" * 60)
    logger.info("步骤3: 分析图表元素（测试前1个）")
    logger.info("=" * 60)
    
    # 只取前1个元素进行测试
    test_elements = elements[:1]
    
    logger.info(f"测试元素数: {len(test_elements)}")
    for i, elem in enumerate(test_elements, 1):
        element = elem.get("element", {})
        logger.info(f"  {i}. Type: {element.get('type')}, ID: {element.get('id')}, Path: {element.get('img_path')}")
    
    # 调用分析
    analysis_results = analyze_elements_with_dify(test_elements, image_base_path)
    
    # 保存分析结果
    analysis_output_file = Path("outputs/test_image_analysis.json")
    
    with open(analysis_output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"分析结果已保存: {analysis_output_file}")
    
    # 打印成功/失败统计
    success_count = len([r for r in analysis_results if r.get("analysis")])
    failed_count = len([r for r in analysis_results if r.get("error")])
    
    logger.info("=" * 60)
    logger.info(f"分析完成: 成功 {success_count}, 失败 {failed_count}")
    logger.info("=" * 60)
    
    # 打印部分分析结果示例
    if analysis_results:
        logger.info("\n分析结果示例:")
        for i, result in enumerate(analysis_results, 1):
            element = result.get("element", {})
            analysis = result.get("analysis", {})
            prompt = result.get("prompt", "")
            dify_metadata = result.get("dify_metadata", {})
            conversation_id = result.get("conversation_id", "")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"元素 {i}")
            logger.info(f"{'='*60}")
            logger.info(f"类型: {element.get('type')}")
            logger.info(f"ID: {element.get('id')}")
            logger.info(f"标题: {element.get('caption', 'N/A')}")
            
            # 显示Dify元数据
            if dify_metadata:
                usage = dify_metadata.get('usage', {})
                logger.info(f"\nDify调用信息:")
                logger.info(f"  会话ID: {conversation_id}")
                logger.info(f"  Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}")
                logger.info(f"  Completion Tokens: {usage.get('completion_tokens', 'N/A')}")
                logger.info(f"  Total Tokens: {usage.get('total_tokens', 'N/A')}")
                logger.info(f"  总价格: {usage.get('total_price', 'N/A')} {usage.get('currency', '')}")
                logger.info(f"  延迟: {usage.get('latency', 'N/A')}s")
            
            logger.info(f"\n提示词 (前500字符):\n{prompt[:500]}...")
            
            if analysis:
                # 显示新的返回结构
                ppt_content = analysis.get('ppt_content', {})
                speaker_notes = analysis.get('speaker_notes', {})
                
                logger.info(f"\n{'─'*60}")
                logger.info("PPT内容:")
                logger.info(f"{'─'*60}")
                logger.info(f"标题: {ppt_content.get('title', 'N/A')}")
                logger.info(f"\n要点 ({len(ppt_content.get('bullet_points', []))} 个):")
                for idx, point in enumerate(ppt_content.get('bullet_points', []), 1):
                    logger.info(f"  {idx}. {point}")
                logger.info(f"\n重点: {ppt_content.get('highlight', 'N/A')}")
                
                logger.info(f"\n{'─'*60}")
                logger.info("演讲者笔记:")
                logger.info(f"{'─'*60}")
                logger.info(f"解释:\n{speaker_notes.get('explanation', 'N/A')}")
                logger.info(f"\n关键推理 ({len(speaker_notes.get('key_reasoning', []))} 个):")
                for idx, reasoning in enumerate(speaker_notes.get('key_reasoning', []), 1):
                    logger.info(f"  {idx}. {reasoning}")
                logger.info(f"\n解读细节:\n{speaker_notes.get('interpretation_details', 'N/A')}")
                
                # 如果有解析错误，显示原始响应
                if analysis.get('parse_error'):
                    logger.info(f"\n{'─'*60}")
                    logger.info(f"解析错误: {analysis.get('parse_error')}")
                    logger.info(f"原始响应 (前1000字符):\n{analysis.get('raw_response', '')[:1000]}...")
            else:
                logger.info(f"\n错误: {result.get('error')}")


if __name__ == "__main__":
    main()
