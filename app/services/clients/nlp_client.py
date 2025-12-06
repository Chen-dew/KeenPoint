"""
NLP 客户端服务
封装对 DashScope (阿里云百炼) 等大模型 API 的调用
"""

from openai import OpenAI
from typing import Optional, Generator, Dict, Any
from app.core.config import settings
from app.core.logger import logger

class NLPClient:
    def __init__(self):
        # 初始化 OpenAI 客户端
        # 使用配置中的 API Key 和 Base URL
        self.client = OpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL,
        )
        self.model = settings.DASHSCOPE_MODEL

    def chat_stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
        """
        流式对话生成，支持思考模式
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词 (可选)
            
        Yields:
            Dict: {"type": "reasoning"|"content"|"usage", "content": str|dict}
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            logger.info(f"开始调用 NLP 模型: {self.model}")
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                # 通过 extra_body 设置 enable_thinking 开启思考模式
                extra_body={"enable_thinking": True},
                stream=True,
                stream_options={
                    "include_usage": True
                },
            )

            is_answering = False

            for chunk in completion:
                # 处理 Usage 信息 (通常在最后)
                if not chunk.choices:
                    if hasattr(chunk, "usage") and chunk.usage:
                        logger.info(f"Token 消耗: {chunk.usage}")
                        yield {"type": "usage", "content": chunk.usage.model_dump() if hasattr(chunk.usage, "model_dump") else chunk.usage}
                    continue

                delta = chunk.choices[0].delta

                # 收集思考内容
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    yield {"type": "reasoning", "content": delta.reasoning_content}

                # 收集回复内容
                if hasattr(delta, "content") and delta.content:
                    if not is_answering:
                        is_answering = True
                    yield {"type": "content", "content": delta.content}

        except Exception as e:
            logger.error(f"NLP API调用失败: {str(e)}")
            raise e

    def chat_sync(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        同步获取完整回复
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            
        Returns:
            Dict: {
                "reasoning": str,  # 完整思考过程
                "answer": str,     # 完整回复
                "usage": dict      # Token 消耗
            }
        """
        reasoning_content = ""
        answer_content = ""
        usage_info = {}
        
        for chunk in self.chat_stream(prompt, system_prompt):
            if chunk["type"] == "reasoning":
                reasoning_content += chunk["content"]
            elif chunk["type"] == "content":
                answer_content += chunk["content"]
            elif chunk["type"] == "usage":
                usage_info = chunk["content"]
                
        return {
            "reasoning": reasoning_content,
            "answer": answer_content,
            "usage": usage_info
        }

# 创建全局实例
nlp_client = NLPClient()
