# 迭代4: 用户认证-API

> 实现用户注册和登录API

## 📋 迭代信息

- **迭代编号**: 4
- **预计时间**: 1-2天
- **当前状态**: ⬜ 未开始
- **依赖迭代**: 迭代3

## 🎯 迭代目标

实现完整的用户注册和登录功能，包括领域层、应用层和接口层。

## 📝 任务清单

### 1. User领域层

**任务**:
- [ ] 创建User实体
- [ ] 创建UserId值对象
- [ ] 创建Email值对象
- [ ] 创建UserRepository接口
- [ ] 编写单元测试

**交付物**:
- `src/domain/user/entities/user.py`
- `src/domain/user/value_objects/user_id.py`
- `src/domain/user/value_objects/email.py`
- `src/domain/user/repositories/user_repository.py`

### 2. User应用层

**任务**:
- [ ] 创建RegisterUserCommand
- [ ] 创建LoginCommand
- [ ] 创建UserDTO
- [ ] 实现命令处理器
- [ ] 编写单元测试

**交付物**:
- `src/application/user/commands/register_user_command.py`
- `src/application/user/commands/login_command.py`
- `src/application/user/dtos/user_dto.py`

### 3. User基础设施层

**任务**:
- [ ] 实现PostgresUserRepository
- [ ] 实现数据库操作
- [ ] 编写集成测试

**交付物**:
- `src/infrastructure/persistence/repositories/postgres_user_repository.py`

### 4. Auth API接口

**任务**:
- [ ] 创建auth路由
- [ ] 实现POST /api/auth/register
- [ ] 实现POST /api/auth/login
- [ ] 实现POST /api/auth/logout
- [ ] 实现POST /api/auth/refresh
- [ ] 创建Pydantic schemas
- [ ] 编写API测试

**交付物**:
- `src/interfaces/api/rest/auth.py`
- `src/interfaces/api/schemas/auth_schema.py`

## ✅ 验收标准

- [ ] 用户可以成功注册
- [ ] 用户可以成功登录
- [ ] 返回正确的JWT Token
- [ ] Token可以刷新
- [ ] 所有测试通过

## 🔜 下一步

完成迭代4后，进入**迭代5: 用户管理**

---

**创建日期**: 2026-03-15
