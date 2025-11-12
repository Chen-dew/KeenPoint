import os
import json
import asyncio
import aiohttp
import aiofiles
import zipfile
import io
from pathlib import Path

# =================== Configuration ===================
API_TOKEN = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI2OTMwMDM4MCIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2MjE0NzMxMywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiN2QyMWJjNjctOGI0ZC00YmQyLTgxMjItYmEzOWIxYWQ5MDZlIiwiZW1haWwiOiIiLCJleHAiOjE3NjMzNTY5MTN9.gZWhu-PKDvLA52rJn9n0hb8XpkYTeqG0bIDNJ3nRjLG7GoFhTUyb8RTPOg03jNxq9uvZPUElliFxqZyT2_20VA"
MODEL_VERSION = "pipeline"  # or vlm
FILE_PATHS = ["test.pdf"]
DOWNLOAD_DIR = "./downloads"
POLL_INTERVAL = 10  # seconds
UPLOAD_URL = "https://mineru.net/api/v4/file-urls/batch"
RESULT_URL = "https://mineru.net/api/v4/extract-results/batch"
# ======================================================

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_TOKEN}"
}

# -------------------------------------------
async def apply_upload_urls(session, file_paths):
    """Apply for batch upload URLs"""
    files_data = [{"name": os.path.basename(p), "data_id": os.path.basename(p)} for p in file_paths]
    payload = {"files": files_data, "model_version": MODEL_VERSION}

    async with session.post(UPLOAD_URL, headers=HEADERS, json=payload) as resp:
        result = await resp.json()
        if result.get("code") != 0:
            raise Exception(f"Failed to apply upload URLs: {result}")
        print(f"Successfully applied upload URLs: {result}")
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
                print(f"{file_path} uploaded successfully")
            else:
                text = await resp.text()
                print(f"{file_path} upload failed ({resp.status})\n{text}")
# -------------------------------------------
async def poll_result(session, batch_id):
    """Poll task status until all complete"""
    while True:
        async with session.get(f"{RESULT_URL}/{batch_id}", headers=HEADERS) as resp:
            result = await resp.json()
            if result.get("code") != 0:
                print(f"Failed to get task status: {result}")
                await asyncio.sleep(POLL_INTERVAL)
                continue

            done, running = [], []
            for item in result["data"]["extract_result"]:
                state = item["state"]
                name = item["file_name"]
                print(f"{name} status: {state}")
                if state == "done":
                    done.append(item)
                elif state not in ["failed"]:
                    running.append(item)

            if not running:
                return result["data"]["extract_result"]
        await asyncio.sleep(POLL_INTERVAL)

# -------------------------------------------
async def download_and_extract(session, file_info_list, output_dir):
    """Download ZIP and keep only md and images files"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for info in file_info_list:
        if info["state"] != "done":
            print(f"{info['file_name']} status={info['state']}, skipping")
            continue

        zip_url = info["full_zip_url"]
        filename = Path(info["file_name"]).stem
        extract_dir = Path(output_dir) / filename
        extract_dir.mkdir(parents=True, exist_ok=True)

        print(f"Downloading {zip_url}")
        async with session.get(zip_url) as resp:
            if resp.status != 200:
                print(f"Download failed: {resp.status}")
                continue

            zip_data = io.BytesIO(await resp.read())
        # Extract only md and images/ files
        with zipfile.ZipFile(zip_data, 'r') as zf:
            for member in zf.infolist():
                if member.filename.endswith(".md") or member.filename.startswith("images/"):
                    target_path = extract_dir / member.filename
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as source, open(target_path, "wb") as target:
                        target.write(source.read())

        print(f"{filename} extraction complete, kept only .md and images/")
        # Print summary
        md_files = list(extract_dir.rglob("*.md"))
        img_dirs = list(extract_dir.rglob("images"))
        for md in md_files:
            print(f"MD: {md}")
        for d in img_dirs:
            print(f"Images: {d}")
# -------------------------------------------
async def main():
    async with aiohttp.ClientSession() as session:
        print("Applying for upload URLs...")
        batch_id, urls = await apply_upload_urls(session, FILE_PATHS)
        print(f"batch_id = {batch_id}")

        print("Uploading files...")
        file_url = urls[0]  # Get first URL for single file
        await upload_file(session, FILE_PATHS[0], file_url)

        print("Waiting for parsing tasks to complete...")
        results = await poll_result(session, batch_id)

        print("Downloading and extracting results (keeping only md and images)...")
        await download_and_extract(session, results, DOWNLOAD_DIR)

        print("All tasks completed!")
# -------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())
