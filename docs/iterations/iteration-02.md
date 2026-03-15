# 迭代2: 数据库基础

> 配置数据库迁移工具和创建核心数据表

## 📋 迭代信息

- **迭代编号**: 2
- **预计时间**: 1天
- **当前状态**: ⬜ 未开始
- **依赖迭代**: 迭代1
- **开始日期**: [待定]
- **预计完成**: [待定]

## 🎯 迭代目标

配置Alembic数据库迁移工具，创建用户认证相关的核心数据表。

## 📝 任务清单

### 1. Alembic配置

**任务**:
- [ ] 初始化Alembic
- [ ] 配置alembic.ini
- [ ] 配置env.py连接数据库
- [ ] 测试迁移命令

**交付物**:
- `alembic.ini` - Alembic配置文件
- `migrations/env.py` - 迁移环境配置
- `migrations/versions/` - 迁移脚本目录

### 2. 创建users表

**任务**:
- [ ] 创建User模型 (SQLAlchemy)
- [ ] 生成迁移脚本
- [ ] 执行迁移
- [ ] 验证表结构

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
- `src/infrastructure/persistence/models/user_model.py`
- `migrations/versions/xxx_create_users_table.py`

### 3. 创建agents表

**任务**:
- [ ] 创建Agent模型
- [ ] 生成迁移脚本
- [ ] 执行迁移
- [ ] 验证表结构

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
- `src/infrastructure/persistence/models/agent_model.py`
- `migrations/versions/xxx_create_agents_table.py`

### 4. 创建sessions表

**任务**:
- [ ] 创建Session模型
- [ ] 生成迁移脚本
- [ ] 执行迁移
- [ ] 验证表结构

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
- `src/infrastructure/persistence/models/session_model.py`
- `migrations/versions/xxx_create_sessions_table.py`

### 5. 创建user_agents关联表

**任务**:
- [ ] 创建UserAgent模型
- [ ] 生成迁移脚本
- [ ] 执行迁移
- [ ] 验证表结构

**交付物**:
- `src/infrastructure/persistence/models/user_agent_model.py`
- `migrations/versions/xxx_create_user_agents_table.py`

### 6. 数据库测试

**任务**:
- [ ] 测试表创建
- [ ] 测试外键约束
- [ ] 测试索引
- [ ] 编写数据库测试用例

## ✅ 验收标准

- [ ] Alembic配置正确
- [ ] 所有表创建成功
- [ ] 外键约束正常工作
- [ ] 索引创建成功
- [ ] 迁移可以回滚
- [ ] 测试用例通过

## 📊 进度追踪

- **总体进度**: 0%
- **开发进度**: 0%
- **测试进度**: 0%

## 📚 相关文档

- [数据库设计](../backend_development_plan.md#数据库设计)
- [Alembic文档](https://alembic.sqlalchemy.org/)

## 🔜 下一步

完成迭代2后，进入**迭代3: 用户认证-基础**

---

**创建日期**: 2026-03-15
**最后更新**: 2026-03-15
