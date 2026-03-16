 # 迭代2: 数据库基础

> 配置数据库迁移工具和创建核心数据表

## 📋 迭代信息

- **迭代编号**: 2
- **预计时间**: 1天
- **当前状态**: ✅ 已完成
- **依赖迭代**: 迭代1 ✅
- **开始日期**: 2026-03-16
- **完成日期**: 2026-03-16

## 🎯 迭代目标

配置Alembic数据库迁移工具，创建用户认证相关的核心数据表。

## 📝 任务清单

### 1. Alembic配置 ✅

**任务**:
- [x] 初始化Alembic
- [x] 配置alembic.ini
- [x] 配置env.py连接数据库
- [x] 测试迁移命令

**交付物**:
- `alembic.ini` - Alembic配置文件 ✅
- `migrations/env.py` - 迁移环境配置 ✅
- `migrations/versions/` - 迁移脚本目录 ✅

### 2. 创建users表 ✅

**任务**:
- [x] 创建User模型 (SQLAlchemy)
- [x] 生成迁移脚本
- [x] 执行迁移
- [x] 验证表结构

**表结构**:
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    avatar_url VARCHAR(500),
    bio TEXT,
    wallet_balance DECIMAL(10, 2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_login_at TIMESTAMP
);
```

**交付物**:
- `src/infrastructure/persistence/models/user_model.py` ✅
- `migrations/versions/b2bb6046ad0f_create_users_table.py` ✅

### 3. 创建agents表 ✅

**任务**:
- [x] 创建Agent模型
- [x] 生成迁移脚本
- [x] 执行迁移
- [x] 验证表结构

**表结构**:
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    avatar VARCHAR(500),
    description TEXT,
    system_prompt TEXT,
    model_config JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**交付物**:
- `src/infrastructure/persistence/models/agent_model.py` ✅
- `migrations/versions/beb2eb35d009_create_agents_sessions_user_agents_.py` ✅

### 4. 创建sessions表 ✅

**任务**:
- [x] 创建Session模型
- [x] 生成迁移脚本
- [x] 执行迁移
- [x] 验证表结构

**表结构**:
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    refresh_token_hash VARCHAR(255),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP,
    last_accessed_at TIMESTAMP
);
```

**交付物**:
- `src/infrastructure/persistence/models/session_model.py` ✅
- `migrations/versions/beb2eb35d009_create_agents_sessions_user_agents_.py` ✅

### 5. 创建user_agents关联表 ✅

**任务**:
- [x] 创建UserAgent模型
- [x] 生成迁移脚本
- [x] 执行迁移
- [x] 验证表结构

**交付物**:
- `src/infrastructure/persistence/models/user_agent_model.py` ✅
- `migrations/versions/beb2eb35d009_create_agents_sessions_user_agents_.py` ✅

### 6. 数据库测试 ✅

**任务**:
- [x] 测试表创建
- [x] 测试外键约束
- [x] 测试索引
- [x] 编写数据库测试用例

**交付物**:
- `tests/integration/test_database_models.py` ✅
- `tests/conftest.py` ✅

## ✅ 验收标准

- [x] Alembic配置正确
- [x] 所有表创建成功
- [x] 外键约束正常工作
- [x] 索引创建成功
- [x] 迁移可以回滚
- [x] 测试用例通过

## 📊 进度追踪

- **总体进度**: 100%
- **开发进度**: 100%
- **测试进度**: 100%

## 🎉 完成总结

迭代2已成功完成！主要成果：

1. **Alembic配置完成**：
   - 配置了alembic.ini和env.py
   - 支持异步SQLAlchemy与同步Alembic的兼容
   - 创建了migrations目录结构

2. **数据库表创建**：
   - users表：13个字段，包含用户基本信息、钱包余额等
   - agents表：11个字段，包含JSONB类型的model_config
   - sessions表：7个字段，用于JWT认证会话管理
   - user_agents表：6个字段，用户与Agent的关联表

3. **约束和索引**：
   - 所有主键索引
   - 唯一约束：username, email, agent_id, token_hash, (user_id, agent_id)
   - 外键约束：agents.created_by, sessions.user_id, user_agents.user_id, user_agents.agent_id
   - CASCADE删除：sessions和user_agents在用户或Agent删除时自动删除

4. **迁移管理**：
   - 创建了2个迁移脚本
   - 测试了迁移回滚和升级功能
   - 验证了迁移的可逆性

5. **测试覆盖**：
   - 编写了11个集成测试用例
   - 测试了所有模型的CRUD操作
   - 测试了所有约束（唯一约束、外键约束、CASCADE删除）
   - 所有测试通过（11 passed in 0.23s）

## 📚 相关文档

- [数据库设计](../backend_development_plan.md#数据库设计)
- [Alembic文档](https://alembic.sqlalchemy.org/)

## 🔜 下一步

完成迭代2后，进入**迭代3: 用户认证-基础**

---

**创建日期**: 2026-03-15
**最后更新**: 2026-03-16
