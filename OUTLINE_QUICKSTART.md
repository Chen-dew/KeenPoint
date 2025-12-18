# 快速参考：大纲分析服务

## 快速开始

### 1. 配置环境

```bash
# .env 文件
DIFY_OUTLINE_API_KEY=app-xxxxxxxxxxxxx
```

### 2. 完整示例代码

```python
from pathlib import Path
from app.services.parse_service import parse_markdown_for_summary
from app.services.nlp_service import extract_and_split_sections, analyze_segments_with_abstract
from app.services.image_service import extract_elements_with_context, analyze_elements_with_dify
from app.services.outline_service import build_outline_prompt, analyze_outline_with_dify
import json

# 设置路径
doc_dir = Path("downloads/test")
md_file = doc_dir / "test.md"
json_file = doc_dir / "test_content_list.json"

# 步骤1: 解析文档
parse_result = parse_markdown_for_summary(str(md_file), str(json_file))

# 步骤2: 文本分析
abstract = ""
for section in parse_result["sections"]:
    if "abstract" in section["name"].lower():
        abstract = section["content"]
        break

segments = extract_and_split_sections(parse_result)
text_analysis = analyze_segments_with_abstract(segments, abstract)

# 步骤3: 视觉元素分析
elements = extract_elements_with_context(parse_result)
visual_analysis = analyze_elements_with_dify(elements, base_path=doc_dir)

# 步骤4: 构建大纲输入
outline_inputs = build_outline_prompt(parse_result, text_analysis, visual_analysis)

# 步骤5: 生成大纲
outline_results = analyze_outline_with_dify(outline_inputs)

# 步骤6: 保存结果
with open("outline_result.json", 'w', encoding='utf-8') as f:
    json.dump(outline_results, f, ensure_ascii=False, indent=2)

print(f"生成了 {sum(len(r.get('ppt_outline', [])) for r in outline_results)} 个幻灯片")
```

## 核心API

### build_outline_prompt

**功能**: 整合三个服务的数据

**签名**:
```python
def build_outline_prompt(
    parse_result: Dict[str, Any],
    text_analysis: List[Dict[str, Any]],
    visual_analysis: List[Dict[str, Any]]
) -> List[Dict[str, Any]]
```

**返回**:
```python
[
  {
    "section_name": str,
    "section_path": str,
    "summary": str,
    "key_points": [str],
    "refs": {
      "images": [{"id", "caption", "ppt_content", "speaker_notes"}],
      "equations": [...],
      "tables": [...]
    }
  }
]
```

### analyze_outline_with_dify

**功能**: 调用Dify生成PPT大纲

**签名**:
```python
def analyze_outline_with_dify(
    outline_inputs: List[Dict[str, Any]],
    skip_abstract: bool = True
) -> List[Dict[str, Any]]
```

**返回**:
```python
[
  {
    "section_name": str,
    "section_path": str,
    "ppt_outline": [
      {
        "slide_title": str,
        "slide_purpose": str,
        "content_points": [str],
        "visual_refs": {
          "images": [str],
          "equations": [str],
          "tables": [str]
        }
      }
    ]
  }
]
```

## 数据结构速查

### parse_result (from parse_service)

```python
{
  "sections": [
    {
      "name": str,              # 章节名称
      "path": str,              # 完整路径
      "content": str,           # 文本内容
      "fig_refs": [             # 图片引用
        {"id": int, "caption": str, "img_path": str}
      ],
      "table_refs": [...],      # 表格引用
      "formula_refs": [...]     # 公式引用
    }
  ]
}
```

### text_analysis (from nlp_service)

```python
[
  {
    "id": str,
    "section_name": str,        # 章节名称（用于匹配）
    "summary": str,             # 摘要
    "key_points": [str]         # 关键点
  }
]
```

### visual_analysis (from image_service)

```python
[
  {
    "element": {
      "type": str,              # "image" | "table" | "equation"
      "id": int
    },
    "analysis": {
      "ppt_content": {
        "title": str,
        "bullet_points": [str],
        "highlight": str
      },
      "speaker_notes": {
        "explanation": str,
        "key_reasoning": [str],
        "interpretation_details": str
      }
    }
  }
]
```

## 常用场景

### 场景1: 仅测试数据整合（不调用Dify）

```python
from app.services.outline_service import build_outline_prompt

outline_inputs = build_outline_prompt(parse_result, text_analysis, visual_analysis)

# 保存用于检查
import json
with open("outline_inputs.json", 'w', encoding='utf-8') as f:
    json.dump(outline_inputs, f, ensure_ascii=False, indent=2)
```

### 场景2: 只处理特定章节

```python
# 过滤特定章节
target_sections = ["1. Introduction", "2. Method", "5. Conclusion"]
filtered_inputs = [
    inp for inp in outline_inputs 
    if inp["section_name"] in target_sections
]

outline_results = analyze_outline_with_dify(filtered_inputs)
```

### 场景3: 包含Abstract章节

```python
# 默认跳过Abstract，如需包含：
outline_results = analyze_outline_with_dify(outline_inputs, skip_abstract=False)
```

## 错误处理

### 检查解析错误

```python
for result in outline_results:
    if result.get("error"):
        print(f"错误: {result['section_name']} - {result['error']}")
    else:
        print(f"成功: {result['section_name']}")
```

### 查看原始响应

```python
for result in outline_results:
    if "raw_response" in result:
        print(f"\n原始响应 ({result['section_name']}):")
        print(result["raw_response"][:500])  # 前500字符
```

## 性能优化建议

### 1. 批量处理

```python
# 将章节分批处理，避免一次处理太多
batch_size = 5
for i in range(0, len(outline_inputs), batch_size):
    batch = outline_inputs[i:i+batch_size]
    batch_results = analyze_outline_with_dify(batch)
    all_results.extend(batch_results)
```

### 2. 缓存结果

```python
import pickle

# 保存中间结果
with open("outline_inputs.pkl", 'wb') as f:
    pickle.dump(outline_inputs, f)

# 下次直接加载
with open("outline_inputs.pkl", 'rb') as f:
    outline_inputs = pickle.load(f)
```

## 调试技巧

### 1. 查看详细日志

```python
import logging
from app.core.logger import logger

logger.setLevel(logging.DEBUG)
```

### 2. 验证数据完整性

```python
def validate_outline_inputs(inputs):
    for inp in inputs:
        assert "section_name" in inp
        assert "summary" in inp
        assert "refs" in inp
        
        refs = inp["refs"]
        for img in refs.get("images", []):
            assert "ppt_content" in img
            assert "speaker_notes" in img
    
    print("数据验证通过")

validate_outline_inputs(outline_inputs)
```

### 3. 统计信息

```python
def print_stats(outline_results):
    total_slides = 0
    for result in outline_results:
        slides = result.get("ppt_outline", [])
        total_slides += len(slides)
        
        total_refs = sum(
            len(slide.get("visual_refs", {}).get(key, []))
            for slide in slides
            for key in ["images", "equations", "tables"]
        )
        
        print(f"{result['section_name']}: {len(slides)} 幻灯片, {total_refs} 个引用")
    
    print(f"\n总计: {total_slides} 个幻灯片")

print_stats(outline_results)
```

## 测试命令

```bash
# 单元测试（数据整合逻辑）
python test_outline_integration.py

# 集成测试（仅构建prompt）
python test_outline_service.py prompt-only

# 完整流程测试（需要API Key）
python test_outline_service.py
```

## 相关文档

- **OUTLINE_SERVICE.md** - 详细功能说明
- **OUTLINE_SERVICE_SUMMARY.md** - 实现总结
- **WORKFLOW.md** - 完整工作流程
- **DIFY_CLIENT_REFACTOR.md** - Dify客户端重构说明

## 技术支持

遇到问题时的检查清单：

- [ ] `.env` 中配置了 `DIFY_OUTLINE_API_KEY`
- [ ] 输入数据格式正确（通过 `validate_outline_inputs` 验证）
- [ ] 日志级别设置为 DEBUG 查看详细信息
- [ ] 检查 Dify API 配额和连接状态
- [ ] 查看 `raw_response` 了解Agent的实际输出
