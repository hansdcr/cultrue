"""API接口功能测试。

测试用户注册、登录、获取用户信息等API接口。
使用真实数据库进行测试，测试前后清理数据。
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    """创建测试客户端。"""
    with TestClient(app) as test_client:
        yield test_client


def generate_unique_email():
    """生成唯一的邮箱地址。"""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def generate_unique_username():
    """生成唯一的用户名。"""
    return f"user_{uuid.uuid4().hex[:8]}"


class TestAuthAPI:
    """认证API测试类。"""

    def test_register_user_success(self, client):
        """测试用户注册成功。"""
        username = generate_unique_username()
        email = generate_unique_email()

        response = client.post(
            "/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": "Test123456",
                "full_name": "Test User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 200  # ApiResponse默认code为200
        assert data["data"]["username"] == username
        assert data["data"]["email"] == email
        assert data["data"]["full_name"] == "Test User"
        assert "id" in data["data"]
        assert data["message"] == "User registered successfully"

    def test_register_user_duplicate_email(self, client):
        """测试注册重复邮箱。"""
        # 第一次注册
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser002",
                "email": "test002@example.com",
                "password": "Test123456",
                "full_name": "Test User 002",
            },
        )

        # 第二次注册相同邮箱
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser003",
                "email": "test002@example.com",
                "password": "Test123456",
                "full_name": "Test User 003",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()

    def test_register_user_duplicate_username(self, client):
        """测试注册重复用户名。"""
        # 第一次注册
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser004",
                "email": "test004@example.com",
                "password": "Test123456",
                "full_name": "Test User 004",
            },
        )

        # 第二次注册相同用户名
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser004",
                "email": "test005@example.com",
                "password": "Test123456",
                "full_name": "Test User 005",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()

    def test_register_user_invalid_email(self, client):
        """测试注册无效邮箱。"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser006",
                "email": "invalid-email",
                "password": "Test123456",
                "full_name": "Test User 006",
            },
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_login_success(self, client):
        """测试登录成功。"""
        # 先注册用户
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser007",
                "email": "test007@example.com",
                "password": "Test123456",
                "full_name": "Test User 007",
            },
        )

        # 登录
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test007@example.com",
                "password": "Test123456",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert data["data"]["user"]["email"] == "test007@example.com"
        assert data["message"] == "Login successful"

    def test_login_invalid_email(self, client):
        """测试登录无效邮箱。"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent999@example.com",
                "password": "Test123456",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid email or password"

    def test_login_invalid_password(self, client):
        """测试登录错误密码。"""
        # 先注册用户
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser008",
                "email": "test008@example.com",
                "password": "Test123456",
                "full_name": "Test User 008",
            },
        )

        # 使用错误密码登录
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test008@example.com",
                "password": "WrongPassword",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid email or password"


class TestUserAPI:
    """用户API测试类。"""

    def test_get_current_user_success(self, client):
        """测试获取当前用户信息成功。"""
        # 注册并登录
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser009",
                "email": "test009@example.com",
                "password": "Test123456",
                "full_name": "Test User 009",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "test009@example.com",
                "password": "Test123456",
            },
        )
        access_token = login_response.json()["data"]["access_token"]

        # 获取当前用户信息
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["username"] == "testuser009"
        assert data["data"]["email"] == "test009@example.com"
        assert data["data"]["full_name"] == "Test User 009"

    def test_get_current_user_without_token(self, client):
        """测试未认证获取当前用户信息。"""
        response = client.get("/api/users/me")

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    def test_get_current_user_invalid_token(self, client):
        """测试使用无效token获取当前用户信息。"""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    def test_update_current_user_success(self, client):
        """测试更新当前用户信息成功。"""
        # 注册并登录
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser010",
                "email": "test010@example.com",
                "password": "Test123456",
                "full_name": "Test User 010",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "test010@example.com",
                "password": "Test123456",
            },
        )
        access_token = login_response.json()["data"]["access_token"]

        # 更新用户信息
        response = client.put(
            "/api/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "full_name": "Updated User 010",
                "bio": "This is my bio",
                "avatar_url": "https://example.com/avatar.jpg",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["full_name"] == "Updated User 010"
        assert data["data"]["bio"] == "This is my bio"
        assert data["data"]["avatar_url"] == "https://example.com/avatar.jpg"

    def test_update_current_user_without_token(self, client):
        """测试未认证更新用户信息。"""
        response = client.put(
            "/api/users/me",
            json={
                "full_name": "Updated User",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    def test_get_user_by_id_success(self, client):
        """测试通过ID获取用户信息成功。"""
        # 注册并登录
        username = generate_unique_username()
        email = generate_unique_email()

        register_response = client.post(
            "/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": "Test123456",
                "full_name": "Test User",
            },
        )
        user_id = register_response.json()["data"]["id"]

        login_response = client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": "Test123456",
            },
        )
        access_token = login_response.json()["data"]["access_token"]

        # 通过ID获取用户信息
        response = client.get(
            f"/api/users/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == user_id
        assert data["data"]["username"] == username

    def test_get_user_by_id_not_found(self, client):
        """测试获取不存在的用户。"""
        # 注册并登录
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser012",
                "email": "test012@example.com",
                "password": "Test123456",
                "full_name": "Test User 012",
            },
        )

        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "test012@example.com",
                "password": "Test123456",
            },
        )
        access_token = login_response.json()["data"]["access_token"]

        # 获取不存在的用户
        response = client.get(
            "/api/users/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestCompleteUserFlow:
    """完整用户流程测试类。"""

    def test_complete_user_flow(self, client):
        """测试完整的用户流程：注册 -> 登录 -> 获取信息 -> 更新信息。"""
        # 1. 注册用户
        username = generate_unique_username()
        email = generate_unique_email()

        register_response = client.post(
            "/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": "Flow123456",
                "full_name": "Flow User",
            },
        )
        assert register_response.status_code == 201
        user_id = register_response.json()["data"]["id"]

        # 2. 登录
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": "Flow123456",
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]
        refresh_token = login_response.json()["data"]["refresh_token"]
        assert access_token is not None
        assert refresh_token is not None

        # 3. 获取当前用户信息
        me_response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["data"]["username"] == username

        # 4. 更新用户信息
        update_response = client.put(
            "/api/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "full_name": "Flow User Updated",
                "bio": "I am a flow test user",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["full_name"] == "Flow User Updated"
        assert update_response.json()["data"]["bio"] == "I am a flow test user"

        # 5. 通过ID获取用户信息
        user_response = client.get(
            f"/api/users/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert user_response.status_code == 200
        assert user_response.json()["data"]["full_name"] == "Flow User Updated"

        # 6. 验证未认证请求被拦截
        unauth_response = client.get("/api/users/me")
        assert unauth_response.status_code == 401
