# 集成测试说明

本目录包含项目的集成测试，测试不同模块之间的交互和完整的用户场景。

## 测试分类

### 1. 单元测试（Unit Tests）
位置：`tests/unit/`
- 测试单个类或函数的行为
- 使用mock隔离依赖
- 运行快速，不需要外部资源

### 2. 集成测试（Integration Tests）
位置：`tests/integration/`
- 测试多个模块之间的交互
- 部分测试需要数据库连接
- 测试API端点和数据库操作

### 3. 功能测试（Functional Tests）
位置：`tests/integration/test_*_functional.py`
- 从用户使用角度测试完整流程
- 需要完整的应用环境
- 测试真实的用户场景

## 运行测试

### 运行所有单元测试
```bash
pytest tests/unit/ -v
```

### 运行所有集成测试（跳过需要完整环境的测试）
```bash
pytest tests/integration/ -v
```

### 运行特定测试文件
```bash
pytest tests/integration/test_api.py -v
```

## 功能测试说明

### WebSocket连接功能测试（迭代9）
文件：`test_websocket_connection_functional.py`

测试场景：
- ✅ 用户使用有效token连接WebSocket
- ✅ 用户无法在没有认证信息的情况下连接
- ✅ 用户无法使用无效token连接
- ✅ 用户可以发送心跳保持连接
- ✅ 用户发送未知消息类型时收到错误
- ✅ 用户可以发送消息送达确认
- ✅ 用户可以从多个设备同时连接

**运行要求：**
- 数据库已启动
- 应用完全初始化（包括WebSocket连接管理器）
- 使用真实的WebSocket客户端

**当前状态：** 已标记为skip，因为TestClient不触发lifespan事件

### 消息推送功能测试（迭代10）
文件：`test_message_push_functional.py`

测试场景：
- ✅ 用户通过REST API发送消息
- ✅ 用户无法向不存在的会话发送消息
- ✅ 未认证用户无法发送消息
- ✅ 消息实时推送给在线接收者
- ✅ 消息推送到接收者的所有设备
- ✅ 离线用户不会收到实时推送
- ✅ 用户收到其他用户上线通知
- ✅ 用户收到其他用户离线通知
- ✅ 用户可以确认收到的消息

**运行要求：**
- 数据库已启动并包含测试数据（用户、会话）
- 应用完全初始化（包括EventBus、MessagePushService）
- 使用真实的WebSocket和HTTP客户端

**当前状态：** 已标记为skip，因为需要完整的数据库环境和测试数据

## 如何运行功能测试

### 方法1：使用真实的应用服务器（推荐）

1. 启动数据库：
```bash
docker-compose up -d postgres
```

2. 准备测试数据：
```bash
# 运行数据库迁移
alembic upgrade head

# 创建测试用户和会话（需要编写数据准备脚本）
python scripts/prepare_test_data.py
```

3. 启动应用服务器：
```bash
uvicorn main:app --reload
```

4. 使用真实的WebSocket客户端运行测试：
```python
# 使用websockets库或其他WebSocket客户端
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws?token=<your_token>"
    async with websockets.connect(uri) as websocket:
        # 接收连接成功消息
        message = await websocket.recv()
        data = json.loads(message)
        print(f"Connected: {data}")

        # 发送心跳
        await websocket.send(json.dumps({"type": "ping"}))
        response = await websocket.recv()
        print(f"Pong: {response}")

asyncio.run(test_websocket())
```

### 方法2：修改测试以手动初始化依赖

1. 在测试中手动初始化ConnectionManager、EventBus等
2. 使用pytest fixtures提供这些依赖
3. Mock数据库操作或使用测试数据库

示例：
```python
@pytest.fixture
def setup_app():
    """手动初始化应用依赖。"""
    from src.application.realtime.services.connection_manager import ConnectionManager
    from src.application.shared.events.event_bus import EventBus
    from src.interfaces.websocket import endpoints as ws_endpoints

    connection_manager = ConnectionManager()
    event_bus = EventBus()

    ws_endpoints.set_connection_manager(connection_manager)
    # ... 设置其他依赖

    yield

    # 清理
```

## 测试覆盖率

查看测试覆盖率：
```bash
pytest --cov=src --cov-report=html
```

生成的报告位于：`htmlcov/index.html`

## 注意事项

1. **功能测试需要完整环境**：功能测试模拟真实用户场景，需要完整的应用环境和数据库。

2. **TestClient的限制**：FastAPI的TestClient不会触发lifespan事件，因此无法初始化全局依赖（如ConnectionManager）。

3. **数据隔离**：运行集成测试时，确保使用测试数据库，避免污染生产数据。

4. **异步测试**：WebSocket测试涉及异步操作，需要使用`pytest-asyncio`插件。

5. **测试顺序**：某些测试可能依赖特定的数据状态，注意测试之间的隔离。

## 持续集成

在CI/CD流程中：
- 单元测试：每次提交都运行
- 集成测试：每次提交都运行（使用测试数据库）
- 功能测试：定期运行或在发布前运行（需要完整环境）

## 贡献指南

添加新测试时：
1. 单元测试放在`tests/unit/`
2. 集成测试放在`tests/integration/`
3. 功能测试放在`tests/integration/`并以`_functional.py`结尾
4. 为需要完整环境的测试添加适当的skip标记
5. 在测试文档字符串中清楚说明测试场景
