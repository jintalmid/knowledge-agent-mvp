# M01_AUTH_PERMISSION_PLACEHOLDER 身份与权限预留

## 模块目标

在阶段 0 中提供固定的演示身份上下文，让任务空间的数据模型提前包含用户、部门和安全等级字段。

## 当前实现

- 暂不做真实登录
- 所有 API 使用默认用户上下文
- 后端依赖边界位于 `app.core.auth`

## 默认身份

```text
owner_user_id = demo_user
department_id = demo_department
security_level = normal
```

## 被调用方式

后端业务接口通过 `get_current_user()` 获取当前用户上下文。

## 非目标

不实现登录、注册、JWT、Session、多部门权限、角色权限、知识库权限或租户隔离。

## 扩展预留

后续真实鉴权接入时，应保持任务模型中的 `owner_user_id`、`department_id`、`security_level` 字段语义稳定，并替换 `get_current_user()` 的实现。
