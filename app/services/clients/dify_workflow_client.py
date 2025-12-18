"""Dify Workflow API 客户端模块"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests

from app.core.config import settings
from app.core.logger import logger


# MIME类型映射表
MIME_TYPES = {
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


class DifyWorkflowClient:
    """Dify Workflow API 客户端"""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        default_user: str = "chen"
    ) -> None:
        """初始化客户端"""
        if not api_key:
            raise ValueError("api_key is required")

        self.api_key = api_key
        self.base_url = (base_url or settings.DIFY_API_BASE_URL).rstrip("/")
        self.default_user = default_user
        self.run_url = f"{self.base_url}/workflows/run"
        self.upload_url = f"{self.base_url}/files/upload"

    def upload_file(
        self,
        file_path: Union[str, Path],
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """上传单个文件"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # 获取MIME类型
        file_ext = file_path.suffix.lower().lstrip('.')
        mime_type = MIME_TYPES.get(file_ext)
        if not mime_type:
            raise ValueError(f"Unsupported file type: {file_ext}")

        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, mime_type)}
            data = {'user': user or self.default_user}
            
            resp = requests.post(
                self.upload_url,
                headers=headers,
                files=files,
                data=data,
                timeout=300
            )
            resp.raise_for_status()
            return resp.json()

    def upload_files_batch(
        self,
        file_paths: List[Union[str, Path]],
        user: Optional[str] = None,
        continue_on_error: bool = True
    ) -> List[Dict[str, Any]]:
        """批量上传文件"""
        if not file_paths:
            return []

        logger.info("upload_batch start count=%s", len(file_paths))
        results = []

        for idx, file_path in enumerate(file_paths, 1):
            file_path = Path(file_path)
            
            try:
                result = self.upload_file(file_path, user)
                results.append({
                    'success': True,
                    'file_path': str(file_path),
                    'file_id': result.get('id'),
                    'file_name': result.get('name')
                })
                logger.info("upload_batch success idx=%s/%s file=%s", idx, len(file_paths), file_path.name)

            except Exception as e:
                results.append({
                    'success': False,
                    'file_path': str(file_path),
                    'error': str(e)
                })
                logger.error("upload_batch failed idx=%s/%s file=%s error=%s", idx, len(file_paths), file_path.name, str(e))
                
                if not continue_on_error:
                    break

        success_count = sum(1 for r in results if r.get('success'))
        logger.info("upload_batch done success=%s/%s", success_count, len(file_paths))
        return results


    def run_workflow(
        self,
        llm_id: int,
        user_prompt: str,
        user: Optional[str] = None,
        extra_inputs: Optional[Dict[str, Any]] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """执行workflow并返回结果"""
        if not isinstance(llm_id, int):
            raise ValueError("llm_id must be integer")
        if not user_prompt or not user_prompt.strip():
            raise ValueError("user_prompt must be non-empty string")

        # 构建请求数据
        inputs = {"llm_id": llm_id, "user_prompt": user_prompt}
        if extra_inputs:
            inputs.update(extra_inputs)

        payload = {
            "inputs": inputs,
            "response_mode": "blocking",
            "user": user or self.default_user
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        logger.info("workflow_run start llm_id=%s prompt_len=%s", llm_id, len(user_prompt))

        try:
            resp = requests.post(
                self.run_url,
                headers=headers,
                json=payload,
                stream=False,
                timeout=timeout
            )
            resp.raise_for_status()
            result = resp.json()
            
            status = result.get("data", {}).get("status", "unknown")
            logger.info("workflow_run done status=%s", status)
            return result

        except requests.exceptions.RequestException as e:
            logger.error("workflow_run failed error=%s", str(e))
            raise
        except Exception as e:
            logger.error("workflow_run error=%s", str(e))
            raise


def get_client(api_key: Optional[str] = None, user: Optional[str] = None) -> DifyWorkflowClient:
    """获取workflow客户端实例"""
    key = api_key or settings.DIFY_WORKFLOW_API_KEY
    if not key:
        raise ValueError("DIFY_WORKFLOW_API_KEY not configured")
    
    return DifyWorkflowClient(
        api_key=key,
        base_url=settings.DIFY_API_BASE_URL,
        default_user=user or settings.DIFY_WORKFLOW_USER
    )


def _extract_outputs(result: Dict[str, Any]) -> Dict[str, Any]:
    """从workflow结果中提取outputs"""
    data = result.get("data", {})
    outputs = data.get("outputs", {})
    
    if not outputs:
        logger.warning("workflow outputs empty")
        return {"error": "No output data", "raw_response": result}
    
    # 单键值直接返回
    if len(outputs) == 1:
        key = list(outputs.keys())[0]
        value = outputs[key]
        
        # 尝试解析JSON字符串
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        return value if isinstance(value, dict) else {key: value}
    
    return outputs


def analyze_summary(
    user_prompt: str,
    llm_id: int = 1,
    user: Optional[str] = None,
    extra_inputs: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """文本摘要分析"""
    client = get_client(api_key=api_key, user=user)
    
    logger.info("analyze_summary start llm_id=%s prompt_len=%s", llm_id, len(user_prompt))
    
    result = client.run_workflow(
        llm_id=llm_id,
        user_prompt=user_prompt,
        user=user,
        extra_inputs=extra_inputs
    )
    
    outputs = _extract_outputs(result)
    logger.info("analyze_summary done")
    return outputs


def upload_files(
    file_paths: List[Union[str, Path]],
    user: Optional[str] = None,
    api_key: Optional[str] = None,
    continue_on_error: bool = True
) -> List[Dict[str, Any]]:
    """批量上传文件"""
    client = get_client(api_key=api_key, user=user)
    return client.upload_files_batch(file_paths, user, continue_on_error)


def build_file_inputs(
    variable_name: str,
    file_ids: Optional[List[str]] = None,
    file_paths: Optional[List[Union[str, Path]]] = None,
    document_type: str = "document",
    user: Optional[str] = None,
    api_key: Optional[str] = None,
    auto_upload: bool = True
) -> Dict[str, List[Dict[str, str]]]:
    """构建workflow文件输入格式"""
    ids = list(file_ids) if file_ids else []
    
    # 自动上传本地文件
    if auto_upload and file_paths:
        upload_results = upload_files(file_paths, user, api_key, continue_on_error=True)
        
        for result in upload_results:
            if result.get('success'):
                ids.append(result['file_id'])
        
        if not ids:
            raise RuntimeError("All file uploads failed")
    
    # 构建文件列表
    file_list = [
        {
            "transfer_method": "local_file",
            "upload_file_id": file_id,
            "type": document_type
        }
        for file_id in ids
    ]
    
    return {variable_name: file_list}


def analyze_images(
    user_prompt: str,
    image_paths: Optional[List[Union[str, Path]]] = None,
    file_ids: Optional[List[str]] = None,
    llm_id: int = 2,
    user: Optional[str] = None,
    api_key: Optional[str] = None,
    auto_upload: bool = True
) -> Dict[str, Any]:
    """图像分析"""
    if not image_paths and not file_ids:
        raise ValueError("Require either image_paths or file_ids")
    
    client = get_client(api_key=api_key, user=user)
    
    # 构建图片输入
    extra_inputs = build_file_inputs(
        variable_name="images",
        file_ids=file_ids,
        file_paths=image_paths,
        document_type="image",
        user=user,
        api_key=api_key,
        auto_upload=auto_upload
    )
    
    logger.info("analyze_images start llm_id=%s image_count=%s prompt_len=%s", 
                llm_id, len(extra_inputs.get('images', [])), len(user_prompt))
    
    result = client.run_workflow(
        llm_id=llm_id,
        user_prompt=user_prompt,
        user=user,
        extra_inputs=extra_inputs
    )
    
    outputs = _extract_outputs(result)
    logger.info("analyze_images done")
    return outputs
