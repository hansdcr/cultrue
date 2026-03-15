# Cultrue 项目文档中心

> 多方通信平台后端服务 - 支持User、Agent之间的实时通信

## 📚 文档导航

### 核心文档

1. **[项目概览](./project_overview.md)** - 项目背景、目标和架构概述
2. **[迭代计划](./iterations/README.md)** - 详细的迭代开发计划（推荐从这里开始）
3. **[编码规范](./coding_standards.md)** - 开发规范和最佳实践

### 设计文档

4. **[后端开发计划](./backend_development_plan.md)** - 完整的后端架构设计
5. **[消息系统设计](./messaging_system_design.md)** - 消息系统详细设计
6. **[数据库设计](./database_design.md)** - 数据库表结构和关系
7. **[API设计](./api_design.md)** - REST API和WebSocket API规范

### 开发指南

8. **[快速开始](./quick_start.md)** - 环境搭建和运行指南
9. **[开发流程](./development_workflow.md)** - 日常开发流程
10. **[测试指南](./testing_guide.md)** - 测试策略和用例

### 更新记录

11. **[设计更新总结](./design_update_summary.md)** - 设计变更历史

## 🚀 快速开始

### 新开发者入门路径

1. 阅读 [项目概览](./project_overview.md) 了解项目背景
2. 查看 [迭代计划](./iterations/README.md) 了解当前进度
3. 阅读 [编码规范](./coding_standards.md) 熟悉开发规范
4. 按照 [快速开始](./quick_start.md) 搭建开发环境
5. 选择一个迭代任务开始开发

### 当前开发状态

- **当前迭代**: 迭代1 - 基础架构搭建
- **完成进度**: 50%
- **下一个里程碑**: 完成数据库迁移配置

## 📋 项目结构

```
cultrue/
├── docs/                    # 文档目录
│   ├── README.md           # 本文件 - 文档入口
│   ├── iterations/         # 迭代计划目录
│   │   ├── README.md       # 迭代总览
│   │   ├── iteration-01.md # 迭代1详情
│   │   ├── iteration-02.md # 迭代2详情
│   │   └── ...
│   └── ...
├── src/                    # 源代码
│   ├── domain/            # 领域层
│   ├── application/       # 应用层
│   ├── infrastructure/    # 基础设施层
│   └── interfaces/        # 接口层
├── tests/                 # 测试代码
├── migrations/            # 数据库迁移
└── main.py               # 应用入口

```

## 🎯 开发原则

1. **迭代开发**: 每个迭代完成一个独立的功能模块
2. **单一职责**: 每次只做一件事，做好一件事
3. **测试驱动**: 每个功能都要有对应的测试
4. **文档同步**: 代码和文档同步更新

## 📞 联系方式

- 项目仓库: [待添加]
- 问题反馈: [待添加]
- 技术讨论: [待添加]

---

**最后更新**: 2026-03-15
**文档版本**: v1.0
