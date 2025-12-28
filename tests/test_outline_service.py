"""测试 outline_service - 从两个JSON提取数据并调用analyze_outline生成大纲"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.clients.dify_workflow_client import analyze_outline
from app.core.logger import logger

# 输入文件
PARSE_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\outputs\test_parse.json"
IMAGE_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\outputs\test_image.json"
OUTPUT_FILE = r"D:\MyFiles\AIPPT\Code\keenPoint\outputs\test_outline.json"


def load_json(path):
    """加载JSON文件"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[TEST] 加载失败 {path}: {e}")
        return None


def build_element_map(image_data):
    """构建元素ID到分析文本的映射
    
    Returns:
        dict: {
            'images': {id: analyze_text},
            'tables': {id: analyze_text},
            'equations': {id: analyze_text}
        }
    """
    element_map = {
        'images': {},
        'tables': {},
        'equations': {}
    }
    
    if not isinstance(image_data, list):
        return element_map
    
    for item in image_data:
        elem = item.get("element", {})
        elem_type = elem.get("type")
        elem_id = elem.get("id")
        analysis = item.get("analysis", {})
        
        if not analysis or elem_id is None:
            continue
        
        analysis_text = analysis.get("analysis_text", "")
        
        # 根据类型存储
        if elem_type == "image":
            element_map['images'][elem_id] = analysis_text
        elif elem_type == "table":
            element_map['tables'][elem_id] = analysis_text
        elif elem_type == "equation":
            element_map['equations'][elem_id] = analysis_text
    
    logger.info(f"[TEST] 元素映射: images={len(element_map['images'])}, "
                f"tables={len(element_map['tables'])}, equations={len(element_map['equations'])}")
    
    return element_map


def extract_section_data(parse_sections, element_map, abstract):
    """从parse和image数据源提取章节数据
    
    Args:
        parse_sections: 解析结果的章节列表
        element_map: 元素映射
        abstract: 论文摘要
    
    Returns:
        list: [{
            abstract: str,
            section_name: str,
            content: str,
            refs: {
                images: [{id, analyze_text}],
                equations: [{id, analyze_text}],
                tables: [{id, analyze_text}]
            }
        }]
    """
    sections_data = []
    
    for idx, parse_sec in enumerate(parse_sections):
        section_name = parse_sec.get("name", "")
        content = parse_sec.get("content", "")
        
        # 提取该章节的图表公式引用
        refs = {
            "images": [],
            "equations": [],
            "tables": []
        }
        
        # 图片
        for fig in parse_sec.get("fig_refs", []):
            fig_id = fig.get("id")
            if fig_id is not None and fig_id in element_map['images']:
                refs["images"].append({
                    "id": fig_id,
                    "analyze_text": element_map['images'][fig_id]
                })
        
        # 表格
        for tbl in parse_sec.get("table_refs", []):
            tbl_id = tbl.get("id")
            if tbl_id is not None and tbl_id in element_map['tables']:
                refs["tables"].append({
                    "id": tbl_id,
                    "analyze_text": element_map['tables'][tbl_id]
                })
        
        # 公式
        for eq in parse_sec.get("formula_refs", []):
            eq_id = eq.get("id")
            if eq_id is not None and eq_id in element_map['equations']:
                refs["equations"].append({
                    "id": eq_id,
                    "analyze_text": element_map['equations'][eq_id]
                })
        
        sections_data.append({
            "abstract": abstract,
            "section_name": section_name,
            "content": content,
            "refs": refs
        })
        
        logger.info(f"[TEST] 章节 {idx}: {section_name[:40]}, "
                   f"content_len={len(content)}, images={len(refs['images'])}, "
                   f"tables={len(refs['tables'])}, equations={len(refs['equations'])}")
    
    return sections_data


def analyze_section_outline(section_data, section_idx, total_sections):
    """分析单个章节的大纲
    
    Args:
        section_data: 章节数据
        section_idx: 章节索引
        total_sections: 总章节数
    
    Returns:
        dict: {
            section_name: str,
            raw_result: dict (原始Dify返回结果)
        }
    """
    section_name = section_data["section_name"]
    
    logger.info(f"[TEST] [{section_idx}/{total_sections}] 分析章节: {section_name}")
    
    # 构造query
    query = json.dumps(section_data, ensure_ascii=False)
    
    logger.info(f"[TEST] Query长度: {len(query)} 字符")
    
    try:
        # 调用analyze_outline
        result = analyze_outline(query=query)
        
        logger.info(f"[TEST] 章节 '{section_name}' 分析成功")
        logger.info(f"[TEST] 返回结果类型: {type(result)}")
        
        if isinstance(result, dict):
            logger.info(f"[TEST] 返回结果键: {list(result.keys())}")
        
        return {
            "section_name": section_name,
            "raw_result": result
        }
        
    except Exception as e:
        logger.error(f"[TEST] 章节 '{section_name}' 分析失败: {e}")
        return {
            "section_name": section_name,
            "raw_result": None,
            "error": str(e)
        }


def test_outline_generation():
    """测试大纲生成 - 分析所有章节"""
    print("=" * 60)
    print("测试: 大纲生成")
    print("=" * 60)
    
    # 1. 加载数据
    print("\n[步骤1] 加载数据...")
    parse_data = load_json(PARSE_FILE)
    image_data = load_json(IMAGE_FILE)
    
    if not parse_data:
        print("  ❌ 无法加载解析数据")
        return None
    
    parse_sections = parse_data.get("sections", [])
    
    # 获取摘要
    abstract = ""
    for sec in parse_sections:
        if "abstract" in sec.get("name", "").lower():
            abstract = sec.get("content", "")
            break
    
    print(f"  解析结果: {len(parse_sections)} 个章节")
    print(f"  摘要长度: {len(abstract)} 字符")
    print(f"  图表分析: {len(image_data) if isinstance(image_data, list) else 0} 个元素")
    
    # 2. 构建元素映射
    print("\n[步骤2] 构建元素映射...")
    element_map = build_element_map(image_data)
    
    # 3. 提取章节数据
    print("\n[步骤3] 提取章节数据...")
    sections_data = extract_section_data(parse_sections, element_map, abstract)
    print(f"  提取了 {len(sections_data)} 个章节的数据")
    
    # 4. 逐个分析章节
    print(f"\n[步骤4] 分析 {len(sections_data)} 个章节...")
    results = []
    
    for idx, section_data in enumerate(sections_data, 1):
        result = analyze_section_outline(section_data, idx, len(sections_data))
        results.append(result)
        
        # 延迟避免API限流
        if idx < len(sections_data):
            time.sleep(1)
    
    # 5. 统计
    success = len([r for r in results if not r.get("error")])
    failed = len([r for r in results if r.get("error")])
    
    print("\n" + "=" * 60)
    print(f"分析完成: 成功={success}, 失败={failed}")
    print("=" * 60)
    
    # 6. 保存结果
    output_data = {
        "sections": results,
        "statistics": {
            "total_sections": len(results),
            "success": success,
            "failed": failed
        }
    }
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 结果已保存: {OUTPUT_FILE}")
        print(f"   文件大小: {Path(OUTPUT_FILE).stat().st_size / 1024:.1f} KB")
    except Exception as e:
        print(f"\n❌ 保存失败: {e}")
    
    return output_data


if __name__ == "__main__":
    test_outline_generation()
