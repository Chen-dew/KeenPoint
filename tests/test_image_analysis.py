"""测试图表公式分析功能"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import json
from app.services.parse_service import parse_markdown_for_summary
from app.services.image_service import extract_elements_with_context, analyze_elements_with_dify
from app.core.logger import logger


def main():
    # 设置路径
    base_dir = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104")
    md_file = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\full.md")
    json_file = Path(r"D:\MyFiles\AIPPT\Code\keenPoint\downloads\acl20_104\9eafd4f2-7e84-4bf8-b8ae-7fd19e07a68b_content_list.json")
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
    
    # 步骤3: 分析图表元素（只测试一个）
    logger.info("=" * 60)
    logger.info("步骤3: 分析图表元素（只测试一个）")
    logger.info("=" * 60)
    
    # 只测试第一个图片元素
    test_elements = []
    for elem in elements:
        element = elem.get("element", {})
        if element.get("type") == "image" and element.get("img_path"):
            test_elements = [elem]
            logger.info(f"选中的测试元素: Type={element.get('type')}, ID={element.get('id')}, Path={element.get('img_path')}")
            break
    
    if not test_elements:
        logger.error("未找到可测试的图片元素")
        return
    
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
    total_count = len(analysis_results)
    
    logger.info("=" * 60)
    logger.info(f"分析完成: 总数 {total_count}, 成功 {success_count}, 失败 {failed_count}")
    logger.info("=" * 60)
    
    # 打印分析结果摘要
    if analysis_results:
        logger.info("\n" + "=" * 60)
        logger.info("分析结果摘要")
        logger.info("=" * 60)
        
        for i, result in enumerate(analysis_results, 1):
            element = result.get("element", {})
            analysis = result.get("analysis", {})
            
            status = "✓" if analysis else "✗"
            element_type = element.get('type', 'N/A')
            element_id = element.get('id', 'N/A')
            
            if analysis:
                ppt_title = analysis.get('ppt_content', {}).get('title', 'N/A')
                bullet_count = len(analysis.get('ppt_content', {}).get('bullet_points', []))
                logger.info(f"{status} [{i}/{len(analysis_results)}] {element_type}-{element_id}: {ppt_title} ({bullet_count} 要点)")
            else:
                error = result.get('error', 'Unknown')
                logger.info(f"{status} [{i}/{len(analysis_results)}] {element_type}-{element_id}: 失败 - {error}")


if __name__ == "__main__":
    main()
