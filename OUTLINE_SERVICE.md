# 大纲分析服务 (Outline Service)

## 功能概述

`outline_service.py` 整合了三个核心服务的分析结果，生成结构化的PPT大纲：

1. **parse_service**: 提供章节结构和视觉元素引用
2. **nlp_service**: 提供文本摘要和关键点
3. **image_service**: 提供图表公式的详细解释

整合后调用 Dify 的 `analyze_outline` Agent 生成最终的PPT大纲结构。

## 数据流程

```
parse_service (章节结构 + refs)
       ↓
nlp_service (文本摘要)
       ↓
image_service (视觉元素分析)
       ↓
outline_service (整合数据 → Dify Agent → PPT大纲)
```

## 核心函数

### 1. build_outline_prompt

整合三个服务的数据，构建大纲分析的输入。

**输入**:
- `parse_result`: 文档解析结果（章节结构、refs）
- `text_analysis`: 文本分析结果（摘要、关键点）
- `visual_analysis`: 视觉元素分析结果（图表公式解释）

**输出**:
```json
[
  {
    "section_name": "1. Introduction",
    "section_path": "1. Introduction",
    "summary": "本节介绍研究背景...",
    "key_points": ["要点1", "要点2"],
    "refs": {
      "images": [
        {
          "id": 1,
          "caption": "图1: 系统架构",
          "ppt_content": {
            "title": "系统架构",
            "bullet_points": ["组件A", "组件B"]
          },
          "speaker_notes": {
            "explanation": "该图展示了...",
            "key_reasoning": ["原因1", "原因2"]
          }
        }
      ],
      "equations": [...],
      "tables": [...]
    }
  }
]
```

### 2. analyze_outline_with_dify

调用 Dify 的 `analyze_outline` Agent 分析大纲。

**输入**:
- `outline_inputs`: 来自 `build_outline_prompt` 的数据
- `skip_abstract`: 是否跳过Abstract章节（默认 True）

**输出**:
```json
[
  {
    "section_name": "1. Introduction",
    "section_path": "1. Introduction",
    "ppt_outline": [
      {
        "slide_title": "研究背景",
        "slide_purpose": "介绍研究领域的现状和挑战",
        "content_points": [
          "当前技术的局限性",
          "研究的必要性",
          "本文的创新点"
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
          "核心组件",
          "数据流程"
        ],
        "visual_refs": {
          "images": ["image_2"],
          "equations": ["equation_1"],
          "tables": []
        }
      }
    ]
  }
]
```

## 使用示例

### 完整流程

```python
from pathlib import Path
from app.services.parse_service import parse_markdown_for_summary
from app.services.nlp_service import extract_and_split_sections, analyze_segments_with_abstract
from app.services.image_service import extract_elements_with_context, analyze_elements_with_dify
from app.services.outline_service import build_outline_prompt, analyze_outline_with_dify

# 1. 解析文档
parse_result = parse_markdown_for_summary("document.md", "content_list.json")

# 2. 文本分析
abstract = ""  # 从parse_result中提取
segments = extract_and_split_sections(parse_result)
text_analysis = analyze_segments_with_abstract(segments, abstract)

# 3. 视觉元素分析
elements = extract_elements_with_context(parse_result)
visual_analysis = analyze_elements_with_dify(elements, base_path=Path("..."))

# 4. 构建大纲输入
outline_inputs = build_outline_prompt(parse_result, text_analysis, visual_analysis)

# 5. 生成PPT大纲
outline_results = analyze_outline_with_dify(outline_inputs)

# 6. 保存结果
import json
with open("outline_result.json", 'w', encoding='utf-8') as f:
    json.dump(outline_results, f, ensure_ascii=False, indent=2)
```

## 特性

### 1. 数据整合
- **章节匹配**: 通过 `section_name` 匹配文本分析结果
- **元素映射**: 通过 `{type}_{id}` 键匹配视觉元素分析
- **完整上下文**: 提供摘要、关键点、视觉元素解释的完整信息

### 2. 智能重试
- 最多重试 3 次
- 失败后提供详细的JSON格式要求
- 自动修复常见JSON格式错误

### 3. JSON解析增强
- 支持 markdown 代码块提取
- 智能识别JSON对象起始位置（避免LaTeX干扰）
- 修复无效转义字符
- 修复常见Agent格式错误

### 4. 日志输出
- 统一简洁风格（无emoji）
- 分析进度追踪
- 详细错误信息

## 输出结构说明

### ppt_outline 字段

每个章节生成多个幻灯片，每个幻灯片包含：

- **slide_title**: 幻灯片标题
- **slide_purpose**: 该幻灯片的目的/作用
- **content_points**: 内容要点（数组）
- **visual_refs**: 引用的视觉元素
  - `images`: 图片ID数组（如 `["image_1", "image_2"]`）
  - `equations`: 公式ID数组（如 `["equation_3"]`）
  - `tables`: 表格ID数组（如 `["table_1"]`）

## 配置要求

需要在 `.env` 中配置 Dify Outline API Key:

```env
DIFY_OUTLINE_API_KEY=app-xxxxxxxxxxxxx
```

## 测试

### 快速测试（仅构建prompt）

```bash
python test_outline_service.py prompt-only
```

### 完整流程测试

```bash
python test_outline_service.py
```

需要准备测试文件：
- `downloads/test/test.md`
- `downloads/test/test_content_list.json`

## 错误处理

### 常见错误

1. **无章节数据**
   ```
   logger.warning("无章节数据")
   return []
   ```

2. **JSON解析失败**
   - 自动重试最多3次
   - 返回包含 `parse_error` 字段的结果

3. **Agent分析失败**
   - 记录详细错误信息
   - 返回空的 `ppt_outline`

### 调试技巧

1. 检查中间结果：
   ```python
   # 保存outline_inputs查看构建的数据
   with open("debug_inputs.json", 'w') as f:
       json.dump(outline_inputs, f, ensure_ascii=False, indent=2)
   ```

2. 查看日志级别：
   ```python
   # 设置DEBUG级别查看详细JSON提取过程
   logger.setLevel(logging.DEBUG)
   ```

## 与其他服务的关系

```
parse_service.py
├── sections: 章节结构
├── fig_refs: 图片引用
├── table_refs: 表格引用
└── formula_refs: 公式引用

nlp_service.py
├── summary: 章节摘要
└── key_points: 关键点

image_service.py
├── ppt_content: PPT内容建议
└── speaker_notes: 演讲者备注

outline_service.py (整合)
└── ppt_outline: PPT结构化大纲
```

## 设计原则

- **高内聚**: 大纲生成逻辑集中在一个服务中
- **低耦合**: 通过标准数据格式与其他服务交互
- **统一风格**: 复用 JSON 解析、重试机制、日志输出模式
- **简洁严肃**: 无装饰性元素，专业规范

## 下一步扩展

可以基于 `ppt_outline` 结果：
1. 生成实际的PPT文件（.pptx）
2. 渲染幻灯片预览
3. 提供大纲编辑功能
4. 导出为其他格式（PDF、HTML等）
