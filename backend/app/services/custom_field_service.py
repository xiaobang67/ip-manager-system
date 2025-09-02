from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.custom_field_repository import CustomFieldRepository
from app.schemas.custom_field import (
    CustomFieldCreate, CustomFieldUpdate, CustomFieldResponse,
    CustomFieldValueCreate, CustomFieldValueUpdate, CustomFieldValueResponse,
    CustomFieldWithValue, EntityCustomFields
)
from app.models.custom_field import CustomField, CustomFieldValue, EntityType, FieldType
from app.core.exceptions import ValidationError, NotFoundError


class CustomFieldService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CustomFieldRepository(db)

    def create_field(self, field_data: CustomFieldCreate) -> CustomFieldResponse:
        """创建自定义字段"""
        # 检查字段名称是否已存在于同一实体类型中
        existing_fields = self.repository.get_fields_by_entity_type(field_data.entity_type)
        if any(f.field_name == field_data.field_name for f in existing_fields):
            raise ValidationError(f"Field name '{field_data.field_name}' already exists for {field_data.entity_type}")
        
        # 验证SELECT类型字段的选项
        if field_data.field_type == FieldType.SELECT:
            if not field_data.field_options or 'options' not in field_data.field_options:
                raise ValidationError("SELECT type fields must have options")
            if not isinstance(field_data.field_options['options'], list) or len(field_data.field_options['options']) == 0:
                raise ValidationError("SELECT type fields must have at least one option")
        
        db_field = self.repository.create_field(field_data)
        return CustomFieldResponse.from_orm(db_field)

    def get_field_by_id(self, field_id: int) -> CustomFieldResponse:
        """根据ID获取自定义字段"""
        db_field = self.repository.get_field_by_id(field_id)
        if not db_field:
            raise NotFoundError(f"Custom field with id {field_id} not found")
        return CustomFieldResponse.from_orm(db_field)

    def get_fields_by_entity_type(self, entity_type: EntityType) -> List[CustomFieldResponse]:
        """根据实体类型获取自定义字段列表"""
        db_fields = self.repository.get_fields_by_entity_type(entity_type)
        return [CustomFieldResponse.from_orm(field) for field in db_fields]

    def get_all_fields(self) -> List[CustomFieldResponse]:
        """获取所有自定义字段"""
        db_fields = self.repository.get_all_fields()
        return [CustomFieldResponse.from_orm(field) for field in db_fields]

    def update_field(self, field_id: int, field_data: CustomFieldUpdate) -> CustomFieldResponse:
        """更新自定义字段"""
        # 检查字段是否存在
        existing_field = self.repository.get_field_by_id(field_id)
        if not existing_field:
            raise NotFoundError(f"Custom field with id {field_id} not found")
        
        # 如果更新字段名称，检查是否与同类型其他字段冲突
        if field_data.field_name and field_data.field_name != existing_field.field_name:
            existing_fields = self.repository.get_fields_by_entity_type(existing_field.entity_type)
            if any(f.field_name == field_data.field_name and f.id != field_id for f in existing_fields):
                raise ValidationError(f"Field name '{field_data.field_name}' already exists for {existing_field.entity_type}")
        
        # 验证SELECT类型字段的选项
        if field_data.field_type == FieldType.SELECT or (field_data.field_type is None and existing_field.field_type == FieldType.SELECT):
            field_options = field_data.field_options if field_data.field_options is not None else existing_field.field_options
            if not field_options or 'options' not in field_options:
                raise ValidationError("SELECT type fields must have options")
            if not isinstance(field_options['options'], list) or len(field_options['options']) == 0:
                raise ValidationError("SELECT type fields must have at least one option")
        
        db_field = self.repository.update_field(field_id, field_data)
        return CustomFieldResponse.from_orm(db_field)

    def delete_field(self, field_id: int) -> bool:
        """删除自定义字段"""
        if not self.repository.get_field_by_id(field_id):
            raise NotFoundError(f"Custom field with id {field_id} not found")
        
        return self.repository.delete_field(field_id)

    def set_field_value(self, field_id: int, entity_id: int, entity_type: EntityType, value: str) -> CustomFieldValueResponse:
        """设置字段值"""
        # 检查字段是否存在
        field = self.repository.get_field_by_id(field_id)
        if not field:
            raise NotFoundError(f"Custom field with id {field_id} not found")
        
        # 检查实体类型是否匹配
        if field.entity_type != entity_type:
            raise ValidationError(f"Field is for {field.entity_type} entities, not {entity_type}")
        
        # 验证值
        self._validate_field_value(field, value)
        
        value_data = CustomFieldValueCreate(
            field_id=field_id,
            entity_id=entity_id,
            entity_type=entity_type,
            field_value=value
        )
        
        db_value = self.repository.create_field_value(value_data)
        return CustomFieldValueResponse.from_orm(db_value)

    def get_entity_fields_with_values(self, entity_id: int, entity_type: EntityType) -> EntityCustomFields:
        """获取实体的所有字段和值"""
        fields_with_values = self.repository.get_fields_with_values_for_entity(entity_id, entity_type)
        
        fields = []
        for item in fields_with_values:
            field_response = CustomFieldResponse.from_orm(item['field'])
            field_with_value = CustomFieldWithValue(
                **field_response.dict(),
                value=item['value']
            )
            fields.append(field_with_value)
        
        return EntityCustomFields(
            entity_id=entity_id,
            entity_type=entity_type,
            fields=fields
        )

    def update_entity_fields(self, entity_id: int, entity_type: EntityType, field_values: Dict[int, str]) -> EntityCustomFields:
        """批量更新实体的字段值"""
        # 获取所有相关字段
        fields = self.repository.get_fields_by_entity_type(entity_type)
        field_map = {f.id: f for f in fields}
        
        # 验证所有字段ID是否有效
        invalid_field_ids = set(field_values.keys()) - set(field_map.keys())
        if invalid_field_ids:
            raise ValidationError(f"Invalid field IDs: {invalid_field_ids}")
        
        # 验证并设置每个字段值
        for field_id, value in field_values.items():
            field = field_map[field_id]
            self._validate_field_value(field, value)
            
            value_data = CustomFieldValueCreate(
                field_id=field_id,
                entity_id=entity_id,
                entity_type=entity_type,
                field_value=value
            )
            self.repository.create_field_value(value_data)
        
        return self.get_entity_fields_with_values(entity_id, entity_type)

    def delete_entity_fields(self, entity_id: int, entity_type: EntityType) -> bool:
        """删除实体的所有字段值"""
        return self.repository.delete_entity_field_values(entity_id, entity_type)

    def _validate_field_value(self, field: CustomField, value: str) -> None:
        """验证字段值"""
        if field.is_required and (not value or value.strip() == ""):
            raise ValidationError(f"Field '{field.field_name}' is required")
        
        if not value:
            return  # 空值对于非必填字段是允许的
        
        if field.field_type == FieldType.NUMBER:
            try:
                float(value)
            except ValueError:
                raise ValidationError(f"Field '{field.field_name}' must be a number")
        
        elif field.field_type == FieldType.DATE:
            from datetime import datetime
            try:
                datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError(f"Field '{field.field_name}' must be a valid date in ISO format")
        
        elif field.field_type == FieldType.SELECT:
            if field.field_options and 'options' in field.field_options:
                valid_options = field.field_options['options']
                if value not in valid_options:
                    raise ValidationError(f"Field '{field.field_name}' must be one of: {valid_options}")
        
        # TEXT类型不需要特殊验证