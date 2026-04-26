# 03 Orchestration Plan

## 阶段 0 定位

阶段 0 不实现正式调度器、后台任务队列、多 Agent 编排或自动补全流程。M12 只提供能力盘点：读取已有任务、文件、解析、摘要、检索、结果和日志数据，判断一个任务是否完成最小闭环。

## 最小闭环

阶段 0 的闭环顺序：

1. 创建任务空间
2. 上传文件并建立物理文件资产
3. 创建任务文件引用
4. 解析文件
5. 生成 LLM 摘要与标签
6. 准备临时检索上下文
7. 生成文本问答结果或 Excel 分析结果
8. 展示 Markdown 结果和来源文件
9. 查看 LLM 调用日志

## 检查 API

M12 暴露两个只读接口：

- `GET /api/tasks/{task_id}/capability-check`
- `GET /api/phase0/requirements`

`capability-check` 返回统一结构：

```json
{
  "task_id": "task_xxx",
  "phase": "phase_0",
  "steps": [
    {
      "step": "task_created",
      "status": "passed",
      "message": "...",
      "next_page": "/tasks/task_xxx"
    }
  ],
  "overall_status": "ready"
}
```

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

## 状态语义

- `passed`：该能力已有数据事实支撑
- `missing`：尚未执行对应步骤或缺少前置数据
- `failed`：存在失败状态，或数据关系异常

整体状态：

- `ready`：全部检查项通过
- `incomplete`：存在缺失项
- `failed`：存在失败项

## 页面

前端入口：

- `/modules/capability-check`

页面职责：

- 选择 task
- 展示阶段 0 检查流
- 显示每一步状态和说明
- 提供下一步页面跳转

## 非目标

- 不自动调用解析、摘要、问答或 Excel 分析
- 不创建后台任务
- 不实现正式工作流引擎
- 不做权限审批或跨部门编排

## 后续扩展

后续可在 M12 上增加轻量调度层，例如“按缺失项引导用户一键执行下一步”。但即使增加执行入口，也应继续复用各模块 API，不应绕过模块 service 边界。
