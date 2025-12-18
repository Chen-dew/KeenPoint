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
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, user: Optional[str] = None):
        """初始化客户端"""
        if not api_key:
            raise ValueError("api_key is required")
        
        self.api_key = api_key
        self.base_url = base_url or settings.DIFY_API_BASE_URL
        self.user = user or settings.DIFY_USER
        self.upload_url = f"{self.base_url}/files/upload"
        self.chat_url = f"{self.base_url}/chat-messages"
    
    def upload_files_batch(
        self,
        file_paths: List[Union[str, Path]],
        user: Optional[str] = None,
        continue_on_error: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量上传文件（兼容单文件上传）
        
        Args:
            file_paths: 文件路径列表
            user: 用户标识
            continue_on_error: 遇到错误时是否继续
            
        Returns:
            上传结果列表
        """
        if not file_paths:
            logger.warning("文件列表为空")
            return []
        
        # 统一处理为列表
        if not isinstance(file_paths, list):
            file_paths = [file_paths]
        
        logger.info(f"开始上传 {len(file_paths)} 个文件")
        results = []
        user_id = user or self.user
        
        for idx, file_path in enumerate(file_paths, 1):
            file_path = Path(file_path)
            
            try:
                if not file_path.exists():
                    raise FileNotFoundError(f"文件不存在: {file_path}")
                
                # 获取文件信息
                file_ext = file_path.suffix.lower().lstrip('.')
                mime_type = self._get_mime_type(file_ext)
                
                # 执行上传
                headers = {'Authorization': f'Bearer {self.api_key}'}
                with open(file_path, 'rb') as f:
                    files = {'file': (file_path.name, f, mime_type)}
                    data = {'user': user_id}
                    
                    response = requests.post(
                        self.upload_url,
                        headers=headers,
                        files=files,
                        data=data,
                        timeout=300
                    )
                    response.raise_for_status()
                    result = response.json()
                
                results.append({
                    'success': True,
                    'file_path': str(file_path),
                    'file_id': result.get('id'),
                    'file_name': result.get('name'),
                    'data': result
                })
                logger.debug(f"上传成功 ({idx}/{len(file_paths)}): {file_path.name}")
                
            except Exception as e:
                error_info = {
                    'success': False,
                    'file_path': str(file_path),
                    'error': str(e)
                }
                results.append(error_info)
                logger.error(f"上传失败 ({idx}/{len(file_paths)}): {file_path.name} - {str(e)}")
                
                if not continue_on_error:
                    logger.error("上传中断")
                    break
        
        success_count = sum(1 for r in results if r.get('success'))
        logger.info(f"上传完成: 成功 {success_count}/{len(file_paths)}")
        return results
    
    def _get_mime_type(self, file_ext: str) -> str:
        """获取文件MIME类型"""
        mime_types = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'webp': 'image/webp',
            'gif': 'image/gif',
            'txt': 'text/plain',
            'md': 'text/markdown',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        mime_type = mime_types.get(file_ext)
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
        调用Dify聊天API（流式响应）
        
        Args:
            query: 用户问题
            file_ids: 已上传文件ID列表
            conversation_id: 会话ID
            inputs: 应用变量
            user: 用户标识
            
        Yields:
            完整的回答内容
        """
        if not query:
            raise ValueError("query不能为空")
        
        # 构建文件列表
        files = []
        if file_ids:
            for file_id in file_ids:
                files.append({
                    "type": "image",
                    "transfer_method": "local_file",
                    "upload_file_id": file_id
                })
        
        # 构建请求payload
        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "streaming",
            "conversation_id": conversation_id,
            "user": user or self.user,
            "files": files
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Dify API 请求: {query[:50]}...")
            
            response = requests.post(
                self.chat_url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=300
            )
            response.raise_for_status()
            
            # 处理流式响应
            answer_chunks = []
            event_stats = {'agent_thought': 0, 'agent_message': 0, 'message_end': 0}
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                line = line.decode('utf-8') if isinstance(line, bytes) else line
                
                if not line.startswith('data:'):
                    continue
                
                try:
                    data_str = line[5:].strip()
                    if not data_str:
                        continue
                    
                    data = json.loads(data_str)
                    event_type = data.get('event', '')
                    
                    if event_type == 'agent_thought':
                        event_stats['agent_thought'] += 1
                        logger.debug(f"agent_thought #{event_stats['agent_thought']}")
                    
                    elif event_type == 'agent_message':
                        event_stats['agent_message'] += 1
                        answer = data.get('answer', '')
                        if answer:
                            answer_chunks.append(answer)
                            logger.debug(f"agent_message #{event_stats['agent_message']}, chunk_len={len(answer)}")
                    
                    elif event_type == 'message_end':
                        event_stats['message_end'] += 1
                        logger.debug(f"message_end, conversation_id={data.get('conversation_id')}")
                    
                    elif event_type == 'message':
                        # 兼容普通message事件
                        answer = data.get('answer', '')
                        if answer:
                            answer_chunks.append(answer)
                    
                    elif event_type == 'message_replace':
                        logger.warning("内容被审核替换")
                        answer_chunks = [data.get('answer', '')]
                    
                    elif event_type == 'error':
                        error_msg = data.get('message', '未知错误')
                        logger.error(f"API错误: {error_msg}")
                        raise RuntimeError(f"API错误: {error_msg}")
                
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"事件处理异常: {e}")
                    continue
            
            # 返回完整答案
            full_answer = ''.join(answer_chunks)
            
            if full_answer:
                logger.info(f"对话完成, 答案长度={len(full_answer)}, "
                          f"事件统计: thought={event_stats['agent_thought']}, "
                          f"message={event_stats['agent_message']}, "
                          f"end={event_stats['message_end']}")
                yield full_answer
            else:
                logger.warning(f"未收到回答内容, 事件统计={event_stats}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"对话异常: {e}")
            raise
            raise
        except Exception as e:
            logger.error(f"对话异常: {e}")
            raise


# 全局客户端实例
_image_client = None
_text_client = None
_outline_client = None


def get_image_client() -> DifyClient:
    """获取图像分析客户端"""
    global _image_client
    if _image_client is None:
        if not settings.DIFY_IMAGE_API_KEY:
            raise ValueError("DIFY_IMAGE_API_KEY未配置")
        _image_client = DifyClient(api_key=settings.DIFY_IMAGE_API_KEY)
    return _image_client


def get_text_client() -> DifyClient:
    """获取文本分析客户端"""
    global _text_client
    if _text_client is None:
        if not settings.DIFY_TEXT_API_KEY:
            raise ValueError("DIFY_TEXT_API_KEY未配置")
        _text_client = DifyClient(api_key=settings.DIFY_TEXT_API_KEY)
    return _text_client


def get_outline_client() -> DifyClient:
    """获取大纲分析客户端"""
    global _outline_client
    if _outline_client is None:
        if not settings.DIFY_OUTLINE_API_KEY:
            raise ValueError("DIFY_OUTLINE_API_KEY未配置")
        _outline_client = DifyClient(api_key=settings.DIFY_OUTLINE_API_KEY)
    return _outline_client


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
    图像分析（支持自动上传，流式响应）
    
    Args:
        query: 用户问题
        image_paths: 本地图片路径列表
        file_ids: 已上传文件ID列表
        conversation_id: 会话ID
        inputs: 应用变量
        user: 用户标识
        auto_upload: 是否自动上传文件
        
    Yields:
        完整的回答内容
    """
    client = get_image_client()
    
    # 自动批量上传
    ids = file_ids or []
    if auto_upload and image_paths:
        logger.debug(f"批量上传 {len(image_paths)} 个文件")
        upload_results = client.upload_files_batch(image_paths, user, continue_on_error=True)
        
        for result in upload_results:
            if result.get('success'):
                ids.append(result['file_id'])
            else:
                logger.warning(f"上传失败: {Path(result.get('file_path')).name}")
        
        if not ids:
            raise RuntimeError("所有文件上传失败")
        
        logger.info(f"成功上传 {len(ids)}/{len(image_paths)} 个文件")
    
    # 调用对话API
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
    文本分析（流式输出）
    
    Args:
        query: 要分析的文本内容
        conversation_id: 会话ID
        inputs: 应用变量
        user: 用户标识
        
    Yields:
        完整的分析结果
    """
    client = get_text_client()
    
    logger.info(f"开始文本分析, 内容长度={len(query)}")
    
    for answer in client.chat_with_files(
        query=query,
        file_ids=None,
        conversation_id=conversation_id,
        inputs=inputs,
        user=user
    ):
        logger.info(f"文本分析完成, 结果长度={len(answer)}")
        yield answer


def analyze_outline(
    query: str,
    conversation_id: str = "",
    inputs: Optional[Dict[str, Any]] = None,
    user: Optional[str] = None
) -> Generator[str, None, None]:
    """
    大纲分析（流式输出）
    
    Args:
        query: 要分析的大纲内容
        conversation_id: 会话ID
        inputs: 应用变量
        user: 用户标识
        
    Yields:
        完整的分析结果
    """
    client = get_outline_client()
    
    logger.info(f"开始大纲分析, 内容长度={len(query)}")
    
    for answer in client.chat_with_files(
        query=query,
        file_ids=None,
        conversation_id=conversation_id,
        inputs=inputs,
        user=user
    ):
        logger.info(f"大纲分析完成, 结果长度={len(answer)}")
        yield answer


def upload_files_batch(
    file_paths: List[Union[str, Path]],
    user: Optional[str] = None,
    use_image_client: bool = True,
    continue_on_error: bool = True
) -> List[Dict[str, Any]]:
    """
    批量上传文件（全局函数，兼容单文件上传）
    
    Args:
        file_paths: 文件路径列表（支持单个文件或列表）
        user: 用户标识
        use_image_client: 使用图像客户端（True）或文本客户端（False）
        continue_on_error: 遇到错误时是否继续
        
    Returns:
        上传结果列表
    """
    client = get_image_client() if use_image_client else get_text_client()
    return client.upload_files_batch(file_paths, user, continue_on_error)

