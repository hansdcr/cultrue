# Cultrue

> 多方通信平台后端服务 - 支持User、Agent之间的实时通信

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 快速开始

```bash
# 安装依赖
uv pip install -e .

# 配置环境变量
cp .env.example .env

# 启动服务
python main.py
```

访问 http://localhost:8000/docs 查看API文档

## 📚 文档

完整文档请访问：**[docs/README.md](./docs/README.md)** ⭐

### 快速导航

- 🎯 [项目概览](./docs/project_overview.md) - 了解项目背景和架构
- 🚀 [快速开始](./docs/quick_start.md) - 5分钟搭建开发环境
- 🔄 [迭代计划](./docs/iterations/README.md) - 查看开发进度
- 📏 [编码规范](./docs/coding_standards.md) - 开发规范和最佳实践

## ✨ 核心特性

- ✅ **多方通信**: 支持User-User、User-Agent、Agent-Agent通信
- ✅ **实时推送**: WebSocket实时消息推送
- ✅ **Agent主动**: Agent可以主动发起消息
- ✅ **DDD架构**: 清晰的领域驱动设计
- ✅ **类型安全**: 完整的类型注解
- ✅ **异步高性能**: 基于asyncio和asyncpg

## 🏗️ 技术栈

- **Web框架**: FastAPI 0.115+
- **数据库**: PostgreSQL 15+ (asyncpg)
- **ORM**: SQLAlchemy 2.0 + Alembic
- **认证**: JWT + bcrypt
- **实时通信**: WebSocket
- **消息队列**: Redis + Celery
- **Python**: 3.12

## 📊 项目状态

- **当前版本**: v0.1.0
- **开发状态**: 开发中
- **当前迭代**: 迭代1 - 基础架构搭建 (85%完成)
- **总体进度**: 5%

## 🎯 开发路线

### 里程碑1: 用户认证系统 (迭代1-5)
- ✅ 基础架构搭建
- ⬜ 数据库配置
- ⬜ 用户注册登录
- ⬜ 用户信息管理

### 里程碑2: Agent和消息系统 (迭代6-8)
- ⬜ Agent管理
- ⬜ 消息数据模型
- ⬜ 消息基础API

### 里程碑3: 实时通信 (迭代9-11)
- ⬜ WebSocket连接
- ⬜ 实时消息推送
- ⬜ Agent主动消息

### 里程碑4: 完整功能 (迭代12-15)
- ⬜ 地图功能
- ⬜ 设置管理
- ⬜ Agent集成
- ⬜ 优化完善

## 🤝 贡献

欢迎贡献！请查看 [编码规范](./docs/coding_standards.md) 了解开发规范。

## 📄 许可证

[MIT License](LICENSE)

## 📞 联系方式

- 项目文档: [docs/README.md](./docs/README.md)
- 问题反馈: [待添加]
- 技术讨论: [待添加]

---

**最后更新**: 2026-03-15
