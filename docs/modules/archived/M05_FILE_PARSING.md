# M05_FILE_PARSING 文件解析

## 模块目标

将任务文件引用解析为后续摘要、检索、问答和 Excel 分析可消费的标准内容。当前阶段只做解析，不调用 LLM。

## 当前实现

- SQLite 表：`parsed_contents`
- 支持文本类文件：`txt`、`md`、`markdown`、`rst`、`log`、`json`、`xml`、`yaml`、`yml`、`html`、`htm`、`rtf`、`docx`、`pdf`
- 支持表格类文件：`csv`、`xlsx`、`xls`
- 文本类保存到 `text_content`
- CSV / Excel 保存结构化 `excel_profile_json`
- 更新 `task_files.parse_status`
- 前端页面：`/tasks/[taskId]/parsing`

## 数据字段

```text
id
task_file_id
physical_file_id
content_type
text_content
excel_profile_json
parse_quality
created_at
updated_at
```

## API

```text
POST /api/task-files/{task_file_id}/parse
POST /api/tasks/{task_id}/parse-all
GET /api/task-files/{task_file_id}/parsed-content
```

## 文本解析

`txt`、`md`、`markdown`、`rst`、`log`、`json`、`xml`、`yaml`、`yml`、`html`、`htm`、`rtf`、`docx`、`pdf` 文件读取为文本：

```text
content_type = text
text_content = 文件文本
parse_quality = ok
```

PDF 当前只支持可复制文本抽取，不做 OCR；扫描件图片 PDF 可能得到空文本。DOCX 当前抽取正文段落文本，不处理批注、修订痕迹或嵌入对象。

## CSV / Excel 解析

`csv`、`xlsx`、`xls` 文件生成 profile：

```text
content_type = excel
excel_profile_json = {
  format,
  sheet_count,
  sheets: [
    {
      sheet_name,
      row_count,
      column_count,
      columns,
      sample_rows
    }
  ]
}
```

字段类型为简单推断：`empty`、`integer`、`number`、`boolean`、`datetime`、`text`、`mixed`。

## 状态流转

```text
not_started -> parsing -> parsed
not_started -> parsing -> failed
```

## 非目标

不实现摘要、标签、Embedding、RAG、Excel 分析代码生成、文件预览下载或 LLM 调用。

## 调用边界

后续 M06 摘要与标签、M08 临时检索、M09 文本问答、M10 Excel 分析应读取 `parsed_contents`，不应重复读取 uploads 或绕过 M03/M04。
