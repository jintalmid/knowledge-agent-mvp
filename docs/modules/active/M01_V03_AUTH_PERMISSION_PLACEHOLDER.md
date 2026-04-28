# M01 v0.3 身份与权限预留

## 模块目标

为后续企业用户、部门、权限、安全等级提供字段和服务边界。本阶段不实现真实登录和鉴权。

## 当前实现

后端使用默认用户上下文：

- `owner_user_id = demo_user`
- `department_id = demo_department`
- `security_level = normal`

默认上下文位于 `backend/app/core/auth.py`，任务、任务文件和 Agent Run 会继承这些字段。

## 涉及字段

`tasks`：

- `owner_user_id`
- `department_id`
- `security_level`

`task_files`：

- `owner_user_id`
- `department_id`
- `security_level`

`agent_runs`：

- `owner_user_id`
- `department_id`
- `security_level`

## 调用方式

业务服务需要用户上下文时，应从 M01 的默认上下文获取，不应在模块内部随意写死用户字段。

## 当前限制

- 所有请求视为同一个 demo 用户。
- 不校验部门隔离。
- 不校验资源权限。
- 不实现角色、组织、租户。

## 非目标

- 不做登录注册。
- 不做 OAuth / SSO。
- 不做 RBAC / ABAC。
- 不做多部门数据隔离。
