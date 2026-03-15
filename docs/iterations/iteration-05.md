# 迭代5: 用户管理

> 实现用户信息的CRUD操作

## 📋 迭代信息

- **迭代编号**: 5
- **预计时间**: 1天
- **当前状态**: ⬜ 未开始
- **依赖迭代**: 迭代4

## 🎯 迭代目标

实现用户信息的查询、更新和删除功能。

## 📝 任务清单

### 1. User查询功能

**任务**:
- [ ] 创建GetUserQuery
- [ ] 创建GetCurrentUserQuery
- [ ] 实现查询处理器
- [ ] 编写测试

**交付物**:
- `src/application/user/queries/get_user_query.py`
- `src/application/user/queries/get_current_user_query.py`

### 2. User更新功能

**任务**:
- [ ] 创建UpdateUserCommand
- [ ] 实现命令处理器
- [ ] 编写测试

**交付物**:
- `src/application/user/commands/update_user_command.py`

### 3. User API接口

**任务**:
- [ ] 实现GET /api/users/me
- [ ] 实现PUT /api/users/me
- [ ] 实现GET /api/users/{user_id}
- [ ] 创建Pydantic schemas
- [ ] 编写API测试

**交付物**:
- `src/interfaces/api/rest/user.py`
- `src/interfaces/api/schemas/user_schema.py`

### 4. 集成到main.py

**任务**:
- [ ] 注册auth路由
- [ ] 注册user路由
- [ ] 测试完整流程

## ✅ 验收标准

- [ ] 可以获取当前用户信息
- [ ] 可以更新用户信息
- [ ] 需要认证才能访问
- [ ] 所有测试通过

## 🎉 里程碑1完成

完成迭代5后，**里程碑1: 用户认证系统**完成！

## 🔜 下一步

完成迭代5后，进入**迭代6: Agent管理**

---

**创建日期**: 2026-03-15
