import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.custom_field import CustomField, CustomFieldValue, EntityType, FieldType
from app.models.user import User
from app.core.database import get_db
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
    # 假设有一个登录接口返回token
    login_data = {
        "username": test_user.username,
        "password": "test_password"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    return {}


class TestCustomFields:
    """自定义字段测试"""

    def test_create_custom_field(self, client: TestClient, auth_headers: dict):
        """测试创建自定义字段"""
        field_data = {
            "entity_type": "ip",
            "field_name": "设备型号",
            "field_type": "text",
            "is_required": False
        }
        
        response = client.post(
            "/api/v1/custom-fields/",
            json=field_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["field_name"] == "设备型号"
        assert data["entity_type"] == "ip"
        assert data["field_type"] == "text"
        assert data["is_required"] is False

    def test_create_select_field_with_options(self, client: TestClient, auth_headers: dict):
        """测试创建带选项的选择字段"""
        field_data = {
            "entity_type": "ip",
            "field_name": "设备类型",
            "field_type": "select",
            "field_options": {
                "options": ["服务器", "工作站", "网络设备"]
            },
            "is_required": True
        }
        
        response = client.post(
            "/api/v1/custom-fields/",
            json=field_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["field_name"] == "设备类型"
        assert data["field_type"] == "select"
        assert data["field_options"]["options"] == ["服务器", "工作站", "网络设备"]
        assert data["is_required"] is True

    def test_create_select_field_without_options_fails(self, client: TestClient, auth_headers: dict):
        """测试创建选择字段但不提供选项应该失败"""
        field_data = {
            "entity_type": "ip",
            "field_name": "设备类型",
            "field_type": "select",
            "is_required": False
        }
        
        response = client.post(
            "/api/v1/custom-fields/",
            json=field_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400

    def test_get_custom_fields(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试获取自定义字段列表"""
        # 创建测试字段
        field1 = CustomField(
            entity_type=EntityType.IP,
            field_name="字段1",
            field_type=FieldType.TEXT
        )
        field2 = CustomField(
            entity_type=EntityType.SUBNET,
            field_name="字段2",
            field_type=FieldType.NUMBER
        )
        
        db_session.add_all([field1, field2])
        db_session.commit()
        
        # 获取所有字段
        response = client.get("/api/v1/custom-fields/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # 按实体类型过滤
        response = client.get("/api/v1/custom-fields/?entity_type=ip", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["field_name"] == "字段1"

    def test_update_custom_field(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试更新自定义字段"""
        field = CustomField(
            entity_type=EntityType.IP,
            field_name="原字段名",
            field_type=FieldType.TEXT
        )
        db_session.add(field)
        db_session.commit()
        db_session.refresh(field)
        
        update_data = {
            "field_name": "新字段名",
            "is_required": True
        }
        
        response = client.put(
            f"/api/v1/custom-fields/{field.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["field_name"] == "新字段名"
        assert data["is_required"] is True

    def test_delete_custom_field(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试删除自定义字段"""
        field = CustomField(
            entity_type=EntityType.IP,
            field_name="待删除字段",
            field_type=FieldType.TEXT
        )
        db_session.add(field)
        db_session.commit()
        db_session.refresh(field)
        
        response = client.delete(f"/api/v1/custom-fields/{field.id}", headers=auth_headers)
        assert response.status_code == 204
        
        # 验证字段已删除
        response = client.get(f"/api/v1/custom-fields/{field.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_set_field_value(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试设置字段值"""
        field = CustomField(
            entity_type=EntityType.IP,
            field_name="设备型号",
            field_type=FieldType.TEXT
        )
        db_session.add(field)
        db_session.commit()
        db_session.refresh(field)
        
        response = client.post(
            "/api/v1/custom-fields/values",
            params={
                "field_id": field.id,
                "entity_id": 1,
                "entity_type": "ip",
                "value": "Dell PowerEdge R740"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["field_value"] == "Dell PowerEdge R740"
        assert data["entity_id"] == 1
        assert data["entity_type"] == "ip"

    def test_get_entity_custom_fields(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试获取实体的自定义字段"""
        # 创建字段
        field = CustomField(
            entity_type=EntityType.IP,
            field_name="设备型号",
            field_type=FieldType.TEXT
        )
        db_session.add(field)
        db_session.commit()
        db_session.refresh(field)
        
        # 创建字段值
        field_value = CustomFieldValue(
            field_id=field.id,
            entity_id=1,
            entity_type=EntityType.IP,
            field_value="Dell PowerEdge R740"
        )
        db_session.add(field_value)
        db_session.commit()
        
        response = client.get("/api/v1/custom-fields/entity/ip/1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["entity_id"] == 1
        assert data["entity_type"] == "ip"
        assert len(data["fields"]) == 1
        assert data["fields"][0]["field_name"] == "设备型号"
        assert data["fields"][0]["value"] == "Dell PowerEdge R740"

    def test_update_entity_custom_fields(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试批量更新实体的自定义字段值"""
        # 创建字段
        field1 = CustomField(
            entity_type=EntityType.IP,
            field_name="设备型号",
            field_type=FieldType.TEXT
        )
        field2 = CustomField(
            entity_type=EntityType.IP,
            field_name="CPU核数",
            field_type=FieldType.NUMBER
        )
        db_session.add_all([field1, field2])
        db_session.commit()
        db_session.refresh(field1)
        db_session.refresh(field2)
        
        field_values = {
            str(field1.id): "Dell PowerEdge R740",
            str(field2.id): "16"
        }
        
        response = client.put(
            "/api/v1/custom-fields/entity/ip/1",
            json=field_values,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["entity_id"] == 1
        assert len(data["fields"]) == 2

    def test_validate_required_field(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试必填字段验证"""
        field = CustomField(
            entity_type=EntityType.IP,
            field_name="必填字段",
            field_type=FieldType.TEXT,
            is_required=True
        )
        db_session.add(field)
        db_session.commit()
        db_session.refresh(field)
        
        # 尝试设置空值应该失败
        response = client.post(
            "/api/v1/custom-fields/values",
            params={
                "field_id": field.id,
                "entity_id": 1,
                "entity_type": "ip",
                "value": ""
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400

    def test_validate_number_field(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试数字字段验证"""
        field = CustomField(
            entity_type=EntityType.IP,
            field_name="数字字段",
            field_type=FieldType.NUMBER
        )
        db_session.add(field)
        db_session.commit()
        db_session.refresh(field)
        
        # 尝试设置非数字值应该失败
        response = client.post(
            "/api/v1/custom-fields/values",
            params={
                "field_id": field.id,
                "entity_id": 1,
                "entity_type": "ip",
                "value": "not_a_number"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400

    def test_validate_select_field(self, client: TestClient, auth_headers: dict, db_session: Session):
        """测试选择字段验证"""
        field = CustomField(
            entity_type=EntityType.IP,
            field_name="选择字段",
            field_type=FieldType.SELECT,
            field_options={"options": ["选项1", "选项2", "选项3"]}
        )
        db_session.add(field)
        db_session.commit()
        db_session.refresh(field)
        
        # 设置有效选项应该成功
        response = client.post(
            "/api/v1/custom-fields/values",
            params={
                "field_id": field.id,
                "entity_id": 1,
                "entity_type": "ip",
                "value": "选项1"
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # 设置无效选项应该失败
        response = client.post(
            "/api/v1/custom-fields/values",
            params={
                "field_id": field.id,
                "entity_id": 2,
                "entity_type": "ip",
                "value": "无效选项"
            },
            headers=auth_headers
        )
        assert response.status_code == 400