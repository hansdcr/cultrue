# 迭代10: 功能测试分析报告

> 对 test_websocket_connection_functional.py 和 test_message_push_functional.py 的正确性与完整性分析

## 📋 分析信息

- **分析日期**: 2026-03-17
- **分析对象**: 迭代9（WebSocket连接）和迭代10（消息推送）功能测试
- **测试文件**:
  - `tests/integration/test_websocket_connection_functional.py`
  - `tests/integration/test_message_push_functional.py`
- **对照实现**:
  - `src/interfaces/websocket/endpoints.py`
  - `src/interfaces/websocket/auth.py`
  - `src/interfaces/api/rest/message.py`

---

## 一、test_websocket_connection_functional.py

### ✅ 正确性：基本正确

所有7个测试逻辑与实现一致：

| 测试 | 断言 | 与实现一致 |
|------|------|-----------|
| `test_user_can_connect_with_valid_token` | `connection_established` 含 `connection_id`, `actor_type`, `actor_id`, `connected_at` | ✅ |
| `test_user_cannot_connect_without_credentials` | 连接后 receive_json 抛异常 | ✅ auth.py 关闭连接 code=4000 |
| `test_user_cannot_connect_with_invalid_token` | 连接后 receive_json 抛异常 | ✅ auth.py 关闭连接 code=4001 |
| `test_user_can_send_heartbeat` | pong 含 `type: pong`, `timestamp` | ✅ |
| `test_user_receives_error_for_unknown_message_type` | error 含 `type: error`, `message` 含 "Unknown message type" | ✅ |
| `test_user_can_send_message_acknowledgement` | 发送 ack 不崩溃 | ✅ |
| `test_user_can_connect_from_multiple_devices` | 两个 connection_id 不同，actor_id 相同 | ✅ |

### ⚠️ 完整性：有缺口

**缺少的测试场景**：

1. **Agent 用 api_key 连接** — `auth.py` 支持 `api_key` 认证，但没有对应测试
2. **无效 api_key 连接被拒绝** — 只测试了无效 token，没测试无效 api_key
3. **typing 消息处理** — `endpoints.py` 有 `elif message_type == "typing"` 分支，无测试
4. **ack 后连接保持正常** — 当前只验证"不崩溃"，未验证发送 ack 后连接仍可继续通信（发 ping 收 pong）
5. **在线状态通知** — `endpoints.py` 连接/断开时会调用 `online_status_service.notify_status_change`，但 conftest 将其设为 None，该路径未被测试

---

## 二、test_message_push_functional.py

### ⚠️ 正确性：有3处问题

**问题1：`test_user_sends_message_via_api` 断言 `data["code"] == 200`**

```python
assert data["code"] == 200  # ❓ 需确认 ApiResponse 的字段结构
```

HTTP 状态码是 201，但响应体中 `code` 字段的值取决于 `ApiResponse.success()` 的实现，需要核实。

**问题2：`test_offline_user_does_not_receive_push` 逻辑不完整**

```python
# User2发送消息（通过REST API，未建立WebSocket）
# 注意：这里需要User2的token，但User2没有连接WebSocket
# 实际测试中需要创建User2的token

# User1应该收到推送
message = ws1.receive_json()  # ❌ 没有人发消息，这里会永久阻塞
```

User2 的 token 没有创建，也没有实际发送消息，`ws1.receive_json()` 会永久阻塞。即使去掉 skip 也无法运行。

**问题3：`TestOnlineStatusNotification` 依赖 None 服务**

```python
# conftest.py 中：
ws_endpoints.set_online_status_service(None)
ws_endpoints.set_conversation_repo(None)
```

在线状态通知测试依赖 `online_status_service` 和 `conversation_repo`，但 conftest 将它们设为 None。即使去掉 skip，`endpoints.py` 中的 `if online_status_service and conversation_repo:` 判断会跳过通知，测试断言会失败。

### ❌ 完整性：缺口较大

**REST API 端点覆盖情况**：

| 端点 | 功能 | 测试覆盖 |
|------|------|---------|
| `POST /api/conversations/{id}/messages` | 发送消息 | ⚠️ 有但全部 skip |
| `GET /api/conversations/{id}/messages` | 获取消息列表（支持 limit/offset 分页） | ❌ 完全没有 |
| `GET /api/messages/{id}` | 获取消息详情 | ❌ 完全没有 |
| `DELETE /api/messages/{id}` | 删除消息（仅发送者） | ❌ 完全没有 |

**WebSocket 推送场景覆盖情况**：

| 场景 | 测试 | 状态 |
|------|------|------|
| 消息实时推送给在线接收者 | `test_message_is_pushed_to_online_recipient` | skip（需要真实会话数据） |
| 消息推送到接收者所有设备 | `test_message_is_pushed_to_all_devices` | skip（需要真实会话数据） |
| 离线用户不收到推送 | `test_offline_user_does_not_receive_push` | skip + 逻辑缺陷 |
| 用户上线通知 | `test_user_receives_online_notification` | skip + 依赖 None 服务 |
| 用户离线通知 | `test_user_receives_offline_notification` | skip + 依赖 None 服务 |
| 消息送达确认 | `test_user_can_acknowledge_received_message` | skip（需要真实会话数据） |

**可以立即去掉 skip 的测试**：

`test_user_cannot_send_message_without_authentication` — 不需要数据库，只验证 401，可直接运行。

---

## 三、总结与建议

### 当前状态

| 文件 | 可运行测试数 | skip 数 | 正确性 | 完整性 |
|------|------------|---------|--------|--------|
| `test_websocket_connection_functional.py` | 7 | 0 | ✅ 正确 | ⚠️ 缺 Agent/typing/在线状态 |
| `test_message_push_functional.py` | 0 | 9 | ⚠️ 有逻辑缺陷 | ❌ GET/DELETE 端点无覆盖 |

### 待修复项

1. **修复 `test_offline_user_does_not_receive_push`** — 补充 User2 token 和发送消息逻辑
2. **补充 GET/DELETE 消息 API 测试** — 这些测试不需要 WebSocket，只需要数据库中有会话和消息
3. **补充 Agent api_key 连接测试** — 需要在数据库中创建 Agent 测试数据
4. **在线状态通知测试** — 需要在 conftest 中初始化真实的 `online_status_service` 和 `conversation_repo`
5. **核实 `ApiResponse.success()` 的 code 字段值** — 确认断言 `data["code"] == 200` 是否正确

---

**文档版本**: v1.0
**创建日期**: 2026-03-17
