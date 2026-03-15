# 迭代3: 用户认证-基础

> 实现JWT Token服务和密码加密服务

## 📋 迭代信息

- **迭代编号**: 3
- **预计时间**: 1天
- **当前状态**: ⬜ 未开始
- **依赖迭代**: 迭代2
- **开始日期**: [待定]

## 🎯 迭代目标

实现用户认证的基础设施：JWT Token生成/验证和密码加密/验证。

## 📝 任务清单

### 1. 密码加密服务

**任务**:
- [ ] 创建PasswordHasher类
- [ ] 实现hash_password方法
- [ ] 实现verify_password方法
- [ ] 编写单元测试

**交付物**:
- `src/infrastructure/security/password_hasher.py`

### 2. JWT Token服务

**任务**:
- [ ] 创建JWTService类
- [ ] 实现create_access_token方法
- [ ] 实现create_refresh_token方法
- [ ] 实现verify_token方法
- [ ] 实现decode_token方法
- [ ] 编写单元测试

**交付物**:
- `src/infrastructure/security/jwt_service.py`

### 3. 认证中间件

**任务**:
- [ ] 创建AuthMiddleware
- [ ] 实现token验证逻辑
- [ ] 实现用户信息注入
- [ ] 处理认证异常
- [ ] 编写测试用例

**交付物**:
- `src/infrastructure/security/auth_middleware.py`

### 4. 认证依赖

**任务**:
- [ ] 创建get_current_user依赖
- [ ] 创建get_current_active_user依赖
- [ ] 编写测试用例

**交付物**:
- `src/interfaces/api/dependencies.py`

## ✅ 验收标准

- [ ] 密码可以正确加密和验证
- [ ] JWT Token可以正确生成和验证
- [ ] 中间件可以正确验证请求
- [ ] 所有测试用例通过

## 🔜 下一步

完成迭代3后，进入**迭代4: 用户认证-API**

---

**创建日期**: 2026-03-15
