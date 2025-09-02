import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.tag import Tag
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.models.user import User
from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_user(db_session: Session):
    """创建测试用户"""
    user = User(
        username="testuser",
        password_hash="hashed_password",
        email="test@example.com",
        role="admin"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client: TestClient, test_user: User):
    """获取认证头"""
    # 这里需要根据实际的认证实现来获取token
    login_data = {
        "username": test_user.username,
        "password": "test_password"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def test_subnet(db_session: Session, test_user: User):
    """创建测试网段"""
    subnet = Subnet(
        network="192.168.1.0/24",
        netmask="255.255.255.0",
        gateway="192.168.1.1",
        description="测试网段",
        created_by=test_user.id
    )
    db_session.add(subnet)
    db_session.commit()
    db_session.refresh(subnet)
    return subnet


@pytest.fixture
def test_ip(db_session: Session, test_subnet: Subnet):
    """创建测试IP地址"""
    ip = IPAddress(
        ip_address="192.168.1.100",
        subnet_id=test_subnet.id,
        status=IPStatus.AVAILABLE,
        hostname="test-host"
    )
    db_session.add(ip)
    db_session.commit()
    db_session.refresh(ip)
    return ip


class TestTags:
    """标签测试"""

    def test_create_tag(self, client: TestClient, auth_headers: dict):
        """测试创建标签"""
        tag_data = {
            "name": "生产环境",
            "color": "#ff0000",
            "description": "生产环境服务器"
        }
        
        response = client.post(
            "/api/v1/tags/",
            json=tag_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "生产环境"
        assert data["color"] == "#ff0000"
        assert data["description"] == "生产环境服务器"

    def test_create_tag_with_invalid_color(self, client: TestClient, auth_headers: dict):
        """测试创建标签时使用无效颜色"""
        tag_data = {
            "name": "测试标签",
            "color": "invalid_color"
        }
        
        response = client.post(
            "/api/v1/tags/",
            json=tag_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # 验证错误

    def test_create_tag_with_invalid_name(self, client: TestClient, auth_headers: dict):
        """测试创建标签时使用无效名称"""
        tag_data = {
            "name": "invalid@name!",  # 包含特殊字符
            "color": "#007bff"
        }
        
        response = client.post(
            "/api/v1/tags/",
            json=tag_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # 验证错误

    def test_create_duplicate_tag_name(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试创建重复名称的标签"""
        # 先创建一个标签
        existing_tag = Tag(name="重复标签", color="#007bff")
        db_session.add(existing_tag)
        db_session.commit()
        
        tag_data = {
            "name": "重复标签",
            "color": "#ff0000"
        }
        
        response = client.post(
            "/api/v1/tags/",
            json=tag_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400

    def test_get_tags(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试获取标签列表"""
        # 创建测试标签
        tag1 = Tag(name="标签1", color="#ff0000")
        tag2 = Tag(name="标签2", color="#00ff00")
        tag3 = Tag(name="标签3", color="#0000ff")
        
        db_session.add_all([tag1, tag2, tag3])
        db_session.commit()
        
        response = client.get("/api/v1/tags/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_tags_with_pagination(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试分页获取标签"""
        # 创建多个标签
        tags = [Tag(name=f"标签{i}", color="#007bff") for i in range(25)]
        db_session.add_all(tags)
        db_session.commit()
        
        # 测试分页
        response = client.get("/api/v1/tags/?skip=0&limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10

    def test_search_tags(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试搜索标签"""
        tag1 = Tag(name="生产环境", color="#ff0000")
        tag2 = Tag(name="测试环境", color="#00ff00")
        tag3 = Tag(name="开发环境", color="#0000ff")
        
        db_session.add_all([tag1, tag2, tag3])
        db_session.commit()
        
        response = client.get("/api/v1/tags/?search=环境", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        response = client.get("/api/v1/tags/?search=生产", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "生产环境"

    def test_update_tag(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试更新标签"""
        tag = Tag(name="原标签名", color="#007bff", description="原描述")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)
        
        update_data = {
            "name": "新标签名",
            "color": "#ff0000",
            "description": "新描述"
        }
        
        response = client.put(
            f"/api/v1/tags/{tag.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新标签名"
        assert data["color"] == "#ff0000"
        assert data["description"] == "新描述"

    def test_delete_tag(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试删除标签"""
        tag = Tag(name="待删除标签", color="#007bff")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)
        
        response = client.delete(f"/api/v1/tags/{tag.id}", headers=auth_headers)
        assert response.status_code == 204
        
        # 验证标签已删除
        response = client.get(f"/api/v1/tags/{tag.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_assign_tags_to_ip(self, client: TestClient, auth_headers: dict, db_session: Session, test_ip: IPAddress):
        """测试为IP地址分配标签"""
        # 创建标签
        tag1 = Tag(name="生产环境", color="#ff0000")
        tag2 = Tag(name="Web服务器", color="#00ff00")
        db_session.add_all([tag1, tag2])
        db_session.commit()
        db_session.refresh(tag1)
        db_session.refresh(tag2)
        
        assignment_data = {
            "entity_type": "ip",
            "entity_id": test_ip.id,
            "tag_ids": [tag1.id, tag2.id]
        }
        
        response = client.post(
            "/api/v1/tags/assign",
            json=assignment_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200

    def test_assign_tags_to_subnet(self, client: TestClient, auth_headers: dict, db_session: Session, test_subnet: Subnet):
        """测试为网段分配标签"""
        # 创建标签
        tag1 = Tag(name="DMZ", color="#ff0000")
        tag2 = Tag(name="内网", color="#00ff00")
        db_session.add_all([tag1, tag2])
        db_session.commit()
        db_session.refresh(tag1)
        db_session.refresh(tag2)
        
        assignment_data = {
            "entity_type": "subnet",
            "entity_id": test_subnet.id,
            "tag_ids": [tag1.id, tag2.id]
        }
        
        response = client.post(
            "/api/v1/tags/assign",
            json=assignment_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200

    def test_get_ip_tags(self, client: TestClient, auth_headers: dict, db_session: Session, test_ip: IPAddress):
        """测试获取IP地址的标签"""
        # 创建标签并关联到IP
        tag = Tag(name="测试标签", color="#007bff")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)
        
        test_ip.tags.append(tag)
        db_session.commit()
        
        response = client.get(f"/api/v1/tags/entity/ip/{test_ip.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["entity_id"] == test_ip.id
        assert data["entity_type"] == "ip"
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == "测试标签"

    def test_get_subnet_tags(self, client: TestClient, auth_headers: dict, db_session: Session, test_subnet: Subnet):
        """测试获取网段的标签"""
        # 创建标签并关联到网段
        tag = Tag(name="网段标签", color="#007bff")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)
        
        test_subnet.tags.append(tag)
        db_session.commit()
        
        response = client.get(f"/api/v1/tags/entity/subnet/{test_subnet.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["entity_id"] == test_subnet.id
        assert data["entity_type"] == "subnet"
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == "网段标签"

    def test_add_tag_to_ip(self, client: TestClient, auth_headers: dict, db_session: Session, test_ip: IPAddress):
        """测试为IP地址添加单个标签"""
        tag = Tag(name="新标签", color="#007bff")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)
        
        response = client.post(
            f"/api/v1/tags/entity/ip/{test_ip.id}/tags/{tag.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # 验证标签已添加
        response = client.get(f"/api/v1/tags/entity/ip/{test_ip.id}", headers=auth_headers)
        data = response.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == "新标签"

    def test_remove_tag_from_ip(self, client: TestClient, auth_headers: dict, db_session: Session, test_ip: IPAddress):
        """测试从IP地址移除标签"""
        # 创建标签并关联到IP
        tag = Tag(name="待移除标签", color="#007bff")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)
        
        test_ip.tags.append(tag)
        db_session.commit()
        
        # 移除标签
        response = client.delete(
            f"/api/v1/tags/entity/ip/{test_ip.id}/tags/{tag.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # 验证标签已移除
        response = client.get(f"/api/v1/tags/entity/ip/{test_ip.id}", headers=auth_headers)
        data = response.json()
        assert len(data["tags"]) == 0

    def test_get_tags_usage_stats(self, client: TestClient, auth_headers: dict, db_session: Session, test_ip: IPAddress, test_subnet: Subnet):
        """测试获取标签使用统计"""
        # 创建标签
        tag1 = Tag(name="常用标签", color="#007bff")
        tag2 = Tag(name="少用标签", color="#ff0000")
        db_session.add_all([tag1, tag2])
        db_session.commit()
        db_session.refresh(tag1)
        db_session.refresh(tag2)
        
        # 关联标签到实体
        test_ip.tags.append(tag1)
        test_subnet.tags.append(tag1)
        test_ip.tags.append(tag2)
        db_session.commit()
        
        response = client.get("/api/v1/tags/stats/usage", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # 找到对应的统计数据
        tag1_stats = next((stat for stat in data if stat["tag"]["name"] == "常用标签"), None)
        tag2_stats = next((stat for stat in data if stat["tag"]["name"] == "少用标签"), None)
        
        assert tag1_stats is not None
        assert tag1_stats["ip_count"] == 1
        assert tag1_stats["subnet_count"] == 1
        assert tag1_stats["total_usage"] == 2
        
        assert tag2_stats is not None
        assert tag2_stats["ip_count"] == 1
        assert tag2_stats["subnet_count"] == 0
        assert tag2_stats["total_usage"] == 1

    def test_assign_nonexistent_tag(self, client: TestClient, auth_headers: dict, test_ip: IPAddress):
        """测试分配不存在的标签"""
        assignment_data = {
            "entity_type": "ip",
            "entity_id": test_ip.id,
            "tag_ids": [99999]  # 不存在的标签ID
        }
        
        response = client.post(
            "/api/v1/tags/assign",
            json=assignment_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_assign_tags_to_nonexistent_entity(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试为不存在的实体分配标签"""
        tag = Tag(name="测试标签", color="#007bff")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)
        
        assignment_data = {
            "entity_type": "ip",
            "entity_id": 99999,  # 不存在的IP ID
            "tag_ids": [tag.id]
        }
        
        response = client.post(
            "/api/v1/tags/assign",
            json=assignment_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404