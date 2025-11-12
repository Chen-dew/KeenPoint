# 配置集中化改进说明

## ✅ 已完成的改进

### 1. 配置文件更新 (app/core/config.py)

#### 新增配置项：
```python
# MinerU API 配置
MINERU_API_TOKEN: str = "..."          # API 认证令牌
MINERU_MODEL_VERSION: str = "pipeline"  # 模型版本
MINERU_UPLOAD_URL: str = "..."         # 上传 URL
MINERU_RESULT_URL: str = "..."         # 结果 URL
MINERU_POLL_INTERVAL: int = 10         # 轮询间隔（秒）
MINERU_DOWNLOAD_DIR: str = "./downloads"  # 下载目录

@property
def MINERU_HEADERS(self):
    """MinerU API request headers"""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.MINERU_API_TOKEN}"
    }
```

### 2. Parser Service 更新 (app/services/parser_service.py)

#### 改进前：
```python
# =================== Configuration ===================
API_TOKEN = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ..."
MODEL_VERSION = "pipeline"
FILE_PATHS = ["test.pdf"]
DOWNLOAD_DIR = "./downloads"
POLL_INTERVAL = 10
UPLOAD_URL = "https://mineru.net/api/v4/file-urls/batch"
RESULT_URL = "https://mineru.net/api/v4/extract-results/batch"
# ======================================================

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_TOKEN}"
}
```

#### 改进后：
```python
from app.core.config import settings
from app.core.logger import logger

# 直接使用 settings 对象访问配置
async def apply_upload_urls(session, file_paths):
    payload = {"files": files_data, "model_version": settings.MINERU_MODEL_VERSION}
    async with session.post(settings.MINERU_UPLOAD_URL, 
                           headers=settings.MINERU_HEADERS, 
                           json=payload) as resp:
        ...
```

---

## 📊 改进对比

| 方面 | 改进前 | 改进后 |
|------|--------|--------|
| **配置位置** | 分散在各个服务文件中 | 集中在 `config.py` |
| **配置管理** | 硬编码在代码中 | 使用 Pydantic Settings |
| **环境变量** | 不支持 | 支持从 `.env` 文件读取 |
| **Token 安全** | 明文硬编码 | 可从环境变量加载 |
| **Headers 构建** | 手动字典 | `@property` 自动生成 |
| **日志输出** | `print()` 语句 | 统一使用 `logger` |
| **可维护性** | 低（修改需要改多处） | 高（修改一处即可） |
| **可测试性** | 难以 Mock | 易于 Mock 和测试 |

---

## 🎯 优势

### 1. 集中管理
所有配置项都在 [`config.py`](app/core/config.py ) 中，一目了然。

### 2. 环境变量支持
可以通过 `.env` 文件配置：
```env
MINERU_API_TOKEN=your_token_here
MINERU_MODEL_VERSION=pipeline
MINERU_POLL_INTERVAL=10
```

### 3. 类型安全
使用 Pydantic 自动验证配置类型。

### 4. 统一日志
所有输出从 `print()` 改为 `logger.info/warning/error()`。

### 5. 易于扩展
新增配置只需在 `Settings` 类中添加属性。

---

## 📝 使用示例

### 访问配置
```python
from app.core.config import settings

# 获取 API Token
token = settings.MINERU_API_TOKEN

# 获取 Headers
headers = settings.MINERU_HEADERS

# 获取 URL
upload_url = settings.MINERU_UPLOAD_URL
```

### 在服务中使用
```python
async def my_function(session):
    async with session.post(
        settings.MINERU_UPLOAD_URL,
        headers=settings.MINERU_HEADERS,
        json=payload
    ) as resp:
        result = await resp.json()
```

### 修改配置（开发/测试）
```python
# 临时修改（仅用于测试）
settings.MINERU_POLL_INTERVAL = 5

# 或通过环境变量
import os
os.environ['MINERU_POLL_INTERVAL'] = '5'
```

---

## 🧪 测试配置

运行验证脚本：
```bash
python verify_config.py
```

预期输出：
```
================================================================================
Configuration Verification
================================================================================

[MinerU API Configuration]
  API Token: eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGk...
  Model Version: pipeline
  Upload URL: https://mineru.net/api/v4/file-urls/batch
  Result URL: https://mineru.net/api/v4/extract-results/batch
  Poll Interval: 10 seconds
  Download Dir: ./downloads

[MinerU Headers]
  Content-Type: application/json
  Authorization: Bearer eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ...

================================================================================
Configuration loaded successfully!
================================================================================
```

---

## 🔐 安全建议

### 1. 使用环境变量
创建 `.env` 文件（不要提交到 Git）：
```env
# MinerU API Configuration
MINERU_API_TOKEN=your_actual_token_here
MINERU_MODEL_VERSION=pipeline
```

### 2. 添加到 .gitignore
```
.env
*.env
.env.*
```

### 3. 使用示例文件
创建 `.env.example`（可以提交）：
```env
# MinerU API Configuration
MINERU_API_TOKEN=your_token_here
MINERU_MODEL_VERSION=pipeline
MINERU_POLL_INTERVAL=10
```

---

## 📂 文件结构

```
keenPoint/
├── app/
│   ├── core/
│   │   ├── config.py          ✅ 配置集中在这里
│   │   └── logger.py          ✅ 日志配置
│   └── services/
│       └── parser_service.py  ✅ 使用 settings 对象
├── .env                       ✅ 环境变量（不提交）
├── .env.example              ✅ 示例配置（可提交）
└── verify_config.py          ✅ 配置验证脚本
```

---

## ✅ 迁移清单

- [x] 将 API_TOKEN 移至 config.py (MINERU_API_TOKEN)
- [x] 将 MODEL_VERSION 移至 config.py (MINERU_MODEL_VERSION)
- [x] 将 UPLOAD_URL 移至 config.py (MINERU_UPLOAD_URL)
- [x] 将 RESULT_URL 移至 config.py (MINERU_RESULT_URL)
- [x] 将 POLL_INTERVAL 移至 config.py (MINERU_POLL_INTERVAL)
- [x] 将 DOWNLOAD_DIR 移至 config.py (MINERU_DOWNLOAD_DIR)
- [x] 将 HEADERS 改为 @property (MINERU_HEADERS)
- [x] 更新 parser_service.py 使用 settings
- [x] 将 print() 改为 logger.info/warning/error()
- [x] 添加 main() 函数参数支持
- [x] 创建配置验证脚本

---

## 🎉 完成！

所有配置项已成功集中到 [`app/core/config.py`](app/core/config.py ) 中！

现在可以：
1. ✅ 统一管理所有配置
2. ✅ 通过环境变量覆盖配置
3. ✅ 使用 Pydantic 进行类型验证
4. ✅ 更安全地管理敏感信息
5. ✅ 更容易进行单元测试
