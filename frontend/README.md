# Frontend

Next.js 前端负责展示任务空间、文件处理过程、LLM 配置、Agent Run 启动与详情、历史结果和 Debug 日志。

## 运行

```bash
cd frontend
npm install
npm run dev
```

默认访问：

```text
http://localhost:3000
```

## 配置后端地址

默认后端地址是：

```text
http://localhost:8000
```

如需覆盖：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

## 页面清单

- `/`: 项目入口。
- `/modules`: 模块注册表。
- `/modules/capability-check`: 阶段能力盘点页面。
- `/settings/llm`: LLM 配置状态与测试。
- `/debug/llm-logs`: LLM 调用日志。
- `/tasks`: 任务列表。
- `/tasks/[taskId]`: 任务详情和模块入口。
- `/tasks/[taskId]/files`: 文件上传、引用和去重状态。
- `/tasks/[taskId]/parsing`: 文件解析。
- `/tasks/[taskId]/summaries`: 文件摘要与标签。
- `/tasks/[taskId]/retrieval`: v0.2 临时检索兼容页面。
- `/tasks/[taskId]/ask`: v0.2 文本问答兼容页面。
- `/tasks/[taskId]/excel`: 单文件 Excel 沙箱分析。
- `/tasks/[taskId]/agent`: 启动 Agent Run。
- `/tasks/[taskId]/runs/[runId]`: Agent Run 每轮过程详情。
- `/tasks/[taskId]/results`: 历史结果、来源、复制 Markdown。

## 前端 API Client

`frontend/lib/api.ts` 封装全部 REST API 调用和 TypeScript 类型。

`frontend/lib/clipboard.ts` 提供复制 Markdown 的浏览器兼容 fallback，用于处理 `navigator.clipboard.writeText` 被内置浏览器拒绝的情况。

## 验证

```bash
npm run build
```

## 设计边界

- 前端不直接访问数据库或文件系统。
- 前端不保存 LLM key。
- 所有业务动作通过后端 REST API 完成。
- Agent Run 当前不是流式执行，页面在请求返回后跳转到详情。
