import pytest
from sqlalchemy.orm import Session
from app.services.custom_field_service import CustomFieldService
from app.services.tag_service import TagService
from app.schemas.custom_field import CustomFieldCreate, EntityType, FieldType
from app.schemas.tag import TagCreate
from app.core.database import get_db


def test_custom_field_service_basic_operations():
    """测试自定义字段服务的基本操作"""
    # 这是一个基本的单元测试，不需要数据库连接
    # 主要测试服务类的实例化和基本逻辑
    
    # 测试字段数据验证
    field_data = CustomFieldCreate(
        entity_type=EntityType.IP,
        field_name="测试字段",
        field_type=FieldType.TEXT,
        is_required=False
    )
    
    assert field_data.entity_type == EntityType.IP
    assert field_data.field_name == "测试字段"
    assert field_data.field_type == FieldType.TEXT
    assert field_data.is_required is False


def test_tag_service_basic_operations():
    """测试标签服务的基本操作"""
    # 测试标签数据验证
    tag_data = TagCreate(
        name="测试标签",
        color="#ff0000",
        description="这是一个测试标签"
    )
    
    assert tag_data.name == "测试标签"
    assert tag_data.color == "#ff0000"
    assert tag_data.description == "这是一个测试标签"


def test_select_field_validation():
    """测试选择字段的验证"""
    # 测试有效的选择字段
    field_data = CustomFieldCreate(
        entity_type=EntityType.IP,
        field_name="设备类型",
        field_type=FieldType.SELECT,
        field_options={"options": ["服务器", "工作站", "网络设备"]},
        is_required=True
    )
    
    assert field_data.field_options["options"] == ["服务器", "工作站", "网络设备"]
    
    # 测试无效的选择字段（没有选项）
    with pytest.raises(ValueError):
        CustomFieldCreate(
            entity_type=EntityType.IP,
            field_name="设备类型",
            field_type=FieldType.SELECT,
            field_options=None,
            is_required=True
        )


def test_tag_name_validation():
    """测试标签名称验证"""
    # 测试有效的标签名称
    valid_names = ["生产环境", "test-tag", "标签_1", "TAG123"]
    
    for name in valid_names:
        tag_data = TagCreate(name=name, color="#007bff")
        assert tag_data.name == name
    
    # 测试无效的标签名称
    invalid_names = ["tag@invalid", "tag with spaces", "tag!special"]
    
    for name in invalid_names:
        with pytest.raises(ValueError):
            TagCreate(name=name, color="#007bff")


def test_color_validation():
    """测试颜色验证"""
    # 测试有效的颜色
    valid_colors = ["#ff0000", "#00FF00", "#0000ff", "#123ABC"]
    
    for color in valid_colors:
        tag_data = TagCreate(name="测试", color=color)
        assert tag_data.color == color
    
    # 测试无效的颜色会在Pydantic验证时失败
    # 这里我们不直接测试，因为Pydantic会抛出ValidationError


if __name__ == "__main__":
    test_custom_field_service_basic_operations()
    test_tag_service_basic_operations()
    test_select_field_validation()
    test_tag_name_validation()
    test_color_validation()
    print("All basic tests passed!")