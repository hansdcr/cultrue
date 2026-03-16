"""测试认证流程的脚本。"""

import sys

sys.path.insert(0, "/Users/gelin/Desktop/store/dev/python/ai/cultrue")

from src.infrastructure.security.jwt_service import jwt_service

# 测试token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZjJjOTY3Yi0wMWUyLTQ3MDktYmVjYS00NjU2MmM4ODM4ZWUiLCJleHAiOjE3NzM2MzYzMzIsImlhdCI6MTc3MzYzNTQzMiwidHlwZSI6ImFjY2VzcyJ9.6i-J1hdkEsOYCYwDiDKMYYyjVw92unbkW8tbSVzQg1E"

try:
    # 验证token
    jwt_service.verify_token(token, token_type="access")
    print("Token验证成功")

    # 获取用户ID
    user_id = jwt_service.get_user_id_from_token(token)
    print(f"用户ID: {user_id}")

except Exception as e:
    print(f"错误: {e}")
    import traceback

    traceback.print_exc()
