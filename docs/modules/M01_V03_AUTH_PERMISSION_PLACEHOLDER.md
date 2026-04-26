# M01 v0.3 身份与权限预留

## 模块目标

继续沿用 demo 用户上下文，为 Agent Run、工具调用和文件访问保留权限字段。

## 当前 Step 1 范围

- 默认用户仍为 `demo_user`
- 默认部门仍为 `demo_department`
- 默认安全等级仍为 `normal`
- 复杂权限、正式角色和跨部门隔离降级为未来预留

## 后续调用约定

Agent Run 创建时应写入 `owner_user_id`、`department_id`、`security_level`，工具执行时只能访问同一任务空间内的资源。

## 非目标

- 不做真实登录
- 不做组织权限审批
- 不做多租户隔离
