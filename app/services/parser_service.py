"""
文档解析服务
使用 MinerU API 进行文档解析
"""

import tempfile
import os
import zipfile
import aiohttp
import aiofiles
from app.core.logger import logger
from app.core.config import settings

async def parse_pdf_with_mineru(pdf_path: str, output_folder: str) -> str:
    """
    使用 MinerU API 解析 PDF 文件并提取文本和图像
    
    参数:
    - pdf_path: PDF 文件路径
    - output_folder: 保存提取内容的根目录
    
    返回:
    - str: 提取内容的文件夹路径
    """
    assert settings.MINERU_API is not None, "MINERU_API is not set"
    logger.info(f"Using MinerU API to parse PDF: {pdf_path}")
    
    os.makedirs(output_folder, exist_ok=True)

    # 读取 PDF 文件内容
    async with aiofiles.open(pdf_path, "rb") as f:
        pdf_content = await f.read()

    # 准备表单数据
    data = aiohttp.FormData()
    data.add_field(
        "files",
        pdf_content,
        filename=os.path.basename(pdf_path),
        content_type="application/pdf",
    )
    data.add_field("return_images", "True")
    data.add_field("response_format_zip", "True")

    # 准备请求头
    headers = {
        "Authorization": f"Bearer {settings.MINERU_TOKEN}"
    }

    # 发送请求到 MinerU API
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(settings.MINERU_API, data=data, headers=headers) as response:
                response.raise_for_status()
                content = await response.read()

                # 保存 ZIP 文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                    tmp.write(content)
                    zip_path = tmp.name

                logger.info("Received ZIP response, extracting files...")

                # 解压 ZIP 文件
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    # 获取顶层文件夹名称
                    top_level = {
                        name.split("/", 1)[0] for name in zip_ref.namelist() if name.strip()
                    }
                    if len(top_level) != 1:
                        raise RuntimeError("Expected exactly one top-level folder in zip")
                    prefix = list(top_level)[0] + "/"

                    # 提取所有文件
                    for member in zip_ref.infolist():
                        filename = member.filename
                        dest_path = os.path.join(
                            output_folder, filename.removeprefix(prefix)
                        )

                        if not member.is_dir():
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            with zip_ref.open(member) as src, open(dest_path, "wb") as dst:
                                dst.write(src.read())

                # 清理临时 ZIP 文件
                try:
                    os.unlink(zip_path)
                except:
                    pass

                logger.info(f"PDF parsing completed successfully, output folder: {output_folder}")
                return output_folder

        except aiohttp.ClientError as e:
            logger.error(f"MinerU API request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"PDF parsing failed: {str(e)}")
            raise

