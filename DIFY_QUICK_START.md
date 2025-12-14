# Dify 聊天与文件上传 - 快速开始

## 🚀 5 分钟快速开始

### 第 1 步：配置 API 密钥

在 `app/core/config.py` 中设置：
```python
DIFY_API_KEY: Optional[str] = "your-dify-api-key"
```

或在 `.env` 文件中：
```env
DIFY_API_KEY=your-api-key
```

### 第 2 步：导入函数

```python
from app.services.clients.dify_client import chat_with_images
```

### 第 3 步：上传并聊天（3 行代码）

```python
# 自动上传图片并进行聊天
for chunk in chat_with_images(
    query="这张图片是什么？",
    image_file_paths=["image.png"]
):
    print(chunk, end="", flush=True)
```

就这样！非常简单！

---

## 📚 常见使用场景

### 场景 1：分析单张图片

```python
from app.services.clients.dify_client import chat_with_images_blocking

result = chat_with_images_blocking(
    query="这张图片中有什么内容？",
    image_file_paths=["paper_figure.png"],
    auto_upload=True,
    user="researcher-001"
)

print(result['answer'])
```

### 场景 2：分析多张图片

```python
result = chat_with_images_blocking(
    query="对比这些图片的差异",
    image_file_paths=["image1.png", "image2.png", "image3.png"],
    auto_upload=True
)

print(result['answer'])
```

### 场景 3：继续之前的对话

```python
# 第一次对话
result1 = chat_with_images_blocking(
    query="这是什么图片？",
    image_file_paths=["image.png"],
    auto_upload=True
)

# 继续对话
result2 = chat_with_images_blocking(
    query="它的用途是什么？",
    conversation_id=result1['conversation_id'],
    auto_upload=False
)

print(result2['answer'])
```

### 场景 4：流式输出（实时显示）

```python
from app.services.clients.dify_client import chat_with_images

print("LLM 回复:")
for chunk in chat_with_images(
    query="分析这张图片",
    image_file_paths=["image.png"],
    auto_upload=True
):
    print(chunk, end="", flush=True)
```

---

## 🎯 核心函数速览

### 1. `upload_file_to_dify()` - 上传文件

```python
result = upload_file_to_dify("image.png")
file_id = result['id']  # 保存 file_id 供后续使用
```

**返回值：**
- `id`: 文件唯一 ID
- `name`: 文件名
- `size`: 文件大小
- `mime_type`: MIME 类型

---

### 2. `chat_with_images()` - 流式聊天

```python
for chunk in chat_with_images(
    query="问题内容",
    image_file_paths=["local_image.png"],  # 本地文件
    auto_upload=True,                      # 自动上传
    user="user-id"
):
    print(chunk, end="", flush=True)
```

**特点：** 实时流式输出，适合长回复

---

### 3. `chat_with_images_blocking()` - 阻塞模式聊天

```python
result = chat_with_images_blocking(
    query="问题内容",
    image_file_paths=["image.png"],
    auto_upload=True
)

print(result['answer'])           # LLM 的完整答案
print(result['conversation_id'])  # 用于继续对话
```

**特点：** 等待完整响应，返回字典

---

## 🔧 高级用法

### 使用已上传的文件 ID（避免重复上传）

```python
# 第一次：上传文件并获取 ID
result = upload_file_to_dify("image.png")
file_id = result['id']

# 保存 file_id...

# 第二次：直接使用 file_id，不再上传
for chunk in chat_with_images(
    query="新问题",
    image_file_ids=[file_id],
    auto_upload=False  # 重要：不要重复上传
):
    print(chunk, end="", flush=True)
```

### 自定义客户端

```python
from app.services.clients.dify_client import DifyClient

client = DifyClient(
    api_key="custom-api-key",
    base_url="https://custom.dify.ai/v1",
    user="custom-user"
)

# 现在可以使用 client 的所有方法
result = client.upload_file("image.png")
for chunk in client.chat_with_files(
    query="问题",
    file_ids=[result['id']]
):
    print(chunk, end="", flush=True)
```

### 批量上传

```python
from app.services.clients.dify_client import DifyClient

client = DifyClient()

results = client.batch_upload_files([
    "image1.png",
    "image2.jpg",
    "image3.png"
])

file_ids = [r['result']['id'] for r in results if r['success']]
```

---

## ⚙️ 完整 API 参数说明

### `chat_with_images()`

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `query` | str | ✅ | 用户问题 |
| `image_file_paths` | list | ❌ | 本地文件路径（auto_upload=True时） |
| `image_file_ids` | list | ❌ | 已上传文件 ID（auto_upload=False时） |
| `conversation_id` | str | ❌ | 对话 ID（继续对话时） |
| `inputs` | dict | ❌ | 应用变量值 |
| `user` | str | ❌ | 用户标识 |
| `auto_upload` | bool | ❌ | 是否自动上传（默认 True） |

### `chat_with_images_blocking()`

参数同上，但返回值不同（见下方）

---

## 📋 返回值格式

### 文件上传返回值

```python
{
    "id": "file-abc123",              # 文件 ID
    "name": "image.png",              # 文件名
    "size": 12345,                    # 大小（字节）
    "extension": "png",               # 扩展名
    "mime_type": "image/png",         # MIME 类型
    "created_by": "user-id",          # 创建者
    "created_at": 1234567890          # 创建时间
}
```

### 聊天返回值（阻塞模式）

```python
{
    "id": "msg-123",                  # 消息 ID
    "conversation_id": "conv-456",    # 对话 ID
    "answer": "LLM 回复的内容...",    # 完整答案
    "created_at": 1234567890          # 创建时间
}
```

### 聊天返回值（流式模式）

```
# 通过 yield 逐块返回，每块是一个 str
"LLM 回复的第一个单词" -> yield
"LLM 回复的第二个单词" -> yield
...
```

---

## ❌ 常见错误和解决方案

### 错误：`ValueError: Dify API key is required`

**解决：** 在 config.py 或 .env 中设置 DIFY_API_KEY

```python
# config.py
DIFY_API_KEY = "sk-your-actual-key"
```

### 错误：`FileNotFoundError: File not found`

**解决：** 确保文件路径正确

```python
import os
assert os.path.exists("image.png"), "文件不存在"
```

### 错误：`requests.exceptions.Timeout`

**解决：** 图片或查询太复杂，需要更长时间

```python
# 已默认设置 300 秒超时，无需修改
# 如需自定义，可在源代码中修改
```

### 错误：`RuntimeError: Dify API error`

**解决：** 检查 API 密钥和 Dify 应用配置

```python
# 确保：
# 1. API 密钥有效
# 2. Dify 应用支持图片输入
# 3. 网络连接正常
```

---

## 📊 性能优化建议

### 1. 缓存文件 ID

```python
# ❌ 低效：每次都上传同一个文件
for query in queries:
    result = chat_with_images(
        query=query,
        image_file_paths=["image.png"],
        auto_upload=True
    )

# ✅ 高效：只上传一次，重复使用
file_result = upload_file_to_dify("image.png")
file_id = file_result['id']

for query in queries:
    result = chat_with_images(
        query=query,
        image_file_ids=[file_id],
        auto_upload=False
    )
```

### 2. 使用流式模式显示长回复

```python
# ❌ 用户等待很久才看到第一个字
result = chat_with_images_blocking(query="...")
print(result['answer'])

# ✅ 立即开始显示回复
for chunk in chat_with_images(query="..."):
    print(chunk, end="", flush=True)
```

### 3. 批量处理多个文件

```python
# 使用 batch_upload_files 一次上传多个
from app.services.clients.dify_client import DifyClient

client = DifyClient()
results = client.batch_upload_files([
    "img1.png", "img2.png", "img3.png"
])

file_ids = [r['result']['id'] for r in results if r['success']]
```

---

## 📞 获取帮助

1. **查看完整文档：** `DIFY_UPLOAD_GUIDE.md`
2. **运行测试：** `python test_dify_chat.py`
3. **查看日志：** `logs/app.log`
4. **Dify 官方文档：** https://docs.dify.ai

---

## 📝 更新日志

### v1.0 (2025-12-09)
- ✅ 实现文件上传功能
- ✅ 实现流式聊天功能
- ✅ 实现阻塞模式聊天
- ✅ 支持对话连续性
- ✅ 完整的错误处理
- ✅ 日志记录功能

---

**祝你使用愉快！** 🎉
