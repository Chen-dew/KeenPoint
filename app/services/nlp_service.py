"""
NLP 服务
提供自然语言处理功能，包括结构分析、关键词提取和摘要生成
"""

import re
from typing import Dict, List
from collections import Counter
from app.core.logger import logger

def analyze_structure(text: str) -> Dict:
    """
    分析论文结构 - 识别章节
    
    使用关键词匹配方法识别学术论文的标准章节
    
    参数:
    - text: 论文文本内容
    
    返回:
    - 结构分析结果
    """
    logger.info("🔍 开始分析论文结构...")
    
    # 标准学术论文章节关键词
    section_keywords = {
        "Abstract": ["abstract", "摘要"],
        "Introduction": ["introduction", "引言", "绪论"],
        "Related Work": ["related work", "literature review", "相关工作", "文献综述"],
        "Methodology": ["methodology", "methods", "approach", "方法", "方法论"],
        "Experiment": ["experiment", "experimental", "实验"],
        "Results": ["results", "结果"],
        "Discussion": ["discussion", "讨论"],
        "Conclusion": ["conclusion", "conclusions", "结论"],
        "References": ["references", "bibliography", "参考文献"]
    }
    
    # 转为小写便于匹配
    text_lower = text.lower()
    
    # 检测到的章节
    detected_sections = []
    section_details = {}
    
    for section_name, keywords in section_keywords.items():
        for keyword in keywords:
            # 使用正则表达式查找章节标题
            pattern = rf'\b{re.escape(keyword)}\b'
            matches = list(re.finditer(pattern, text_lower))
            
            if matches:
                detected_sections.append(section_name)
                section_details[section_name] = {
                    "keyword_matched": keyword,
                    "occurrences": len(matches),
                    "first_position": matches[0].start()
                }
                break  # 找到一个匹配就跳出
    
    # 按照在文本中出现的位置排序
    detected_sections = sorted(
        detected_sections,
        key=lambda x: section_details[x]["first_position"]
    )
    
    result = {
        "sections_detected": detected_sections,
        "section_count": len(detected_sections),
        "details": section_details
    }
    
    logger.info(f"✅ 结构分析完成，检测到 {len(detected_sections)} 个章节: {', '.join(detected_sections)}")
    
    return result

def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """
    提取关键词
    
    使用简单的词频统计方法提取关键词
    (实际应用中可使用 TF-IDF 或更复杂的算法)
    
    参数:
    - text: 文本内容
    - top_n: 返回前 N 个关键词
    
    返回:
    - 关键词列表
    """
    logger.info(f"🔑 开始提取关键词 (Top {top_n})...")
    
    # 清理文本
    text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # 停用词列表（简化版）
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which',
        'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
        'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very'
    }
    
    # 分词
    words = text_clean.split()
    
    # 过滤停用词和短词
    filtered_words = [
        word for word in words
        if word not in stop_words and len(word) > 3
    ]
    
    # 统计词频
    word_freq = Counter(filtered_words)
    
    # 获取最常见的词
    keywords = [word for word, freq in word_freq.most_common(top_n)]
    
    logger.info(f"✅ 关键词提取完成: {', '.join(keywords[:5])}...")
    
    return keywords

def generate_summary(text: str, max_length: int = 200) -> str:
    """
    生成文本摘要
    
    使用简单的句子提取方法生成摘要
    (实际应用中可使用 BERT 等预训练模型)
    
    参数:
    - text: 文本内容
    - max_length: 摘要最大长度
    
    返回:
    - 生成的摘要
    """
    logger.info("📝 开始生成摘要...")
    
    # 分句
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    if not sentences:
        return "无法生成摘要：文本过短。"
    
    # 简单策略：取前几句作为摘要
    summary = ""
    for sentence in sentences[:5]:  # 最多取前5句
        if len(summary) + len(sentence) > max_length:
            break
        summary += sentence + ". "
    
    if not summary:
        summary = sentences[0][:max_length] + "..."
    
    logger.info(f"✅ 摘要生成完成，长度: {len(summary)}")
    
    return summary.strip()

def detect_language(text: str) -> str:
    """
    检测文本语言
    
    简单的语言检测（中文/英文）
    
    参数:
    - text: 文本内容
    
    返回:
    - 语言代码 ('zh' 或 'en')
    """
    # 统计中文字符数量
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    
    # 统计英文字符数量
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    
    if chinese_chars > english_chars:
        return "zh"
    else:
        return "en"

def extract_citations(text: str) -> List[str]:
    """
    提取引用信息
    
    参数:
    - text: 文本内容
    
    返回:
    - 引用列表
    """
    # 简单的引用模式匹配 [1], [2], etc.
    citations = re.findall(r'\[\d+\]', text)
    return list(set(citations))  # 去重

def count_figures_and_tables(text: str) -> Dict:
    """
    统计图表数量
    
    参数:
    - text: 文本内容
    
    返回:
    - 统计结果
    """
    figures = len(re.findall(r'Figure\s+\d+|图\s*\d+', text, re.IGNORECASE))
    tables = len(re.findall(r'Table\s+\d+|表\s*\d+', text, re.IGNORECASE))
    
    return {
        "figures": figures,
        "tables": tables,
        "total": figures + tables
    }
