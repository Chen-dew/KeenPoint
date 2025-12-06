# Parse Service 输出数据结构

## 顶层结构

```json
{
  "sections": [],
  "figures": [],
  "formulas": [],
  "tables": [],
  "metadata": {}
}
```

## 详细字段说明

### 1. sections (章节数组)

扁平结构的章节列表，每个章节包含：

```json
{
  "name": "4.2.1 Results on CIFAR-10",
  "level": 3,
  "path": "4. Experiments > 4.2. Results and Analysis > 4.2.1 Results on CIFAR-10",
  "content": "章节的文本内容（不含标题行）",
  "word_count": 1523,
  "direct_char_count": 10632,
  "total_char_count": 10632,
  "fig_refs": [1, 2],
  "table_refs": [1, 2, 3],
  "formula_refs": [4, 5]
}
```

字段说明：
- `name`: 完整标题（含数字编号）
- `level`: 层级（基于数字编号，如 4.2.1 为 level 3）
- `path`: 完整路径（从根到当前节点）
- `content`: 章节文本内容
- `word_count`: 字数（中文按字符，英文按单词）
- `direct_char_count`: 当前章节字符数
- `total_char_count`: 包含所有子章节的总字符数
- `fig_refs`: 章节中引用的图片ID数组
- `table_refs`: 章节中引用的表格ID数组
- `formula_refs`: 章节中引用的公式ID数组

### 2. figures (图片数组)

从JSON或Markdown提取的图片列表：

```json
{
  "type": "image",
  "id": 1,
  "img_path": "images/figure1.jpg",
  "caption": "Figure 1. Framework of HRank."
}
```

字段说明：
- `type`: 固定值 "image"
- `id`: 图片ID（从1开始递增）
- `img_path`: 图片路径
- `caption`: 图片标题/说明

### 3. formulas (公式数组)

从JSON或Markdown提取的公式列表（仅块级公式）：

**JSON来源：**
```json
{
  "type": "equation",
  "id": 1,
  "img_path": "images/equation1.jpg",
  "text": "$$\\begin{array}...",
  "text_format": "latex"
}
```

**Markdown来源：**
```json
{
  "id": 1,
  "type": "block",
  "text": "$$\n\\alpha = \\beta + \\gamma\n$$",
  "position": 1523
}
```

字段说明：
- `type`: "equation" (JSON) 或 "block" (Markdown)
- `id`: 公式ID（从1开始递增）
- `img_path`: 公式图片路径（仅JSON）
- `text`: 公式LaTeX文本
- `text_format`: 格式，通常为 "latex"（仅JSON）
- `position`: 公式在文档中的位置（仅Markdown）

### 4. tables (表格数组)

从JSON或Markdown提取的表格列表：

**JSON来源：**
```json
{
  "type": "table",
  "id": 1,
  "img_path": "images/table1.jpg",
  "caption": "Table 1. Pruning results of VGGNet on CIFAR-10.",
  "body": "<table><tr><td>Model</td>...</table>"
}
```

**Markdown来源：**
```json
{
  "id": 1,
  "caption": "Table 1. Results",
  "body": "<table>...</table>",
  "img_path": null,
  "position": 5234
}
```

字段说明：
- `type`: 固定值 "table"（仅JSON）
- `id`: 表格ID（从1开始递增）
- `img_path`: 表格截图路径
- `caption`: 表格标题
- `body`: 表格HTML内容
- `position`: 表格在文档中的位置（仅Markdown）

### 5. metadata (元数据)

文档统计信息：

```json
{
  "total_sections": 15,
  "total_figures": 7,
  "total_formulas": 6,
  "total_tables": 5,
  "total_words": 8523,
  "top_level_sections": 6
}
```

字段说明：
- `total_sections`: 总章节数
- `total_figures`: 总图片数
- `total_formulas`: 总公式数
- `total_tables`: 总表格数
- `total_words`: 总字数
- `top_level_sections`: 顶层章节数（level=1）

## 数据来源

### JSON优先模式
当提供MinerU的JSON文件时：
- `figures`、`formulas`、`tables` 从JSON提取
- 数据包含 `type` 字段和 `img_path`

### Markdown降级模式
当没有JSON文件时：
- 从Markdown文本中提取
- 数据包含 `position` 字段
- 缺少图片路径信息

## 章节匹配规则

通过Markdown文本内容匹配ID：

1. **图片匹配**：检测 "Figure 1", "Fig. 1", "图1" 等引用
2. **表格匹配**：检测 "Table 1", "Tab. 1", "表1" 等引用
3. **公式匹配**：检测公式文本片段（前30字符）在章节中出现

## 使用示例

```python
from app.services.parse_service import parse_markdown_file

# 带JSON文件
result = parse_markdown_file(
    "path/to/file.md",
    "path/to/content_list.json"
)

# 仅Markdown
result = parse_markdown_file("path/to/file.md")

# 访问数据
for section in result["sections"]:
    print(f"{section['name']} - Level {section['level']}")
    print(f"  Path: {section['path']}")
    print(f"  Figures: {section['fig_refs']}")
    print(f"  Tables: {section['table_refs']}")
```
