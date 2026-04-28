# M12 调度与能力盘点

## 模块目标

提供阶段 0 最小闭环的只读能力盘点，帮助用户判断一个任务空间是否已经完成“上传、解析、摘要、检索、回答/分析、来源展示、LLM 日志”的验证链路。

## 当前 Step 8 范围

- 实现任务级能力检查 API
- 实现阶段 0 要求清单 API
- 实现前端页面 `/modules/capability-check`
- 每个检查项返回 `passed` / `missing` / `failed`
- 每个检查项返回下一步页面 `next_page`
- 不触发任何业务执行，不自动解析、摘要、检索、问答或分析

## 对外接口

### GET /api/tasks/{task_id}/capability-check

返回：

```json
{
  "task_id": "task_xxx",
  "phase": "phase_0",
  "steps": [
    {
      "step": "task_created",
      "status": "passed",
      "message": "任务空间已创建。",
      "next_page": "/tasks/task_xxx"
    }
  ],
  "overall_status": "ready"
}
```

`overall_status` 规则：

- `ready`：全部检查项为 `passed`
- `incomplete`：存在 `missing`，且不存在 `failed`
- `failed`：任一检查项为 `failed`

### GET /api/phase0/requirements

返回阶段 0 检查项、说明、关联模块和推荐页面模板。

## 检查项

- `task_created`
- `file_uploaded`
- `physical_file_deduplicated`
- `task_file_reference_created`
- `file_parsed`
- `summary_generated`
- `retrieval_available`
- `text_answer_generated_or_excel_analysis_generated`
- `result_has_sources`
- `llm_logs_available`

## 页面

`/modules/capability-check`

页面能力：

- 选择任务
- 展示阶段 0 流程检查
- 显示每一步状态
- 展示检查说明和关联模块
- 提供下一步页面跳转

## 非目标

- 不实现多 Agent 编排
- 不实现后台任务队列
- 不自动执行缺失步骤
- 不替代各业务模块页面

## 调用约定

其他模块如果需要判断当前任务是否具备阶段 0 闭环能力，应调用 `GET /api/tasks/{task_id}/capability-check`，不要直接复制 SQL 检查逻辑。
