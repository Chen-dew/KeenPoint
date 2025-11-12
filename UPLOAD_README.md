# 文件上传功能使用指南

## 📁 上传目录配置

文件将保存到: `D:\MyFiles\AIPPT\Code\keenPoint\uploads`

目录结构:
```
uploads/
  └── 20241112/          # 按日期组织
      ├── uuid1.pdf      # 上传的文件
      ├── uuid2.docx
      └── uuid3.txt
```

## 🚀 启动服务

### 1. 启动后端 API

**方法一：使用批处理脚本**
```bash
cd D:\MyFiles\AIPPT\Code\keenPoint
start_server.bat
```

**方法二：使用命令行**
```bash
cd D:\MyFiles\AIPPT\Code\keenPoint
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将运行在: `http://localhost:8000`

API 文档: `http://localhost:8000/docs`

### 2. 启动前端

```bash
cd D:\MyFiles\AIPPT\Code\keenPoint-web
npm run dev
```

前端服务将运行在: `http://localhost:5173`

## 📤 上传文件

### 通过前端界面

1. 打开浏览器访问 `http://localhost:5173`
2. 进入"文档上传"页面
3. 拖拽文件或点击"浏览文件"按钮选择文件
4. 点击"确认上传"按钮
5. 等待上传完成，查看结果

### 通过 API 测试

运行测试脚本:
```bash
cd D:\MyFiles\AIPPT\Code\keenPoint
python test_upload_api.py
```

或使用 curl:
```bash
curl -X POST "http://localhost:8000/api/v1/upload/" \
  -F "file=@your_file.pdf"
```

## 🔧 配置说明

### 后端配置 (app/core/config.py)

```python
UPLOAD_DIR: str = r"D:\MyFiles\AIPPT\Code\keenPoint\uploads"  # 上传目录
MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB 最大文件大小
ALLOWED_EXTENSIONS: list = ["pdf", "doc", "docx", "txt"]  # 允许的文件类型
```

### 前端配置 (src/pages/DocumentUpload.jsx)

```javascript
const API_URL = 'http://localhost:8000/api/v1/upload/'  // API 地址
const allowedExtensions = ['pdf', 'doc', 'docx', 'txt']  // 允许的文件类型
const maxFileSize = 50 * 1024 * 1024  // 50MB
```

## 📋 功能特性

### 前端功能
- ✅ 拖拽上传文件
- ✅ 点击浏览文件
- ✅ 文件类型验证 (.pdf, .doc, .docx, .txt)
- ✅ 文件大小验证 (最大 50MB)
- ✅ 上传进度显示
- ✅ 上传结果反馈（成功/失败）
- ✅ 显示文件信息（名称、大小、保存路径）
- ✅ 清空选择的文件
- ✅ 上传成功后启用"下一步"按钮

### 后端功能
- ✅ 文件接收与保存
- ✅ 文件类型验证
- ✅ 文件大小限制
- ✅ 按日期组织文件存储
- ✅ 生成唯一文件名 (UUID)
- ✅ 返回文件详细信息
- ✅ 错误处理与日志记录
- ✅ CORS 支持

## 🔍 API 接口文档

### 上传文件

**端点**: `POST /api/v1/upload/`

**请求**:
- Content-Type: `multipart/form-data`
- Body: `file` (文件)

**响应示例**:
```json
{
  "status": "success",
  "message": "文档上传成功",
  "file_info": {
    "filename": "paper.pdf",
    "file_path": "D:\\MyFiles\\AIPPT\\Code\\keenPoint\\uploads\\20241112\\uuid.pdf",
    "file_size": 1234567,
    "file_size_formatted": "1.18 MB",
    "file_type": "pdf",
    "upload_dir": "D:\\MyFiles\\AIPPT\\Code\\keenPoint\\uploads"
  }
}
```

**错误响应**:
```json
{
  "detail": "不支持的文件类型。请上传 PDF、Word 或 TXT 文档。"
}
```

## 🛠️ 故障排除

### 1. 后端无法启动
- 检查 Python 环境是否正确安装
- 确保安装了所有依赖: `pip install -r requirements.txt`
- 检查端口 8000 是否被占用

### 2. 前端无法连接后端
- 确保后端服务正在运行
- 检查 CORS 配置
- 验证 API URL 是否正确

### 3. 文件上传失败
- 检查文件格式是否支持
- 确认文件大小未超过 50MB
- 查看上传目录是否有写入权限
- 检查后端日志获取详细错误信息

### 4. 上传目录不存在
后端会自动创建目录，如果失败请手动创建:
```bash
mkdir D:\MyFiles\AIPPT\Code\keenPoint\uploads
```

## 📝 开发说明

### 修改上传目录

编辑 `app/core/config.py`:
```python
UPLOAD_DIR: str = r"你的路径"
```

### 修改允许的文件类型

后端 (`app/core/config.py`):
```python
ALLOWED_EXTENSIONS: list = ["pdf", "doc", "docx", "txt", "新类型"]
```

前端 (`src/pages/DocumentUpload.jsx`):
```javascript
const allowedExtensions = ['pdf', 'doc', 'docx', 'txt', '新类型']
```

### 修改文件大小限制

后端 (`app/core/config.py`):
```python
MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
```

前端 (`src/pages/DocumentUpload.jsx`):
```javascript
if (file.size > 100 * 1024 * 1024) { // 100MB
```

## 📊 日志查看

后端日志位置: `logs/app.log`

查看实时日志:
```bash
tail -f logs/app.log
```

## 🔗 相关链接

- 后端 API 文档: http://localhost:8000/docs
- 前端应用: http://localhost:5173
- GitHub 仓库: [链接]
