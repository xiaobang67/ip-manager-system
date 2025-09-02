"""
认证相关测试
"""
import pytest
from fastapi.testclient import TestClient
from app.core.security import verify_password, get_password_hash, create_access_token, verify_token


class TestSecurity:
    """安全工具测试"""
    
    def test_password_hashing(self):
        """测试密码加密和验证"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # 验证密码哈希不等于原密码
        assert hashed != password
        
        # 验证密码验证功能
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_token_creation_and_verification(self):
        """测试JWT令牌创建和验证"""
        data = {"sub": "123", "username": "testuser", "role": "user"}
        
        # 创建访问令牌
        access_token = create_access_token(data)
        assert access_token is not None
        
        # 验证访问令牌
        payload = verify_token(access_token, token_type="access")
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["username"] == "testuser"
        assert payload["role"] == "user"
        assert payload["type"] == "access"
    
    def test_invalid_token_verification(self):
        """测试无效令牌验证"""
        # 测试无效令牌
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)
        assert payload is None
        
        # 测试错误的令牌类型
        data = {"sub": "123", "username": "testuser"}
        access_token = create_access_token(data)
        payload = verify_token(access_token, token_type="refresh")
        assert payload is None


class TestAuthAPI:
    """认证API测试"""
    
    def test_login_success(self, client, test_user):
        """测试成功登录"""
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        
        user_data = data["user"]
        assert user_data["username"] == "testuser"
        assert user_data["email"] == "test@example.com"
        assert user_data["role"] == "user"
    
    def test_login_invalid_credentials(self, client, test_user):
        """测试无效凭据登录"""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """测试不存在的用户登录"""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]
    
    def test_logout(self, client, auth_headers):
        """测试登出"""
        response = client.post("/api/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "登出成功"
    
    def test_logout_without_token(self, client):
        """测试无令牌登出"""
        response = client.post("/api/auth/logout")
        
        # 登出应该总是成功，即使没有令牌
        assert response.status_code == 200
    
    def test_refresh_token(self, client, test_user):
        """测试刷新令牌"""
        # 先登录获取刷新令牌
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        login_response = client.post("/api/auth/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]
        
        # 使用刷新令牌获取新的访问令牌
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_token_invalid(self, client):
        """测试无效刷新令牌"""
        refresh_data = {"refresh_token": "invalid.refresh.token"}
        response = client.post("/api/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
        assert "无效的刷新令牌" in response.json()["detail"]
    
    def test_get_profile(self, client, auth_headers, test_user):
        """测试获取用户个人信息"""
        response = client.get("/api/auth/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["role"] == "user"
        assert data["theme"] == "light"
        assert data["is_active"] is True
    
    def test_get_profile_without_auth(self, client):
        """测试未认证获取个人信息"""
        response = client.get("/api/auth/profile")
        
        assert response.status_code == 401
    
    def test_update_profile(self, client, auth_headers):
        """测试更新个人信息"""
        update_data = {
            "email": "newemail@example.com",
            "theme": "dark"
        }
        
        response = client.put("/api/auth/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == "newemail@example.com"
        assert data["theme"] == "dark"
    
    def test_change_password_success(self, client, auth_headers):
        """测试成功修改密码"""
        password_data = {
            "old_password": "testpass123",
            "new_password": "NewPass123!"
        }
        
        response = client.put("/api/auth/password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "密码修改成功"
    
    def test_change_password_wrong_old_password(self, client, auth_headers):
        """测试旧密码错误"""
        password_data = {
            "old_password": "wrongpassword",
            "new_password": "NewPass123!"
        }
        
        response = client.put("/api/auth/password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "旧密码错误" in response.json()["detail"]
    
    def test_change_password_weak_password(self, client, auth_headers):
        """测试弱密码"""
        password_data = {
            "old_password": "testpass123",
            "new_password": "weak"
        }
        
        response = client.put("/api/auth/password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "密码长度至少8位" in response.json()["detail"]
    
    def test_verify_token(self, client, auth_headers):
        """测试验证令牌"""
        response = client.get("/api/auth/verify", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] is True
        assert "user" in data
        assert data["user"]["username"] == "testuser"
    
    def test_verify_invalid_token(self, client):
        """测试验证无效令牌"""
        invalid_headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/auth/verify", headers=invalid_headers)
        
        assert response.status_code == 401


class TestUserRepository:
    """用户数据访问层测试"""
    
    def test_create_user(self, db_session):
        """测试创建用户"""
        from app.repositories.user_repository import UserRepository
        
        repo = UserRepository(db_session)
        user = repo.create(
            username="newuser",
            password="password123",
            email="newuser@example.com"
        )
        
        assert user is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.role.value == "user"
        assert user.is_active is True
        assert verify_password("password123", user.password_hash)
    
    def test_create_duplicate_user(self, db_session, test_user):
        """测试创建重复用户"""
        from app.repositories.user_repository import UserRepository
        
        repo = UserRepository(db_session)
        user = repo.create(
            username="testuser",  # 已存在的用户名
            password="password123"
        )
        
        assert user is None
    
    def test_authenticate_user(self, db_session, test_user):
        """测试用户认证"""
        from app.repositories.user_repository import UserRepository
        
        repo = UserRepository(db_session)
        
        # 正确凭据
        user = repo.authenticate("testuser", "testpass123")
        assert user is not None
        assert user.username == "testuser"
        
        # 错误密码
        user = repo.authenticate("testuser", "wrongpassword")
        assert user is None
        
        # 不存在的用户
        user = repo.authenticate("nonexistent", "password")
        assert user is None
    
    def test_get_user_by_username(self, db_session, test_user):
        """测试根据用户名获取用户"""
        from app.repositories.user_repository import UserRepository
        
        repo = UserRepository(db_session)
        
        user = repo.get_by_username("testuser")
        assert user is not None
        assert user.username == "testuser"
        
        user = repo.get_by_username("nonexistent")
        assert user is None
    
    def test_update_user(self, db_session, test_user):
        """测试更新用户"""
        from app.repositories.user_repository import UserRepository
        
        repo = UserRepository(db_session)
        
        updated_user = repo.update(test_user.id, email="updated@example.com")
        assert updated_user is not None
        assert updated_user.email == "updated@example.com"
    
    def test_update_password(self, db_session, test_user):
        """测试更新密码"""
        from app.repositories.user_repository import UserRepository
        
        repo = UserRepository(db_session)
        
        success = repo.update_password(test_user.id, "newpassword123")
        assert success is True
        
        # 验证新密码
        user = repo.authenticate("testuser", "newpassword123")
        assert user is not None


class TestAuthService:
    """认证服务测试"""
    
    def test_login_service(self, db_session, test_user):
        """测试登录服务"""
        from app.services.auth_service import AuthService
        
        service = AuthService(db_session)
        
        access_token, refresh_token, user_info = service.login("testuser", "testpass123")
        
        assert access_token is not None
        assert refresh_token is not None
        assert user_info["username"] == "testuser"
        assert user_info["role"] == "user"
    
    def test_login_service_invalid_credentials(self, db_session, test_user):
        """测试登录服务无效凭据"""
        from app.services.auth_service import AuthService
        from fastapi import HTTPException
        
        service = AuthService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.login("testuser", "wrongpassword")
        
        assert exc_info.value.status_code == 401
    
    def test_get_current_user_service(self, db_session, test_user):
        """测试获取当前用户服务"""
        from app.services.auth_service import AuthService
        
        service = AuthService(db_session)
        
        # 先登录获取令牌
        access_token, _, _ = service.login("testuser", "testpass123")
        
        # 使用令牌获取用户
        user = service.get_current_user(access_token)
        assert user is not None
        assert user.username == "testuser"
    
    def test_refresh_access_token_service(self, db_session, test_user):
        """测试刷新访问令牌服务"""
        from app.services.auth_service import AuthService
        
        service = AuthService(db_session)
        
        # 先登录获取刷新令牌
        _, refresh_token, _ = service.login("testuser", "testpass123")
        
        # 刷新访问令牌
        new_access_token = service.refresh_access_token(refresh_token)
        assert new_access_token is not None
        
        # 验证新令牌可以获取用户信息
        user = service.get_current_user(new_access_token)
        assert user is not None
        assert user.username == "testuser"