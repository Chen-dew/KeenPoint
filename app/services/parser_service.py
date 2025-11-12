import os
import json
import asyncio
import aiohttp
import aiofiles
import zipfile
import io
from pathlib import Path
from app.core.config import settings
from app.core.logger import logger

# -------------------------------------------
async def apply_upload_urls(session, file_paths):
    """Apply for batch upload URLs"""
    files_data = [{"name": os.path.basename(p), "data_id": os.path.basename(p)} for p in file_paths]
    payload = {"files": files_data, "model_version": settings.MINERU_MODEL_VERSION}

    async with session.post(settings.MINERU_UPLOAD_URL, headers=settings.MINERU_HEADERS, json=payload) as resp:
        result = await resp.json()
        if result.get("code") != 0:
            raise Exception(f"Failed to apply upload URLs: {result}")
        logger.info(f"Successfully applied upload URLs: {result}")
        return result["data"]["batch_id"], result["data"]["file_urls"]

# -------------------------------------------
async def upload_file(session, file_path, url):
    """Upload a single file"""
    with open(file_path, 'rb') as f:
        # Disable auto Content-Type to use the pre-signed URL configuration
        async with session.put(
            url, 
            data=f,
            headers={'Content-Type': ''}  # Clear Content-Type
        ) as resp:
            if resp.status == 200:
                logger.info(f"{file_path} uploaded successfully")
            else:
                text = await resp.text()
                logger.error(f"{file_path} upload failed ({resp.status})\n{text}")
                
# -------------------------------------------
async def poll_result(session, batch_id):
    """Poll task status until all complete"""
    while True:
        async with session.get(f"{settings.MINERU_RESULT_URL}/{batch_id}", headers=settings.MINERU_HEADERS) as resp:
            result = await resp.json()
            if result.get("code") != 0:
                logger.warning(f"Failed to get task status: {result}")
                await asyncio.sleep(settings.MINERU_POLL_INTERVAL)
                continue

            done, running = [], []
            for item in result["data"]["extract_result"]:
                state = item["state"]
                name = item["file_name"]
                logger.info(f"{name} status: {state}")
                if state == "done":
                    done.append(item)
                elif state not in ["failed"]:
                    running.append(item)

            if not running:
                return result["data"]["extract_result"]
        await asyncio.sleep(settings.MINERU_POLL_INTERVAL)

# -------------------------------------------
async def download_and_extract(session, file_info_list, output_dir):
    """Download ZIP and keep only md and images files"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for info in file_info_list:
        if info["state"] != "done":
            logger.warning(f"{info['file_name']} status={info['state']}, skipping")
            continue

        zip_url = info["full_zip_url"]
        filename = Path(info["file_name"]).stem
        extract_dir = Path(output_dir) / filename
        extract_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading {zip_url}")
        async with session.get(zip_url) as resp:
            if resp.status != 200:
                logger.error(f"Download failed: {resp.status}")
                continue

            zip_data = io.BytesIO(await resp.read())
        # Extract only md and images/ files
        # with zipfile.ZipFile(zip_data, 'r') as zf:
        #     for member in zf.infolist():
        #         if member.filename.endswith(".md") or member.filename.startswith("images/"):
        #             target_path = extract_dir / member.filename
        #             target_path.parent.mkdir(parents=True, exist_ok=True)
        #             with zf.open(member) as source, open(target_path, "wb") as target:
        #                 target.write(source.read())

        # Extract all files from ZIP
        with zipfile.ZipFile(zip_data, 'r') as zf:
            logger.info(f"Extracting {len(zf.namelist())} files from ZIP...")
            for member in zf.infolist():
                # Skip directories
                if member.is_dir():
                    continue
                
                target_path = extract_dir / member.filename
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                with zf.open(member) as source, open(target_path, "wb") as target:
                    target.write(source.read())

        logger.info(f"{filename} extraction complete, kept only .md and images/")         
# -------------------------------------------
async def main(file_paths=None):
    """Main function to process PDF files
    
    Args:
        file_paths: List of PDF file paths to process. If None, uses default test file.
    """
    if file_paths is None:
        file_paths = ["D:\\MyFiles\\AIPPT\\Code\\keenPoint\\test.pdf"]
    
    async with aiohttp.ClientSession() as session:
        logger.info("Applying for upload URLs...")
        batch_id, urls = await apply_upload_urls(session, file_paths)
        logger.info(f"batch_id = {batch_id}")

        logger.info("Uploading files...")
        file_url = urls[0]  # Get first URL for single file
        await upload_file(session, file_paths[0], file_url)

        logger.info("Waiting for parsing tasks to complete...")
        results = await poll_result(session, batch_id)

        logger.info("Downloading and extracting results (keeping only md and images)...")
        await download_and_extract(session, results, settings.MINERU_DOWNLOAD_DIR)

        logger.info("All tasks completed!")
        
# -------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())
