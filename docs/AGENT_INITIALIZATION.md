# 默认Agent初始化完成

## ✅ 已创建的Agent

### 1. Hans - 文化历史专家
- **Agent ID**: `agent_hans`
- **名称**: Hans
- **描述**: 文化历史专家，擅长讲述历史故事和文化背景
- **API Key**: `ak_IX0KUjLXs7hskOCBYOVhZJ--s3hSe0F_`
- **API Key前缀**: `ak_IX0KUjLXs7hsk`
- **状态**: 激活

### 2. Alice - 艺术鉴赏家
- **Agent ID**: `agent_alice`
- **名称**: Alice
- **描述**: 艺术鉴赏家，热爱艺术和美学，对各种艺术形式有独到见解
- **API Key**: `ak_hh0q-__S8mhAJO7XOqxuJEdp6SJPvrBC`
- **API Key前缀**: `ak_hh0q-__S8mhAJ`
- **状态**: 激活

### 3. Bob - 旅行向导
- **Agent ID**: `agent_bob`
- **名称**: Bob
- **描述**: 旅行向导，熟悉世界各地的文化和风土人情
- **API Key**: `ak_xZM34TtEJ9uE3dpGUUKb4n7KhWE_i7iW`
- **API Key前缀**: `ak_xZM34TtEJ9uE3`
- **状态**: 激活

## 🔐 使用API Key进行认证

### 示例：使用curl测试Agent认证

```bash
# 获取Agent列表
curl -X GET http://localhost:8000/api/agents \
  -H "Authorization: ApiKey ak_IX0KUjLXs7hskOCBYOVhZJ--s3hSe0F_"

# 获取Agent详情
curl -X GET http://localhost:8000/api/agents/{agent_id} \
  -H "Authorization: ApiKey ak_IX0KUjLXs7hskOCBYOVhZJ--s3hSe0F_"
```

### 示例：使用Python测试Agent认证

```python
import requests

# Agent的API Key
api_key = "ak_IX0KUjLXs7hskOCBYOVhZJ--s3hSe0F_"

# 设置请求头
headers = {
    "Authorization": f"ApiKey {api_key}",
    "Content-Type": "application/json"
}

# 获取Agent列表
response = requests.get(
    "http://localhost:8000/api/agents",
    headers=headers
)

print(response.json())
```

## ⚠️ 重要提示

1. **API Key安全**：这些API Key仅在初始化时显示一次，请妥善保存
2. **生产环境**：在生产环境中，应该使用环境变量或密钥管理服务来存储API Key
3. **重新生成**：如果API Key泄露，可以使用`POST /api/agents/{agent_id}/regenerate-key`端点重新生成

## 📝 下一步

1. 在main.py中注册Agent和Contact路由
2. 使用UnifiedAuthMiddleware替换现有的AuthMiddleware
3. 启动应用并测试API
4. 运行单元测试

---

**创建日期**: 2026-03-16
**初始化脚本**: `scripts/init_agents.py`
