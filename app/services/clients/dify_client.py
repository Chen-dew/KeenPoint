"""
Dify API 客户端
提供文件上传和对话功能
"""

import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Union, Generator, List
from app.core.config import settings
from app.core.logger import logger


class DifyClient:
    """Dify API 客户端"""
    
    def __init__(
        self, 
        api_key: str,
        base_url: Optional[str] = None, 
        user: Optional[str] = None
    ):
        """初始化 Dify 客户端"""
        self.api_key = api_key
        self.base_url = base_url or settings.DIFY_API_BASE_URL
        self.user = user or settings.DIFY_USER
        
        if not self.api_key:
            raise ValueError("api_key is required")
        
        self.upload_url = f"{self.base_url}/files/upload"
        self.chat_url = f"{self.base_url}/chat-messages"
            
    def upload_file(
        self, 
        file_path: Union[str, Path],
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        上传文件到 Dify
        
        Args:
            file_path: 文件路径
            user: 用户标识
            
        Returns:
            包含文件 ID 等信息的字典
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # 获取文件信息
        file_ext = file_path.suffix.lower().lstrip('.')
        file_name = file_path.name
        
        # 判断 MIME 类型
        mime_type = self._get_mime_type(file_ext)
        
        headers = {'Authorization': f'Bearer {self.api_key}'}
        user_id = user or self.user
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_name, f, mime_type)}
                data = {'user': user_id}
                
                logger.info(f"上传文件: {file_name}")
                
                response = requests.post(
                    self.upload_url,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=300
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"文件上传成功: {result.get('id')}")
                return result
                
        except requests.exceptions.RequestException as e:
            logger.error(f"文件上传失败: {e}")
            raise
        except Exception as e:
            logger.error(f"上传过程异常: {e}")
            raise
    
    def _get_mime_type(self, file_ext: str) -> str:
        """获取文件 MIME 类型"""
        image_types = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'webp': 'image/webp',
            'gif': 'image/gif'
        }
        
        doc_types = {
            'txt': 'text/plain',
            'md': 'text/markdown',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        mime_type = image_types.get(file_ext) or doc_types.get(file_ext)
        if not mime_type:
            raise ValueError(f"不支持的文件类型: {file_ext}")
        
        return mime_type

    def chat_with_files(
        self,
        query: str,
        file_ids: Optional[List[str]] = None,
        conversation_id: str = "",
        inputs: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        调用 Dify 聊天 API（流式响应，返回完整答案）
        
        Args:
            query: 用户问题
            file_ids: 已上传文件的 ID 列表
            conversation_id: 会话 ID
            inputs: 应用变量
            user: 用户标识
            
        Yields:
            完整的回答内容
        """
        if not query:
            raise ValueError("query 不能为空")
        
        user_id = user or self.user
        
        # 构建文件列表
        files = []
        if file_ids:
            for file_id in file_ids:
                files.append({
                    "type": "image",
                    "transfer_method": "local_file",
                    "upload_file_id": file_id
                })
        
        # 构建payload - 严格按照Dify API文档格式
        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "streaming",
            "conversation_id": conversation_id,
            "user": user_id,
            "files": files
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"调用 Dify API: {query[:50]}...")
            
            response = requests.post(
                self.chat_url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=300
            )
            
            response.raise_for_status()
            
            # 收集流式响应中的所有答案片段
            answer_chunks = []
            
            for line in response.iter_lines():
                if not line:
                    continue
                    
                line = line.decode('utf-8') if isinstance(line, bytes) else line
                
                if line.startswith(':') or not line.startswith('data:'):
                    continue
                
                try:
                    data_str = line[5:].strip()
                    if not data_str:
                        continue
                    
                    data = json.loads(data_str)
                    event_type = data.get('event', '')
                    
                    # 收集答案片段
                    if event_type in ['message', 'agent_message']:
                        answer = data.get('answer', '')
                        if answer:
                            answer_chunks.append(answer)
                    
                    # 消息结束
                    elif event_type == 'message_end':
                        logger.info("对话结束")
                    
                    # 内容被替换
                    elif event_type == 'message_replace':
                        logger.warning("内容被审核替换")
                        answer_chunks = [data.get('answer', '')]
                    
                    # 错误事件
                    elif event_type == 'error':
                        error_msg = data.get('message', '未知错误')
                        logger.error(f"API 错误: {error_msg}")
                        raise RuntimeError(f"API 错误: {error_msg}")
                
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"处理事件异常: {e}")
                    continue
            
            # 返回完整答案
            full_answer = ''.join(answer_chunks)
            
            if full_answer:
                logger.info(f"对话完成，答案长度: {len(full_answer)}")
                yield full_answer
            else:
                logger.warning("未收到回答内容")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API 请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"对话异常: {e}")
            raise


# 全局客户端实例
_image_client = None
_text_client = None

def get_image_client() -> DifyClient:
    """获取图像分析客户端实例"""
    global _image_client
    if _image_client is None:
        if not settings.DIFY_IMAGE_API_KEY:
            raise ValueError("DIFY_IMAGE_API_KEY 未配置")
        _image_client = DifyClient(api_key=settings.DIFY_IMAGE_API_KEY)
    return _image_client

def get_text_client() -> DifyClient:
    """获取文本分析客户端实例"""
    global _text_client
    if _text_client is None:
        if not settings.DIFY_TEXT_API_KEY:
            raise ValueError("DIFY_TEXT_API_KEY 未配置")
        _text_client = DifyClient(api_key=settings.DIFY_TEXT_API_KEY)
    return _text_client


def analyze_image(
    query: str,
    image_paths: Optional[List[Union[str, Path]]] = None,
    file_ids: Optional[List[str]] = None,
    conversation_id: str = "",
    inputs: Optional[Dict[str, Any]] = None,
    user: Optional[str] = None,
    auto_upload: bool = True
) -> Generator[str, None, None]:
    """
    与 Dify 对话（支持图片，流式响应）
    
    Args:
        query: 用户问题
        image_paths: 本地图片路径列表（auto_upload=True 时使用）
        file_ids: 已上传文件的 ID 列表
        conversation_id: 会话 ID
        inputs: 应用变量
        user: 用户标识
        auto_upload: 是否自动上传文件
        
    Yields:
        完整的回答内容
    """
    client = get_image_client()
    
    # 自动上传文件
    ids = file_ids or []
    if auto_upload and image_paths:
        logger.info(f"自动上传 {len(image_paths)} 个文件")
        for path in image_paths:
            result = client.upload_file(path, user)
            ids.append(result['id'])
    
    # 调用对话 API
    for answer in client.chat_with_files(
        query=query,
        file_ids=ids if ids else None,
        conversation_id=conversation_id,
        inputs=inputs,
        user=user
    ):
        yield answer


def analyze_text(
    query: str,
    conversation_id: str = "",
    inputs: Optional[Dict[str, Any]] = None,
    user: Optional[str] = None
) -> Generator[str, None, None]:
    """
    文本分析函数（流式输出）
    
    Args:
        query: 要分析的文本内容
        conversation_id: 会话 ID（可选）
        inputs: 应用变量（可选）
        user: 用户标识（可选）
        
    Yields:
        完整的分析结果（answer）
    """
    client = get_text_client()
    
    logger.info(f"开始文本分析，内容长度: {len(query)}")
    
    # 调用对话 API，流式返回答案
    for answer in client.chat_with_files(
        query=query,
        file_ids=None,
        conversation_id=conversation_id,
        inputs=inputs,
        user=user
    ):
        logger.info(f"文本分析完成，结果长度: {len(answer)}")
        yield answer

