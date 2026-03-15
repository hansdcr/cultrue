# 快速开始

> 5分钟快速搭建Cultrue开发环境

## 📋 前置要求

- Python 3.12+
- PostgreSQL 15+
- Redis 5.0+
- uv (Python包管理器)

## 🚀 快速安装

### 1. 克隆项目

```bash
cd /Users/gelin/Desktop/store/dev/python/ai/cultrue
```

### 2. 安装依赖

```bash
# 使用uv安装依赖
uv pip install -e .

# 或使用pip
pip install -e .
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，配置数据库连接等
vim .env
```

**最小配置**:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cultrue
JWT_SECRET_KEY=your-secret-key-change-this
REDIS_URL=redis://localhost:6379/0
```

### 4. 启动服务

```bash
# 开发模式启动
python main.py

# 或使用uvicorn
uvicorn main:app --reload
```

### 5. 验证安装

访问以下URL验证服务：

- 应用信息: http://localhost:8000/
- 健康检查: http://localhost:8000/health
- API文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc

## 📦 数据库设置

### 创建数据库

```bash
# 连接PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE cultrue;

# 创建用户（如果需要）
CREATE USER cultrue_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE cultrue TO cultrue_user;
```

### 运行迁移

```bash
# 初始化Alembic（仅第一次）
alembic init migrations

# 生成迁移脚本
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

## 🧪 运行测试

```bash
# 安装测试依赖
uv pip install -e ".[dev]"

# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 🔧 开发工具

### 代码格式化

```bash
# 安装black
pip install black

# 格式化代码
black src/ tests/
```

### 代码检查

```bash
# 安装ruff
pip install ruff

# 检查代码
ruff check src/ tests/

# 自动修复
ruff check --fix src/ tests/
```

### 类型检查

```bash
# 安装mypy
pip install mypy

# 类型检查
mypy src/ main.py
```

## 📖 下一步

1. 阅读 [项目概览](./project_overview.md) 了解项目架构
2. 查看 [迭代计划](./iterations/README.md) 了解开发进度
3. 阅读 [编码规范](./coding_standards.md) 熟悉开发规范
4. 选择一个任务开始开发

## 🐛 常见问题

### Q: 启动时报错 "No module named 'greenlet'"

**A**: 安装greenlet包
```bash
uv pip install greenlet
```

### Q: 数据库连接失败

**A**: 检查以下几点：
1. PostgreSQL服务是否启动
2. 数据库是否已创建
3. .env中的DATABASE_URL是否正确
4. 用户权限是否足够

### Q: Redis连接失败

**A**: 检查Redis服务是否启动
```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis
```

## 📞 获取帮助

- 查看文档: [docs/README.md](./README.md)
- 提交Issue: [待添加]
- 技术讨论: [待添加]

---

**最后更新**: 2026-03-15
