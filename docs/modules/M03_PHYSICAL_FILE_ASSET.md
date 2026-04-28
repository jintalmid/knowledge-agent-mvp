# M03_PHYSICAL_FILE_ASSET 物理文件资产与去重

## 模块目标

管理上传后的物理文件资产，并基于 SHA256 `content_hash` 去重。不同任务或同一任务重复上传相同内容时，复用同一个 `physical_file`。

## 当前实现

- SQLite 表：`physical_files`
- 文件存储目录：`backend/uploads/{sha256}/`
- 支持文本类文件：`txt`、`md`、`markdown`、`rst`、`log`、`json`、`xml`、`yaml`、`yml`、`html`、`htm`、`rtf`、`docx`、`pdf`
- 支持表格类文件：`csv`、`xlsx`、`xls`
- 新文件保存到本地 uploads，重复文件只复用已有记录
- `ref_count` 记录当前任务文件引用数量

## 数据字段

```text
id
content_hash
original_filename
file_ext
mime_type
file_size
storage_path
ref_count
created_at
updated_at
```

## API

```text
GET /api/physical-files/{physical_file_id}
```

物理文件由 M04 的上传流程创建或复用。

## 删除策略

删除任务文件引用时只递减 `ref_count`。当 `ref_count = 0` 时，物理文件暂不删除，当前阶段通过引用数标记其可清理状态。

## 非目标

不实现文件解析、内容抽取、下载接口、物理清理任务、对象存储或权限隔离。

## 调用边界

其他模块不得直接写 uploads，应通过 M04 上传 API 创建任务文件引用，并由本模块负责物理文件去重。
