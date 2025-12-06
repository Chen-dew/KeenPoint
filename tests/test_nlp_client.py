"""
测试 NLP 客户端服务
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.clients.nlp_client import nlp_client


def test_chat_stream():
    """测试流式对话"""
    print("=" * 80)
    print("测试流式对话")
    print("=" * 80)
    
    prompt = "请用一句话介绍深度学习"
    system_prompt = "你是一个专业的AI助手"
    
    print(f"\n用户: {prompt}\n")
    print("AI回复（流式）:")
    print("-" * 80)
    
    reasoning_parts = []
    content_parts = []
    usage_info = None
    
    for chunk in nlp_client.chat_stream(prompt, system_prompt):
        if chunk["type"] == "reasoning":
            reasoning_parts.append(chunk["content"])
            print(f"[思考] {chunk['content']}", end="", flush=True)
        elif chunk["type"] == "content":
            content_parts.append(chunk["content"])
            print(chunk["content"], end="", flush=True)
        elif chunk["type"] == "usage":
            usage_info = chunk["content"]
    
    print("\n" + "-" * 80)
    
    # 统计
    reasoning_text = "".join(reasoning_parts)
    content_text = "".join(content_parts)
    
    print(f"\n思考内容长度: {len(reasoning_text)} 字符")
    print(f"回复内容长度: {len(content_text)} 字符")
    
    if usage_info:
        print(f"\nToken消耗:")
        for key, value in usage_info.items():
            print(f"  {key}: {value}")
    
    print("\n✅ 流式对话测试完成")


def test_chat_sync():
    """测试同步对话"""
    print("\n" + "=" * 80)
    print("测试同步对话")
    print("=" * 80)
    
    prompt = "什么是机器学习？"
    system_prompt = "你是一个技术专家，请简洁回答"
    
    print(f"\n用户: {prompt}\n")
    print("正在获取完整回复...")
    
    result = nlp_client.chat_sync(prompt, system_prompt)
    
    print("\n思考过程:")
    print("-" * 80)
    print(result["reasoning"] if result["reasoning"] else "无思考内容")
    print("-" * 80)
    
    print("\nAI回复:")
    print("-" * 80)
    print(result["answer"])
    print("-" * 80)
    
    if result["usage"]:
        print(f"\nToken消耗:")
        for key, value in result["usage"].items():
            print(f"  {key}: {value}")
    
    print("\n✅ 同步对话测试完成")


def test_long_prompt():
    """测试长文本提示"""
    print("\n" + "=" * 80)
    print("测试长文本提示")
    print("=" * 80)
    
    prompt = """
请分析以下学术论文的主要贡献：

HRank: Filter Pruning using High-Rank Feature Map

摘要：模型压缩是深度学习领域的重要研究方向。本文提出了一种基于特征图秩的滤波器剪枝方法。

要求：
1. 总结主要创新点
2. 分析技术优势
3. 说明应用场景
"""
    
    print(f"提示词长度: {len(prompt)} 字符\n")
    print("AI分析:")
    print("-" * 80)
    
    content_parts = []
    
    for chunk in nlp_client.chat_stream(prompt):
        if chunk["type"] == "content":
            content_parts.append(chunk["content"])
            print(chunk["content"], end="", flush=True)
    
    print("\n" + "-" * 80)
    print(f"\n回复长度: {len(''.join(content_parts))} 字符")
    print("\n✅ 长文本测试完成")


def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 80)
    print("测试错误处理")
    print("=" * 80)
    
    try:
        # 空提示词
        print("\n测试1: 空提示词")
        result = nlp_client.chat_sync("")
        print("结果:", "成功" if result["answer"] else "返回空内容")
    except Exception as e:
        print(f"捕获异常: {e}")
    
    print("\n✅ 错误处理测试完成")


if __name__ == "__main__":
    print("开始测试 NLP 客户端服务")
    print("=" * 80)
    
    # 执行测试
    test_chat_stream()
    test_chat_sync()
    test_long_prompt()
    test_error_handling()
    
    print("\n" + "=" * 80)
    print("所有测试完成")
    print("=" * 80)
