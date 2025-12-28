"""Dify Workflow API客户端"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Generator

import requests

from app.core.config import settings
from app.core.logger import logger


MIME_TYPES = {
    'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
    'webp': 'image/webp', 'gif': 'image/gif', 'pdf': 'application/pdf'
}


class DifyClient:
    """Dify Workflow客户端"""
    
    def __init__(self, api_key: str, base_url: str = None, user: str = "keenpoint"):
        if not api_key:
            raise ValueError("api_key required")
        
        self.api_key = api_key
        self.base_url = (base_url or settings.DIFY_API_URL).rstrip("/")
        self.user = user
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    def upload(self, file_path: Union[str, Path]) -> Dict:
        """上传文件"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        ext = path.suffix.lower().lstrip('.')
        mime = MIME_TYPES.get(ext)
        if not mime:
            raise ValueError(f"Unsupported type: {ext}")
        
        with open(path, 'rb') as f:
            resp = requests.post(
                f"{self.base_url}/files/upload",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"file": (path.name, f, mime)},
                data={"user": self.user},
                timeout=300
            )
            resp.raise_for_status()
            return resp.json()
    
    def upload_batch(self, paths: List[Union[str, Path]], continue_on_error: bool = True) -> List[Dict]:
        """批量上传"""
        results = []
        for idx, p in enumerate(paths, 1):
            try:
                r = self.upload(p)
                results.append({"success": True, "file_path": str(p), "file_id": r.get("id")})
                logger.info(f"[DIFY] upload [{idx}/{len(paths)}] success: {Path(p).name}")
            except Exception as e:
                results.append({"success": False, "file_path": str(p), "error": str(e)})
                logger.error(f"[DIFY] upload [{idx}/{len(paths)}] failed: {e}")
                if not continue_on_error:
                    break
        return results
    
    def run(self, llm_id: int, prompt: str, extra: Dict = None, timeout: int = 300) -> Dict:
        """执行workflow"""
        inputs = {"llm_id": llm_id, "user_prompt": prompt}
        if extra:
            inputs.update(extra)
        
        payload = {"inputs": inputs, "response_mode": "blocking", "user": self.user}
        
        logger.info(f"[DIFY] run llm_id={llm_id} prompt_len={len(prompt)}")
        
        resp = requests.post(
            f"{self.base_url}/workflows/run",
            headers=self.headers,
            json=payload,
            timeout=timeout
        )
        resp.raise_for_status()
        return resp.json()

def _get_client(api_key: str = None, user: str = None) -> DifyClient:
    """获取客户端实例"""
    key = api_key or settings.DIFY_API_KEY
    if not key:
        raise ValueError("DIFY_API_KEY not configured")
    return DifyClient(key, settings.DIFY_API_URL, user or settings.DIFY_USER)


def _extract_output(result: Dict) -> Dict:
    """提取outputs"""
    outputs = result.get("data", {}).get("outputs", {})
    if not outputs:
        return {"error": "No output"}
    
    if len(outputs) == 1:
        val = list(outputs.values())[0]
        if isinstance(val, str):
            try:
                return json.loads(val)
            except:
                pass
        return val if isinstance(val, dict) else outputs
    return outputs


def upload_files(paths: List[Union[str, Path]], continue_on_error: bool = True) -> List[Dict]:
    """批量上传文件"""
    return _get_client().upload_batch(paths, continue_on_error)


def analyze_basic(query: str, llm_id: int = 0) -> Dict:
    """提取文章基础信息"""
    if not query or not query.strip():
        raise ValueError("query required")
    
    result = _get_client().run(llm_id, query)
    return _extract_output(result)


def analyze_summary(user_prompt: str, llm_id: int = 1) -> Dict:
    """文本摘要分析"""
    result = _get_client().run(llm_id, user_prompt)
    return _extract_output(result)


def analyze_images(user_prompt: str, file_ids: List[str] = None, 
                   image_paths: List[Union[str, Path]] = None,
                   llm_id: int = 2, auto_upload: bool = True, allow_empty_files: bool = False) -> Dict:
    """图像分析
    
    Args:
        user_prompt: 提示词
        file_ids: 文件ID列表
        image_paths: 图片路径列表
        llm_id: LLM ID
        auto_upload: 是否自动上传
        allow_empty_files: 是否允许空文件列表（用于纯文本分析，如公式）
    """
    ids = list(file_ids) if file_ids else []
    
    # 自动上传
    if auto_upload and image_paths:
        results = upload_files(image_paths)
        ids.extend([r["file_id"] for r in results if r.get("success")])
    
    # 检查是否有文件（equation等元素可能不需要文件）
    if not ids and not allow_empty_files:
        raise ValueError("No valid file_ids")
    
    # 构造extra参数（仅当有文件时）
    extra = None
    if ids:
        extra = {
            "images": [
                {"transfer_method": "local_file", "upload_file_id": fid, "type": "image"}
                for fid in ids
            ]
        }
    
    result = _get_client().run(llm_id, user_prompt, extra)
    return _extract_output(result)


def analyze_outline(query: str, llm_id: int = 3) -> Dict:
    """大纲分析"""
    result = _get_client().run(llm_id, query)
    return _extract_output(result)