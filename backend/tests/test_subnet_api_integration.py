import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from app.core.database import get_db, Base
from app.models.user import User
from app.models.subnet import Subnet
from app.models.ip_address import IPAddress
from app.core.security import get_password_hash, create_access_token
import json


# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_subnet.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    """创建测试客户端"""
    Base.metadata.create_all(bind=engine)
    # 创建一个没有lifespan的测试应用
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from app.api.v1.api import api_router
    
    test_app = FastAPI(title="Test IPAM API")
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    test_app.include_router(api_router, prefix="/api/v1")
    test_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(test_app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def test_user():
    """创建测试用户"""
    db = TestingSessionLocal()
    try:
        user = User(
            username="testuser",
            password_hash=get_password_hash("testpass"),
            email="test@example.com",
            role="admin"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture(scope="module")
def auth_headers(test_user):
    """创建认证头"""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestSubnetAPIIntegration:
    """网段API集成测试"""

    def test_create_subnet_success(self, client, auth_headers):
        """测试成功创建网段"""
        subnet_data = {
            "network": "192.168.1.0/24",
            "netmask": "255.255.255.0",
            "gateway": "192.168.1.1",
            "description": "测试网段",
            "vlan_id": 100,
            "location": "测试位置"
        }

        response = client.post(
            "/api/v1/subnets/",
            json=subnet_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["network"] == "192.168.1.0/24"
        assert data["netmask"] == "255.255.255.0"
        assert data["gateway"] == "192.168.1.1"
        assert data["description"] == "测试网段"
        assert data["vlan_id"] == 100
        assert data["location"] == "测试位置"
        assert "id" in data
        assert "created_at" in data

    def test_create_subnet_invalid_network(self, client, auth_headers):
        """测试创建无效网段格式"""
        subnet_data = {
            "network": "invalid-network",
            "netmask": "255.255.255.0"
        }

        response = client.post(
            "/api/v1/subnets/",
            json=subnet_data,
            headers=auth_headers
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_subnet_overlap(self, client, auth_headers):
        """测试创建重叠网段"""
        # 首先创建一个网段
        subnet_data1 = {
            "network": "192.168.2.0/24",
            "netmask": "255.255.255.0"
        }
        client.post("/api/v1/subnets/", json=subnet_data1, headers=auth_headers)

        # 尝试创建重叠的网段
        subnet_data2 = {
            "network": "192.168.2.0/25",  # 与上面的网段重叠
            "netmask": "255.255.255.128"
        }

        response = client.post(
            "/api/v1/subnets/",
            json=subnet_data2,
            headers=auth_headers
        )

        assert response.status_code == 409
        data = response.json()
        assert "重叠" in data["detail"]

    def test_get_subnets_list(self, client, auth_headers):
        """测试获取网段列表"""
        response = client.get("/api/v1/subnets/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "subnets" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert isinstance(data["subnets"], list)

    def test_get_subnet_by_id(self, client, auth_headers):
        """测试根据ID获取网段"""
        # 首先创建一个网段
        subnet_data = {
            "network": "192.168.3.0/24",
            "netmask": "255.255.255.0",
            "description": "测试获取网段"
        }
        create_response = client.post(
            "/api/v1/subnets/",
            json=subnet_data,
            headers=auth_headers
        )
        subnet_id = create_response.json()["id"]

        # 获取网段详情
        response = client.get(f"/api/v1/subnets/{subnet_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == subnet_id
        assert data["network"] == "192.168.3.0/24"
        assert data["description"] == "测试获取网段"

    def test_get_subnet_not_found(self, client, auth_headers):
        """测试获取不存在的网段"""
        response = client.get("/api/v1/subnets/99999", headers=auth_headers)

        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]

    def test_update_subnet(self, client, auth_headers):
        """测试更新网段"""
        # 首先创建一个网段
        subnet_data = {
            "network": "192.168.4.0/24",
            "netmask": "255.255.255.0",
            "description": "原始描述"
        }
        create_response = client.post(
            "/api/v1/subnets/",
            json=subnet_data,
            headers=auth_headers
        )
        subnet_id = create_response.json()["id"]

        # 更新网段
        update_data = {
            "description": "更新后的描述",
            "location": "新位置"
        }
        response = client.put(
            f"/api/v1/subnets/{subnet_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "更新后的描述"
        assert data["location"] == "新位置"

    def test_update_subnet_not_found(self, client, auth_headers):
        """测试更新不存在的网段"""
        update_data = {"description": "更新描述"}
        response = client.put(
            "/api/v1/subnets/99999",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_delete_subnet_success(self, client, auth_headers):
        """测试成功删除网段"""
        # 首先创建一个网段
        subnet_data = {
            "network": "192.168.5.0/24",
            "netmask": "255.255.255.0",
            "description": "待删除的网段"
        }
        create_response = client.post(
            "/api/v1/subnets/",
            json=subnet_data,
            headers=auth_headers
        )
        subnet_id = create_response.json()["id"]

        # 删除网段
        response = client.delete(f"/api/v1/subnets/{subnet_id}", headers=auth_headers)

        assert response.status_code == 204

        # 验证网段已被删除
        get_response = client.get(f"/api/v1/subnets/{subnet_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_subnet_not_found(self, client, auth_headers):
        """测试删除不存在的网段"""
        response = client.delete("/api/v1/subnets/99999", headers=auth_headers)

        assert response.status_code == 404

    def test_validate_subnet_valid(self, client, auth_headers):
        """测试验证有效网段"""
        validation_data = {
            "network": "192.168.100.0/24"
        }

        response = client.post(
            "/api/v1/subnets/validate",
            json=validation_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert "验证通过" in data["message"]

    def test_validate_subnet_invalid(self, client, auth_headers):
        """测试验证无效网段"""
        validation_data = {
            "network": "invalid-network"
        }

        response = client.post(
            "/api/v1/subnets/validate",
            json=validation_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert "无效" in data["message"]

    def test_search_subnets(self, client, auth_headers):
        """测试搜索网段"""
        # 首先创建一些测试网段
        test_subnets = [
            {
                "network": "192.168.10.0/24",
                "netmask": "255.255.255.0",
                "description": "办公网段"
            },
            {
                "network": "192.168.11.0/24",
                "netmask": "255.255.255.0",
                "description": "服务器网段"
            }
        ]

        for subnet_data in test_subnets:
            client.post("/api/v1/subnets/", json=subnet_data, headers=auth_headers)

        # 搜索网段
        response = client.get(
            "/api/v1/subnets/search?q=办公",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "subnets" in data
        # 应该至少找到一个包含"办公"的网段
        found_office_subnet = any("办公" in subnet.get("description", "") for subnet in data["subnets"])
        assert found_office_subnet

    def test_get_subnets_by_vlan(self, client, auth_headers):
        """测试根据VLAN ID获取网段"""
        # 创建带VLAN的网段
        subnet_data = {
            "network": "192.168.20.0/24",
            "netmask": "255.255.255.0",
            "vlan_id": 200,
            "description": "VLAN 200网段"
        }
        client.post("/api/v1/subnets/", json=subnet_data, headers=auth_headers)

        # 根据VLAN ID获取网段
        response = client.get("/api/v1/subnets/vlan/200", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 应该找到VLAN ID为200的网段
        vlan_200_subnets = [subnet for subnet in data if subnet.get("vlan_id") == 200]
        assert len(vlan_200_subnets) > 0

    def test_unauthorized_access(self, client):
        """测试未授权访问"""
        response = client.get("/api/v1/subnets/")
        assert response.status_code in [401, 403]  # 可能返回401或403

    def test_pagination(self, client, auth_headers):
        """测试分页功能"""
        # 创建多个网段用于测试分页
        for i in range(5):
            subnet_data = {
                "network": f"192.168.{30+i}.0/24",
                "netmask": "255.255.255.0",
                "description": f"分页测试网段{i+1}"
            }
            client.post("/api/v1/subnets/", json=subnet_data, headers=auth_headers)

        # 测试第一页
        response = client.get(
            "/api/v1/subnets/?skip=0&limit=3",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["subnets"]) <= 3
        assert data["page"] == 1
        assert data["size"] == 3

        # 测试第二页
        response = client.get(
            "/api/v1/subnets/?skip=3&limit=3",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2