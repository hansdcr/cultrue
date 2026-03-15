# 编码规范

## 开发原则

### 1. 迭代原则
- **单一功能**：每个迭代完成的功能尽量单一和简单
- **渐进式开发**：从简单到复杂，逐步迭代
- **可验证**：每个迭代都能独立测试和验证

### 2. 文件管理
- **单文件原则**：每次只创建一个文件
- **逐步构建**：不要一次性创建大量文件
- **先核心后外围**：优先创建核心模块

### 3. 代码更新
- **限制更新范围**：每个文件每次更新不超过两个方法
- **小步提交**：不能一次更新很多个文件或方法
- **逐步完善**：如果确实需要大量更新，也要一步一步来

### 4. 方法设计
- **代码行数限制**：
  - 理想：每个方法不超过50行
  - 最大：不超过100行
- **职责单一**：一个方法只做一件事
- **适当抽象**：如果方法过长，抽象出新的方法

### 5. 编码规范
- **遵循Google Python编码规范**
- **类型注解**：使用类型提示（Type Hints）
  - **必须**：所有方法的参数都必须有类型注解
  - **必须**：所有方法都必须有返回值类型注解
  - **必须**：包括classmethod、staticmethod和普通方法
  - **例外**：`self`和`cls`参数不需要类型注解
- **文档字符串**：每个模块、类、方法都要有docstring
- **命名规范**：
  - 模块名：小写+下划线（`my_module.py`）
  - 类名：大驼峰（`MyClass`）
  - 函数/方法名：小写+下划线（`my_function`）
  - 常量：大写+下划线（`MY_CONSTANT`）

## 类型注解规范

### 1. 基本要求

**所有方法必须包含完整的类型注解**：
- 所有参数（除了`self`和`cls`）必须有类型注解
- 所有方法必须有返回值类型注解
- 使用`typing`模块提供的类型

### 2. 常用类型注解

```python
from typing import Dict, List, Optional, Tuple, Union, AsyncIterator

# 基本类型
def get_name(user_id: int) -> str:
    pass

# 可选类型
def find_user(user_id: int) -> Optional[User]:
    pass

# 列表和字典
def get_users() -> List[User]:
    pass

def get_config() -> Dict[str, str]:
    pass

# 元组
def get_session(session_id: str) -> Tuple[str, Conversation]:
    pass

# 联合类型
def process(value: str | int) -> bool:
    pass

# 异步迭代器
async def stream_data() -> AsyncIterator[str]:
    pass
```

### 3. 泛型类型

```python
from typing import Generic, TypeVar

T = TypeVar("T")

class ApiResponse(Generic[T]):
    @classmethod
    def success(cls, data: T) -> "ApiResponse[T]":
        pass
```

### 4. 特殊情况

```python
# 无返回值
def log_message(message: str) -> None:
    print(message)

# 异步函数
async def fetch_data(url: str) -> Dict[str, str]:
    pass

# 生成器
from typing import Iterator

def generate_numbers() -> Iterator[int]:
    for i in range(10):
        yield i

# 异步生成器
from typing import AsyncIterator

async def async_generate() -> AsyncIterator[str]:
    for item in items:
        yield item
```

### 5. 类型注解检查

使用以下工具检查类型注解：

```bash
# 使用mypy检查类型
mypy src/ --ignore-missing-imports

# 自定义检查脚本
python check_types.py src/**/*.py
```

## Google Python编码规范要点

### 1. 导入规范
```python
# 标准库
import os
import sys

# 第三方库
from fastapi import FastAPI
from pydantic import BaseModel

# 本地模块
from src.core.llm import LLMClient
```

### 2. 文档字符串（必须包含类型注解）
```python
def my_function(param1: str, param2: int) -> bool:
    """简短的一行描述。

    更详细的描述（如果需要）。

    Args:
        param1: 参数1的描述
        param2: 参数2的描述

    Returns:
        返回值的描述

    Raises:
        ValueError: 什么情况下抛出此异常
    """
    pass

# 异步函数示例
async def async_function(user_id: int) -> Optional[User]:
    """异步获取用户信息.

    Args:
        user_id: 用户ID

    Returns:
        用户对象，如果不存在则返回None
    """
    pass

# 泛型方法示例
@classmethod
def create_response(cls, data: T) -> "ApiResponse[T]":
    """创建API响应.

    Args:
        data: 响应数据

    Returns:
        API响应对象
    """
    pass
```

### 3. 类型注解（必须）
```python
from typing import List, Dict, Optional, AsyncIterator

# 所有参数和返回值都必须有类型注解
def process_messages(
    messages: List[Dict[str, str]],
    max_tokens: Optional[int] = None
) -> str:
    """处理消息列表。"""
    pass

# 异步函数也必须有类型注解
async def fetch_data(url: str) -> Dict[str, str]:
    """异步获取数据。"""
    pass

# 生成器必须有类型注解
async def stream_response(data: str) -> AsyncIterator[str]:
    """流式返回响应。"""
    for chunk in data.split():
        yield chunk
```

### 4. 异常处理
```python
# 具体的异常类型
try:
    result = await client.chat(messages)
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### 5. 代码格式化
- 使用`black`进行代码格式化
- 使用`ruff`进行代码检查
- 行长度：88字符（black默认）

## 开发流程

### 每次开发的步骤
1. **明确目标**：确定本次要实现的功能
2. **创建/更新文件**：一次只操作一个文件
3. **编写代码**：遵循上述规范
4. **代码检查**：运行ruff检查
5. **格式化**：运行black格式化
6. **测试**：编写并运行测试
7. **提交**：提交代码（如果需要）

### 示例工作流
```bash
# 1. 创建新文件
# 编写代码...

# 2. 格式化代码
black src/core/llm.py

# 3. 代码检查
ruff check src/core/llm.py

# 4. 运行测试
pytest tests/test_llm.py

# 5. 提交（如果用户要求）
git add src/core/llm.py
git commit -m "feat: add LLM client base class"
```

## 代码审查清单

在完成每个文件/方法后，检查：

- [ ] 是否符合单一职责原则
- [ ] 方法是否超过100行
- [ ] **所有参数是否都有类型注解（除了self和cls）**
- [ ] **方法是否有返回值类型注解**
- [ ] 是否有docstring
- [ ] 命名是否清晰
- [ ] 是否有适当的错误处理
- [ ] 是否有必要的日志
- [ ] 是否可以进一步抽象

### 类型注解检查工具

```bash
# 使用mypy检查类型
.venv/bin/mypy src/ main.py --ignore-missing-imports

# 使用自定义脚本检查
.venv/bin/python check_types.py src/**/*.py main.py
```

## 注意事项

1. **不要过度设计**：只实现当前需要的功能
2. **不要过早优化**：先保证功能正确，再考虑性能
3. **保持简单**：简单的代码比聪明的代码更好
4. **及时重构**：发现代码变复杂时，及时重构

---

**文档版本**：v1.0
**创建日期**：2026-03-15
**更新日期**：2026-03-15
**更新内容**：添加类型注解强制要求和详细规范
