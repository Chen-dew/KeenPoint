# 开发指南 🛠️

## 项目架构

### 分层架构

```
┌─────────────────────────────────────┐
│         API Layer (FastAPI)         │  ← 接口层
├─────────────────────────────────────┤
│       Business Logic (Services)     │  ← 业务逻辑层
├─────────────────────────────────────┤
│      Data Models (Pydantic/ORM)     │  ← 数据模型层
├─────────────────────────────────────┤
│    Core Utilities (Config/Logger)   │  ← 核心工具层
└─────────────────────────────────────┘
```

### 目录说明

```
app/
├── api/              # API 路由层 - 处理 HTTP 请求
│   ├── routes.py     # 路由聚合
│   ├── upload.py     # 文档上传接口
│   ├── analysis.py   # 分析接口
│   └── ...
│
├── services/         # 业务逻辑层 - 核心功能实现
│   ├── parser_service.py    # 文档解析
│   ├── nlp_service.py       # NLP 处理
│   └── ...
│
├── models/           # 数据模型层
│   ├── schema.py     # Pydantic 数据模型
│   └── db.py         # 数据库模型（预留）
│
└── core/             # 核心工具层
    ├── config.py     # 配置管理
    ├── logger.py     # 日志管理
    └── utils.py      # 工具函数
```

## 添加新功能

### 1. 添加新的 API 接口

**步骤**:

1. 在 `app/api/` 下创建新文件，例如 `new_feature.py`:

```python
from fastapi import APIRouter
from app.core.logger import logger

router = APIRouter()

@router.post("/new-endpoint")
async def new_endpoint(data: dict):
    """新接口的文档字符串"""
    logger.info("处理新功能...")
    return {"status": "success"}
```

2. 在 `app/api/routes.py` 中注册路由:

```python
from . import new_feature

router.include_router(
    new_feature.router,
    prefix="/new-feature",
    tags=["新功能"]
)
```

### 2. 添加新的服务

在 `app/services/` 下创建新服务文件:

```python
"""
新服务模块
"""
from app.core.logger import logger

def process_data(data: dict):
    """处理数据"""
    logger.info("开始处理数据...")
    # 实现业务逻辑
    return result
```

### 3. 添加新的数据模型

在 `app/models/schema.py` 中添加:

```python
class NewDataModel(BaseModel):
    """新数据模型"""
    field1: str
    field2: int
    field3: Optional[List[str]] = None
```

## 编码规范

### Python 代码风格

- 遵循 PEP 8 规范
- 使用 4 空格缩进
- 函数和变量使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_CASE

### 文档字符串

```python
def function_name(param1: str, param2: int) -> dict:
    """
    函数简要描述
    
    详细描述（可选）
    
    参数:
    - param1: 参数1的说明
    - param2: 参数2的说明
    
    返回:
    - dict: 返回值说明
    
    异常:
    - ValueError: 异常说明
    """
    pass
```

### 日志规范

```python
from app.core.logger import logger

# INFO: 常规信息
logger.info("✅ 操作成功")

# WARNING: 警告信息
logger.warning("⚠️ 注意事项")

# ERROR: 错误信息
logger.error("❌ 操作失败", exc_info=True)

# DEBUG: 调试信息
logger.debug("🔍 调试信息")
```

## 测试编写

### 单元测试

在 `tests/` 目录下创建测试文件:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_new_feature():
    """测试新功能"""
    response = client.post("/api/v1/new-feature/", json={"data": "test"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/test_upload.py

# 显示详细输出
pytest -v

# 生成覆盖率报告
pytest --cov=app tests/
```

## 配置管理

### 环境变量

在 `.env` 文件中添加配置:

```env
NEW_CONFIG_KEY=value
```

在 `app/core/config.py` 中读取:

```python
class Settings(BaseSettings):
    NEW_CONFIG_KEY: str = "default_value"
```

使用配置:

```python
from app.core.config import settings

value = settings.NEW_CONFIG_KEY
```

## 错误处理

### 标准错误响应

```python
from fastapi import HTTPException

# 400 Bad Request
raise HTTPException(status_code=400, detail="请求参数错误")

# 404 Not Found
raise HTTPException(status_code=404, detail="资源未找到")

# 500 Internal Server Error
raise HTTPException(status_code=500, detail="服务器内部错误")
```

### Try-Catch 模式

```python
try:
    result = risky_operation()
    logger.info("✅ 操作成功")
    return {"status": "success", "data": result}
except SpecificError as e:
    logger.error(f"❌ 特定错误: {str(e)}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"❌ 未知错误: {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail="服务器错误")
```

## 性能优化

### 1. 异步处理

对 I/O 密集型操作使用异步:

```python
async def process_file(file: UploadFile):
    content = await file.read()
    # 处理内容
    return result
```

### 2. 缓存策略

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_operation(param):
    # 耗时操作
    return result
```

### 3. 数据库查询优化

```python
# 使用索引
# 批量查询
# 避免 N+1 查询
```

## 数据库集成（未来）

### SQLAlchemy 集成

1. 在 `app/models/db.py` 中定义模型:

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    filename = Column(String)
```

2. 创建数据库连接:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
```

## 部署指南

### 本地开发

```bash
uvicorn app.main:app --reload
```

### 生产部署

```bash
# 使用 Gunicorn + Uvicorn Worker
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker 部署（未来）

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 调试技巧

### 1. 使用日志

```python
logger.debug(f"变量值: {variable}")
```

### 2. API 文档调试

访问 http://127.0.0.1:8000/docs 使用交互式文档测试

### 3. Python Debugger

```python
import pdb; pdb.set_trace()
```

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload

# 运行测试
pytest

# 代码格式化
black app/

# 代码检查
flake8 app/

# 类型检查
mypy app/
```

## 版本控制

### Git 工作流

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 提交更改
git add .
git commit -m "feat: 添加新功能"

# 合并到主分支
git checkout main
git merge feature/new-feature
```

### 提交信息规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

## 安全最佳实践

1. **永远不要在代码中硬编码密钥**
2. **使用环境变量存储敏感信息**
3. **验证所有用户输入**
4. **使用 HTTPS**
5. **实现速率限制**
6. **定期更新依赖**

## 监控与日志

### 日志级别

- DEBUG: 详细调试信息
- INFO: 常规信息
- WARNING: 警告信息
- ERROR: 错误信息
- CRITICAL: 严重错误

### 查看日志

```bash
# 实时查看日志
tail -f logs/app.log

# 搜索错误
grep ERROR logs/app.log
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 资源链接

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [PyMuPDF 文档](https://pymupdf.readthedocs.io/)
- [python-pptx 文档](https://python-pptx.readthedocs.io/)

---

**Happy Coding! 🎉**
