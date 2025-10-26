# Academic Paper Assistant 🎓

一个基于 FastAPI 的 AI 学术论文辅助网站后端系统，提供论文解析、结构分析、图像管理和 PPT 自动生成功能。

## ✨ 核心功能

### 1. 📤 文档解析
- 支持上传 PDF 和 Word 文档
- 自动提取文本内容和元数据
- 批量文档处理

### 2. 🔍 结构分析
- 自动识别论文章节（Introduction、Methods、Results、Discussion、Conclusion）
- 关键词提取
- 自动摘要生成
- 图表统计

### 3. 🖼️ 图像管理
- 从 PDF 中提取图像
- 图像自动分类（图表、示意图、照片、公式）
- 图像导出（支持 ZIP 打包）

### 4. 📊 PPT 生成
- 根据论文结构自动生成演示文稿
- 多种模板选择（默认、学术、现代）
- PPT 样式自定义
- 支持导出下载

## 🚀 快速开始

### 环境要求
- Python 3.8+
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
uvicorn app.main:app --reload
```

或使用指定端口和主机：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 访问 API

- **API 文档**: http://127.0.0.1:8000/docs
- **ReDoc 文档**: http://127.0.0.1:8000/redoc
- **健康检查**: http://127.0.0.1:8000/health

## 📁 项目结构

```
keenPoint/
│
├── app/                          # 应用主目录
│   ├── __init__.py              # 应用初始化
│   ├── main.py                  # FastAPI 应用入口
│   │
│   ├── api/                     # API 路由层
│   │   ├── __init__.py
│   │   ├── routes.py            # 路由聚合器
│   │   ├── upload.py            # 文档上传接口
│   │   ├── analysis.py          # 结构分析接口
│   │   ├── image_manager.py     # 图像管理接口
│   │   └── ppt_generator.py     # PPT 生成接口
│   │
│   ├── core/                    # 核心配置模块
│   │   ├── config.py            # 应用配置
│   │   ├── logger.py            # 日志配置
│   │   └── utils.py             # 工具函数
│   │
│   ├── services/                # 业务逻辑层
│   │   ├── parser_service.py    # 文档解析服务
│   │   ├── nlp_service.py       # NLP 处理服务
│   │   ├── image_service.py     # 图像处理服务
│   │   └── ppt_service.py       # PPT 生成服务
│   │
│   ├── models/                  # 数据模型
│   │   ├── schema.py            # Pydantic 模型
│   │   └── db.py                # 数据库模型（预留）
│   │
│   └── static/                  # 静态文件目录
│
├── tests/                       # 测试目录
│   ├── test_upload.py           # 上传功能测试
│   ├── test_analysis.py         # 分析功能测试
│   └── test_ppt.py              # PPT 生成测试
│
├── uploads/                     # 上传文件存储（自动创建）
├── outputs/                     # 输出文件存储（自动创建）
├── logs/                        # 日志文件（自动创建）
│
├── requirements.txt             # Python 依赖
├── .env                         # 环境变量配置（需创建）
└── README.md                    # 项目文档
```

## 🔧 API 接口说明

### 1. 文档上传

**POST** `/api/v1/upload/`

上传 PDF 或 Word 文档并解析。

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/upload/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@paper.pdf"
```

### 2. 结构分析

**POST** `/api/v1/analysis/structure`

分析论文结构，识别章节。

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/analysis/structure" \
  -H "Content-Type: application/json" \
  -d '{"text": "Introduction\nThis paper...", "options": {}}'
```

### 3. 图像提取

**POST** `/api/v1/images/extract`

从 PDF 中提取图像。

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/images/extract?pdf_path=/path/to/paper.pdf"
```

### 4. PPT 生成

**POST** `/api/v1/ppt/generate`

根据论文结构生成 PPT。

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/ppt/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc_123",
    "structure_data": {
      "sections_detected": ["Introduction", "Methods", "Results"],
      "section_count": 3
    },
    "template": "academic"
  }'
```

## 🧪 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_upload.py

# 显示详细输出
pytest -v

# 生成覆盖率报告
pytest --cov=app tests/
```

## 🔐 环境变量配置

创建 `.env` 文件：

```env
# 应用配置
APP_NAME=Academic Paper Assistant
ENVIRONMENT=development
DEBUG=true

# 文件配置
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs
MAX_UPLOAD_SIZE=52428800

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 数据库配置（可选）
# DATABASE_URL=sqlite:///./database.db
```

## 📦 技术栈

- **Web 框架**: FastAPI
- **文档解析**: PyMuPDF, python-docx
- **PPT 生成**: python-pptx
- **数据验证**: Pydantic
- **测试框架**: pytest
- **ASGI 服务器**: Uvicorn

## 🔮 未来扩展

- [ ] 数据库集成（PostgreSQL/MongoDB）
- [ ] 用户认证与权限管理
- [ ] Redis 缓存支持
- [ ] 高级 NLP 模型集成（BERT、GPT）
- [ ] 实时协作功能
- [ ] Docker 容器化部署
- [ ] 前端界面开发（React/Vue）
- [ ] 云存储集成（AWS S3/阿里云 OSS）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📧 联系方式

如有问题或建议，请联系项目维护者。

---

**Enjoy coding! 🚀**
