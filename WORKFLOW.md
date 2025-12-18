# 完整的PPT生成工作流程

## 概览

```
PDF文档
   ↓
[MinerU解析]
   ↓
Markdown + JSON
   ↓
┌─────────────────────────────────────────┐
│         1. parse_service                │
│   ├─ 解析Markdown结构                    │
│   ├─ 提取章节层级                        │
│   └─ 识别图表公式引用                    │
└─────────────────────────────────────────┘
   ↓
parse_result: {sections, metadata}
   ↓
┌──────────────────┬──────────────────────┐
│                  │                      │
▼                  ▼                      ▼
┌─────────────────┐ ┌──────────────────┐ ┌────────────────┐
│ 2. nlp_service  │ │ 3. image_service │ │                │
│ ├─ 拆分超长章节  │ │ ├─ 提取元素上下文 │ │                │
│ ├─ 文本分析     │ │ ├─ 批量上传图片   │ │                │
│ └─ 生成摘要     │ │ └─ Dify图像分析  │ │                │
└─────────────────┘ └──────────────────┘ │                │
   ↓                      ↓               │                │
text_analysis         visual_analysis     │                │
   ↓                      ↓               │                │
   └──────────────────────┴───────────────┘
                          ↓
            ┌─────────────────────────────┐
            │    4. outline_service       │
            │    ├─ 整合三方数据           │
            │    ├─ 构建prompt            │
            │    └─ Dify大纲分析          │
            └─────────────────────────────┘
                          ↓
                  ppt_outline
                          ↓
            ┌─────────────────────────────┐
            │    5. ppt_service           │
            │    ├─ 生成幻灯片             │
            │    ├─ 应用模板              │
            │    └─ 导出PPTX              │
            └─────────────────────────────┘
                          ↓
                    final.pptx
```

## 详细数据流

### 阶段1: 文档解析 (parse_service)

**输入**:
- `document.md`: Markdown文档
- `content_list.json`: MinerU输出的内容列表

**处理**:
```python
parse_result = parse_markdown_for_summary(md_file, json_file)
```

**输出**:
```json
{
  "sections": [
    {
      "name": "1. Introduction",
      "level": 1,
      "path": "1. Introduction",
      "content": "文本内容...",
      "fig_refs": [
        {"id": 1, "caption": "图1", "img_path": "..."}
      ],
      "table_refs": [...],
      "formula_refs": [...]
    }
  ],
  "metadata": {
    "total_sections": 10,
    "total_figures": 5,
    "total_tables": 3,
    "total_formulas": 8
  }
}
```

### 阶段2A: 文本分析 (nlp_service)

**输入**:
- `parse_result`: 章节结构
- `abstract`: 摘要内容

**处理**:
```python
segments = extract_and_split_sections(parse_result)
text_analysis = analyze_segments_with_abstract(segments, abstract)
```

**中间结果 (segments)**:
```json
[
  {
    "id": "0",
    "name": "1. Introduction",
    "content": "内容...",
    "is_split": false,
    "total_parts": 1
  }
]
```

**输出 (text_analysis)**:
```json
[
  {
    "id": "0",
    "section_name": "1. Introduction",
    "summary": "本节介绍研究背景和动机",
    "key_points": ["要点1", "要点2", "要点3"]
  }
]
```

### 阶段2B: 视觉元素分析 (image_service)

**输入**:
- `parse_result`: 章节结构（包含refs）

**处理**:
```python
elements = extract_elements_with_context(parse_result)
visual_analysis = analyze_elements_with_dify(elements, base_path)
```

**中间结果 (elements)**:
```json
[
  {
    "abstract": "摘要内容",
    "element": {
      "type": "image",
      "id": 1,
      "img_path": "fig1.jpg",
      "caption": "图1: 系统架构"
    },
    "local_context": "上下文片段...",
    "section_content": "完整章节内容...",
    "section_name": "1. Introduction"
  }
]
```

**输出 (visual_analysis)**:
```json
[
  {
    "element": {"type": "image", "id": 1, ...},
    "analysis": {
      "element_id": 1,
      "element_type": "image",
      "ppt_content": {
        "title": "系统架构",
        "bullet_points": ["模块A", "模块B"],
        "highlight": "分层设计"
      },
      "speaker_notes": {
        "explanation": "详细说明...",
        "key_reasoning": ["原因1", "原因2"],
        "interpretation_details": "深入解释..."
      }
    },
    "error": null
  }
]
```

### 阶段3: 数据整合 (outline_service)

**输入**:
- `parse_result`: 章节结构
- `text_analysis`: 文本分析结果
- `visual_analysis`: 视觉元素分析结果

**处理 (步骤1: 构建prompt)**:
```python
outline_inputs = build_outline_prompt(
    parse_result, 
    text_analysis, 
    visual_analysis
)
```

**中间结果 (outline_inputs)**:
```json
[
  {
    "section_name": "1. Introduction",
    "section_path": "1. Introduction",
    "summary": "本节介绍研究背景和动机",
    "key_points": ["要点1", "要点2"],
    "refs": {
      "images": [
        {
          "id": 1,
          "caption": "图1: 系统架构",
          "ppt_content": {...},
          "speaker_notes": {...}
        }
      ],
      "equations": [...],
      "tables": [...]
    }
  }
]
```

**处理 (步骤2: 大纲分析)**:
```python
outline_results = analyze_outline_with_dify(outline_inputs)
```

**输出 (outline_results)**:
```json
[
  {
    "section_name": "1. Introduction",
    "section_path": "1. Introduction",
    "ppt_outline": [
      {
        "slide_title": "研究背景",
        "slide_purpose": "介绍研究领域现状",
        "content_points": [
          "当前技术局限",
          "研究必要性",
          "本文贡献"
        ],
        "visual_refs": {
          "images": ["image_1"],
          "equations": [],
          "tables": []
        }
      },
      {
        "slide_title": "系统架构",
        "slide_purpose": "展示提出的系统设计",
        "content_points": [
          "整体架构",
          "核心模块",
          "数据流程"
        ],
        "visual_refs": {
          "images": ["image_1"],
          "equations": ["equation_1"],
          "tables": []
        }
      }
    ]
  }
]
```

### 阶段4: PPT生成 (ppt_service)

**输入**:
- `outline_results`: 大纲结构
- `visual_analysis`: 视觉元素数据（用于嵌入图片）
- `template`: PPT模板（可选）

**处理**:
```python
ppt_file = generate_ppt(outline_results, visual_analysis, template)
```

**输出**:
- `presentation.pptx`: 最终的PowerPoint文件

## 数据映射关系

### 1. 章节文本映射

```
parse_result.sections[i].name
          ↓
text_analysis[j].section_name
          ↓
outline_inputs[k].section_name
          ↓
outline_results[k].section_name
```

### 2. 视觉元素映射

```
parse_result.sections[i].fig_refs[m].id
          ↓
visual_analysis[n].element.id
          ↓
outline_inputs[k].refs.images[p].id
          ↓
outline_results[k].ppt_outline[q].visual_refs.images[]
```

**映射键**: `f"{element_type}_{element_id}"` (如 `image_1`)

## 关键设计模式

### 1. 数据传递模式

```
结构化数据 → JSON序列化 → Dify Agent → JSON解析 → 结构化结果
```

### 2. 错误处理模式

```python
max_retries = 3
for retry in range(max_retries):
    try:
        # 调用Agent
        result = analyze(prompt)
        
        # 验证结果
        if result.get("parse_error"):
            raise ValueError("解析失败")
        
        return result
    
    except Exception as e:
        if retry < max_retries:
            # 重新构造prompt
            prompt = rebuild_with_format_hints(original_prompt)
        else:
            # 记录错误，返回默认结果
            return default_result
```

### 3. 日志输出模式

```python
# 开始阶段
logger.info(f"开始处理: {count} 个项目")

# 处理中
logger.debug(f"处理进度 [{idx}/{total}]: {item_name}")

# 完成阶段
logger.info(f"处理完成: 成功 {success}/{total}")
```

## 配置要求

### 环境变量

```env
# Dify API Keys
DIFY_IMAGE_API_KEY=app-xxxxx  # 图像分析Agent
DIFY_TEXT_API_KEY=app-xxxxx   # 文本分析Agent
DIFY_OUTLINE_API_KEY=app-xxxxx # 大纲分析Agent

# Dify配置
DIFY_API_BASE_URL=https://api.dify.ai/v1
DIFY_USER=default-user
```

### 目录结构

```
project/
├── app/
│   ├── services/
│   │   ├── parse_service.py      # 文档解析
│   │   ├── nlp_service.py        # 文本分析
│   │   ├── image_service.py      # 视觉分析
│   │   ├── outline_service.py    # 大纲生成
│   │   └── ppt_service.py        # PPT生成
│   │   └── clients/
│   │       └── dify_client.py    # Dify客户端
│   └── core/
│       ├── config.py              # 配置管理
│       └── logger.py              # 日志管理
├── downloads/                     # 文档存储
│   └── test/
│       ├── test.md
│       └── test_content_list.json
└── outputs/                       # 结果输出
    ├── outline_inputs.json
    ├── outline_results.json
    └── presentation.pptx
```

## 性能指标

### 处理时间（估算）

- **文档解析**: ~1秒
- **文本分析**: ~5秒/章节
- **视觉分析**: ~3秒/元素
- **大纲生成**: ~8秒/章节
- **PPT生成**: ~2秒

### 示例（10章节，15个视觉元素）

- 总时间: ~150秒（约2.5分钟）
- 可通过并行处理优化到 ~60秒

## 扩展点

### 1. 新增分析维度

```python
# 在outline_service中添加新的数据源
def build_outline_prompt(..., additional_analysis):
    section_input["additional_data"] = additional_analysis_map.get(section_name)
```

### 2. 自定义大纲格式

```python
# 修改Dify Agent的输出schema
# 在_parse_outline_response中适配新格式
```

### 3. 多语言支持

```python
# 在各服务中添加语言参数
def analyze_segments(..., language="zh-CN"):
    prompt = build_prompt_for_language(language)
```

## 总结

整个流程通过4个核心服务协作完成：

1. **parse_service**: 提供结构化的章节和元素引用
2. **nlp_service**: 提供文本摘要和关键点
3. **image_service**: 提供视觉元素的详细解释
4. **outline_service**: 整合数据并生成PPT大纲

每个服务都遵循统一的设计原则：高内聚、低耦合、简洁严肃。通过标准的JSON格式传递数据，确保了系统的可维护性和可扩展性。
