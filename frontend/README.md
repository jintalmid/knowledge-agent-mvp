# Frontend

Next.js 前端负责展示任务空间、文件处理过程、模型管理、模型路由、Agent Run 启动与详情、历史结果和 Debug 日志。

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

WSL 或局域网 IP 经常变化时，可以使用自动模式：

```bash
NEXT_PUBLIC_API_BASE_URL=auto:8000 npm run dev
```

此时浏览器会用当前页面的 host 访问后端。例如打开 `http://localhost:3000` 时访问 `http://localhost:8000`，打开 `http://<Windows 当前 IP>:3000` 时访问 `http://<Windows 当前 IP>:8000`。

在 Next.js 服务端渲染页面中，`auto:8000` 会转为 `http://127.0.0.1:8000`，用于让 `/modules` 这类服务端页面正常读取后端 API。

## 页面清单

- `/`: 项目入口。
- `/modules`: 模块注册表。
- `/modules/capability-check`: 阶段能力盘点页面。
- `/settings/models`: Provider 与模型管理。Provider 是接入通道，模型挂在 Provider 下；模型类型、能力 tags、context/output window 都在这里配置。
- `/settings/model-routing`: 场景模型路由。为 `default_text`、`file_summary`、`agent_planning`、`excel_code_generation` 等 scenario 选择模型。
- `/settings/llm`: legacy `.env` 配置状态与诊断入口。
- `/debug/llm-logs`: LLM 调用日志。
- `/tasks`: 任务列表。
- `/tasks/[taskId]`: 任务详情和模块入口。
- `/tasks/[taskId]/files`: 文件上传、自动解析状态、失败提示、重试入口、引用和去重状态。
- `/tasks/[taskId]/parsing`: 文件解析 Debug、批量重试、profile 和 text preview。
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

## 模型设置体验

- 宽屏使用左侧固定导航；模型相关页面会显示“模型设置”二级目录。
- 小屏使用点击式目录，不再把一级和二级入口横向平铺。
- 新增模型只能在某个 Provider 下发起，避免 Provider 和模型关系混乱。
- 模型类型和能力 tags 使用按钮式多选，不再依赖逗号分隔文本。
- 模型测试在 `/settings/models` 中执行，场景路由测试在 `/settings/model-routing` 中执行。
- `/settings/llm` 只用于查看 `.env` 种子配置和基础诊断，不是新的主配置入口。

## 验证

```bash
npm run build
```

## 设计边界

- 前端不直接访问数据库或文件系统。
- 前端不保存 LLM key。
- 所有业务动作通过后端 REST API 完成。
- Agent Run 当前不是流式执行，页面在请求返回后跳转到详情。
