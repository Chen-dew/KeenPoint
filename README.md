# KeenPoint

学术论文PPT生成后端服务

## 结构

```
app/
├── main.py              # FastAPI入口
├── api/
│   └── routes.py        # API路由
├── core/
│   ├── config.py        # 配置
│   └── logger.py        # 日志
└── services/
    ├── parse_service.py    # Markdown解析
    ├── nlp_service.py      # 文本分析
    ├── image_service.py    # 图表分析
    ├── outline_service.py  # 大纲生成
    └── clients/
        ├── dify_workflow_client.py  # Dify API
        └── mineru_client.py         # MinerU API
```

## 安装

```bash
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 为 `.env` 并填写API密钥

## 运行

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API

- `POST /api/v1/parse` - 解析Markdown文档
- `POST /api/v1/analyze/basic` - 提取文章基础信息
- `POST /api/v1/analyze/full` - 完整文档分析
- `POST /api/v1/analyze/images` - 图表分析
- `POST /api/v1/outline/build` - 构建大纲输入
- `POST /api/v1/outline/analyze` - 大纲分析
