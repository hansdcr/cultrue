# 测试文档

## 测试概述

本项目采用pytest作为测试框架，包含单元测试、集成测试和端到端测试。

## 测试结构

```
tests/
├── conftest.py              # pytest配置和共享fixtures
├── unit/                    # 单元测试
│   ├── domain/             # 领域层测试
│   ├── application/        # 应用层测试
│   └── infrastructure/     # 基础设施层测试
├── integration/            # 集成测试
│   ├── test_api.py        # User API功能测试
│   ├── test_agent_api.py  # Agent API功能测试
│   └── test_database_models.py  # 数据库模型测试
└── e2e/                    # 端到端测试
```

## 运行测试

### 运行所有测试

```bash
uv run pytest
```

### 运行特定测试文件

```bash
uv run pytest tests/integration/test_api.py
```

### 运行特定测试类

```bash
uv run pytest tests/integration/test_api.py::TestAuthAPI
```

### 运行特定测试用例

```bash
uv run pytest tests/integration/test_api.py::TestAuthAPI::test_register_user_success
```

### 显示详细输出

```bash
uv run pytest -v
```

### 显示测试覆盖率

```bash
uv run pytest --cov=src --cov-report=html
```

## API功能测试

### User API测试

详见 `tests/integration/test_api.py`

### Agent API测试

详见 [Agent API测试文档](./agent_api_testing.md)

测试文件：`tests/integration/test_agent_api.py`

快速运行：
```bash
# 运行所有Agent API测试
python -m pytest tests/integration/test_agent_api.py -v

# 运行特定测试类
python -m pytest tests/integration/test_agent_api.py::TestAgentRegistrationAPI -v
```

### User API测试详情

测试文件：`tests/integration/test_api.py`

### 测试覆盖

#### 认证API测试（TestAuthAPI）

1. **test_register_user_success** - 测试用户注册成功
   - 验证返回状态码201
   - 验证返回的用户信息正确
   - 验证包含用户ID

2. **test_register_user_duplicate_email** - 测试注册重复邮箱
   - 验证返回状态码400
   - 验证错误信息包含"already exists"

3. **test_register_user_duplicate_username** - 测试注册重复用户名
   - 验证返回状态码400
   - 验证错误信息包含"already exists"

4. **test_register_user_invalid_email** - 测试注册无效邮箱
   - 验证返回状态码422（Pydantic验证错误）

5. **test_login_success** - 测试登录成功
   - 验证返回状态码200
   - 验证返回access_token和refresh_token
   - 验证token_type为"bearer"

6. **test_login_invalid_email** - 测试登录无效邮箱
   - 验证返回状态码401
   - 验证错误信息为"Invalid email or password"

7. **test_login_invalid_password** - 测试登录错误密码
   - 验证返回状态码401
   - 验证错误信息为"Invalid email or password"

#### 用户API测试（TestUserAPI）

1. **test_get_current_user_success** - 测试获取当前用户信息成功
   - 验证返回状态码200
   - 验证返回的用户信息正确

2. **test_get_current_user_without_token** - 测试未认证获取用户信息
   - 验证返回状态码401
   - 验证错误信息为"Not authenticated"

3. **test_get_current_user_invalid_token** - 测试使用无效token
   - 验证返回状态码401
   - 验证错误信息为"Not authenticated"

4. **test_update_current_user_success** - 测试更新当前用户信息成功
   - 验证返回状态码200
   - 验证更新后的信息正确

5. **test_update_current_user_without_token** - 测试未认证更新用户信息
   - 验证返回状态码401
   - 验证错误信息为"Not authenticated"

6. **test_get_user_by_id_success** - 测试通过ID获取用户信息成功
   - 验证返回状态码200
   - 验证返回的用户信息正确

7. **test_get_user_by_id_not_found** - 测试获取不存在的用户
   - 验证返回状态码404
   - 验证错误信息包含"not found"

#### 完整流程测试（TestCompleteUserFlow）

1. **test_complete_user_flow** - 测试完整的用户流程
   - 注册用户
   - 登录获取token
   - 获取当前用户信息
   - 更新用户信息
   - 通过ID获取用户信息
   - 验证未认证请求被拦截

### 测试结果

#### User API测试
```
======================== 15 passed, 4 warnings in 1.97s ========================
```
所有15个测试用例全部通过 ✅

#### Agent API测试
```
======================== 10 passed, 16 warnings in 1.99s ========================
```
所有10个测试用例全部通过 ✅

## 测试最佳实践

### 1. 使用唯一的测试数据

为避免测试之间的数据冲突，使用UUID生成唯一的用户名和邮箱：

```python
def generate_unique_email():
    """生成唯一的邮箱地址。"""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"

def generate_unique_username():
    """生成唯一的用户名。"""
    return f"user_{uuid.uuid4().hex[:8]}"
```

### 2. 测试命名规范

- 测试类名：`Test<功能名>`，如`TestAuthAPI`
- 测试方法名：`test_<功能>_<场景>`，如`test_register_user_success`
- 使用中文文档字符串描述测试目的

### 3. 测试结构

每个测试应该遵循AAA模式：
- **Arrange**（准备）：设置测试数据和环境
- **Act**（执行）：执行被测试的操作
- **Assert**（断言）：验证结果是否符合预期

### 4. 使用TestClient

FastAPI提供的TestClient可以方便地测试API端点：

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
response = client.post("/api/auth/register", json={...})
```

### 5. 测试认证

对于需要认证的端点，先登录获取token，然后在请求头中携带：

```python
login_response = client.post("/api/auth/login", json={...})
access_token = login_response.json()["data"]["access_token"]

response = client.get(
    "/api/users/me",
    headers={"Authorization": f"Bearer {access_token}"}
)
```

## 持续集成

测试应该在每次提交前运行，确保代码质量。可以配置Git hooks或CI/CD流程自动运行测试。

### 运行测试的Git Hook

在`.git/hooks/pre-commit`中添加：

```bash
#!/bin/bash
uv run pytest
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

## 测试覆盖率目标

- 单元测试覆盖率：≥ 80%
- 集成测试覆盖率：≥ 70%
- 关键业务逻辑覆盖率：100%

## 下一步

- [ ] 添加更多单元测试
- [ ] 添加性能测试
- [ ] 添加安全测试
- [ ] 配置CI/CD自动运行测试
