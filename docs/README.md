# Cultrue 项目文档

> 多工程协作的文化交流平台后端服务

## 📚 文档导航

### 🚀 快速开始

- **[快速开始指南](quick_start.md)** - 项目启动和开发环境配置
- **[项目概览](project_overview.md)** - 项目背景、目标和技术栈
- **[编码规范](coding_standards.md)** - DDD架构和代码规范
- **[测试指南](testing.md)** - 测试策略和规范

### 🏗️ 架构设计

#### 核心架构文档

1. **[架构总结](ARCHITECTURE_SUMMARY.md)** ⭐ 必读
   - 设计演进历程
   - 最终架构方案（双层抽象 + Agent独立认证）
   - 文档索引和实施建议

2. **[快速参考指南](QUICK_REFERENCE.md)** ⭐ 实施必备
   - 核心概念（Actor vs Participant）
   - 完整文件结构
   - 关键代码模板
   - 数据库表结构
   - 测试示例
   - 实施检查清单

3. **[实施就绪总结](IMPLEMENTATION_READY.md)**
   - 完成的工作总结
   - 验收标准
   - 实施路径

#### 设计决策文档

4. **[方案对比](design_comparison.md)**
   - 方案A（User+Agent混合）vs 方案B（Agent独立认证）
   - 详细对比分析
   - 推荐方案

5. **[架构决策](architecture_decision.md)**
   - Participant中间表方案
   - 双层抽象设计
   - 数据完整性保证

6. **[Agent认证机制](agent_authentication.md)**
   - Agent独立认证设计
   - ApiKey值对象
   - 认证中间件
   - API设计

### 📋 迭代计划

#### 迭代文档索引

- **[迭代总览](iterations/README.md)** - 所有迭代的进度和状态

#### 已完成迭代

- **[迭代1: 项目初始化](iterations/iteration-01.md)** ✅
- **[迭代2: 数据库设计](iterations/iteration-02.md)** ✅
- **[迭代3: 基础架构](iterations/iteration-03.md)** ✅
- **[迭代4: 用户领域](iterations/iteration-04.md)** ✅
- **[迭代5: 用户认证](iterations/iteration-05.md)** ✅

#### 待实施迭代

- **[迭代6: Agent管理](iterations/iteration-06.md)** 🟡
  - Agent实体和认证
  - Contact系统
  - Participant中间表

- **[迭代7: 消息系统-数据模型](iterations/iteration-07.md)** 🟡
  - Conversation和Message实体
  - 使用Participant外键

- **[迭代8: 消息系统-API](iterations/iteration-08.md)** 🟡
  - 会话和消息API
  - 统一Actor抽象

#### 迭代实施指南

- **[迭代更新指南](iterations/iteration-update-guide.md)**
  - 迭代6、7、8更新说明
  - 仓储层实现模式
  - 测试更新指南

- **[关键修改详解](iterations/iteration-participant-changes.md)**
  - Participant实体和仓储
  - 数据库表结构
  - 完整代码示例

#### 参考版本（已归档）

- **[迭代6-纯Actor版本](iterations/iteration-06-actor-only.md)** - 仅供参考

## 📖 文档使用指南

### 新成员入门

1. 阅读 [项目概览](project_overview.md) 了解项目背景
2. 阅读 [快速开始指南](quick_start.md) 配置开发环境
3. 阅读 [编码规范](coding_standards.md) 了解代码规范
4. 阅读 [架构总结](ARCHITECTURE_SUMMARY.md) 了解整体架构

### 开始实施迭代6、7、8

1. **必读**：[架构总结](ARCHITECTURE_SUMMARY.md) - 了解设计方案
2. **必读**：[快速参考指南](QUICK_REFERENCE.md) - 获取代码模板
3. **参考**：[关键修改详解](iterations/iteration-participant-changes.md) - 详细实现
4. **参考**：[Agent认证机制](agent_authentication.md) - Agent认证细节
5. **实施**：按照 [迭代6](iterations/iteration-06.md) → [迭代7](iterations/iteration-07.md) → [迭代8](iterations/iteration-08.md) 顺序

### 遇到问题时

- **设计疑问** → [架构决策](architecture_decision.md)
- **方案选择** → [方案对比](design_comparison.md)
- **实施细节** → [关键修改详解](iterations/iteration-participant-changes.md)
- **代码模板** → [快速参考指南](QUICK_REFERENCE.md)
- **Agent认证** → [Agent认证机制](agent_authentication.md)

## 🎯 核心设计理念

### 双层抽象架构

```
领域层：Actor值对象（轻量级抽象）
    ↕ 仓储层自动转换
数据库层：Participant实体（外键保证）
```

### Agent作为一等公民

- ✅ Agent使用API Key独立认证
- ✅ Agent可以管理contacts、创建会话、发送消息
- ✅ Agent与User在API层面完全平等
- ✅ 支持User-User、User-Agent、Agent-Agent所有类型通信

### 数据完整性保证

- ✅ Participant中间表 + 外键约束
- ✅ 数据库层面保证一致性
- ✅ 应用层无需手动验证
- ✅ 自动级联删除

## 📊 项目进度

- **已完成**：迭代1-5（基础架构、用户管理、认证系统）
- **进行中**：迭代6-8设计完成，待实施
- **预计时间**：5-7天完成迭代6-8

## 📁 项目结构

```
cultrue/
├── docs/                           # 文档目录
│   ├── README.md                   # 本文件 - 文档入口
│   ├── ARCHITECTURE_SUMMARY.md     # 架构总结 ⭐
│   ├── QUICK_REFERENCE.md          # 快速参考 ⭐
│   ├── IMPLEMENTATION_READY.md     # 实施就绪
│   ├── design_comparison.md        # 方案对比
│   ├── architecture_decision.md    # 架构决策
│   ├── agent_authentication.md     # Agent认证
│   ├── project_overview.md         # 项目概览
│   ├── quick_start.md              # 快速开始
│   ├── coding_standards.md         # 编码规范
│   ├── testing.md                  # 测试指南
│   └── iterations/                 # 迭代计划
│       ├── README.md               # 迭代总览
│       ├── iteration-01.md         # 迭代1-5（已完成）
│       ├── iteration-06.md         # Agent管理
│       ├── iteration-07.md         # 消息数据模型
│       ├── iteration-08.md         # 消息API
│       ├── iteration-update-guide.md        # 更新指南
│       └── iteration-participant-changes.md # 关键修改
├── src/                            # 源代码
│   ├── domain/                     # 领域层
│   ├── application/                # 应用层
│   ├── infrastructure/             # 基础设施层
│   └── interfaces/                 # 接口层
├── tests/                          # 测试代码
├── migrations/                     # 数据库迁移
└── main.py                         # 应用入口
```

## 🎯 开发原则

1. **迭代开发**：每个迭代完成一个独立的功能模块
2. **DDD架构**：严格遵循领域驱动设计
3. **测试驱动**：每个功能都要有对应的测试
4. **文档同步**：代码和文档同步更新

---

**文档版本**：v3.0
**最后更新**：2026-03-16
**维护者**：开发团队
