from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.models.custom_field import CustomField, CustomFieldValue, EntityType
from app.schemas.custom_field import CustomFieldCreate, CustomFieldUpdate, CustomFieldValueCreate, CustomFieldValueUpdate


class CustomFieldRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_field(self, field_data: CustomFieldCreate) -> CustomField:
        """创建自定义字段"""
        db_field = CustomField(**field_data.dict())
        self.db.add(db_field)
        self.db.commit()
        self.db.refresh(db_field)
        return db_field

    def get_field_by_id(self, field_id: int) -> Optional[CustomField]:
        """根据ID获取自定义字段"""
        return self.db.query(CustomField).filter(CustomField.id == field_id).first()

    def get_fields_by_entity_type(self, entity_type: EntityType) -> List[CustomField]:
        """根据实体类型获取自定义字段列表"""
        return self.db.query(CustomField).filter(CustomField.entity_type == entity_type).all()

    def get_all_fields(self) -> List[CustomField]:
        """获取所有自定义字段"""
        return self.db.query(CustomField).all()

    def update_field(self, field_id: int, field_data: CustomFieldUpdate) -> Optional[CustomField]:
        """更新自定义字段"""
        db_field = self.get_field_by_id(field_id)
        if not db_field:
            return None
        
        update_data = field_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_field, key, value)
        
        self.db.commit()
        self.db.refresh(db_field)
        return db_field

    def delete_field(self, field_id: int) -> bool:
        """删除自定义字段"""
        db_field = self.get_field_by_id(field_id)
        if not db_field:
            return False
        
        self.db.delete(db_field)
        self.db.commit()
        return True

    def create_field_value(self, value_data: CustomFieldValueCreate) -> CustomFieldValue:
        """创建字段值"""
        # 检查是否已存在相同的字段值
        existing_value = self.db.query(CustomFieldValue).filter(
            and_(
                CustomFieldValue.field_id == value_data.field_id,
                CustomFieldValue.entity_id == value_data.entity_id,
                CustomFieldValue.entity_type == value_data.entity_type
            )
        ).first()
        
        if existing_value:
            # 更新现有值
            existing_value.field_value = value_data.field_value
            self.db.commit()
            self.db.refresh(existing_value)
            return existing_value
        else:
            # 创建新值
            db_value = CustomFieldValue(**value_data.dict())
            self.db.add(db_value)
            self.db.commit()
            self.db.refresh(db_value)
            return db_value

    def get_field_value_by_id(self, value_id: int) -> Optional[CustomFieldValue]:
        """根据ID获取字段值"""
        return self.db.query(CustomFieldValue).options(joinedload(CustomFieldValue.field)).filter(
            CustomFieldValue.id == value_id
        ).first()

    def get_entity_field_values(self, entity_id: int, entity_type: EntityType) -> List[CustomFieldValue]:
        """获取实体的所有字段值"""
        return self.db.query(CustomFieldValue).options(joinedload(CustomFieldValue.field)).filter(
            and_(
                CustomFieldValue.entity_id == entity_id,
                CustomFieldValue.entity_type == entity_type
            )
        ).all()

    def update_field_value(self, value_id: int, value_data: CustomFieldValueUpdate) -> Optional[CustomFieldValue]:
        """更新字段值"""
        db_value = self.get_field_value_by_id(value_id)
        if not db_value:
            return None
        
        update_data = value_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_value, key, value)
        
        self.db.commit()
        self.db.refresh(db_value)
        return db_value

    def delete_field_value(self, value_id: int) -> bool:
        """删除字段值"""
        db_value = self.get_field_value_by_id(value_id)
        if not db_value:
            return False
        
        self.db.delete(db_value)
        self.db.commit()
        return True

    def delete_entity_field_values(self, entity_id: int, entity_type: EntityType) -> bool:
        """删除实体的所有字段值"""
        values = self.get_entity_field_values(entity_id, entity_type)
        for value in values:
            self.db.delete(value)
        self.db.commit()
        return True

    def get_fields_with_values_for_entity(self, entity_id: int, entity_type: EntityType) -> List[Dict[str, Any]]:
        """获取实体的字段定义和值"""
        fields = self.get_fields_by_entity_type(entity_type)
        values = self.get_entity_field_values(entity_id, entity_type)
        
        # 创建值的映射
        value_map = {v.field_id: v.field_value for v in values}
        
        # 组合字段定义和值
        result = []
        for field in fields:
            result.append({
                'field': field,
                'value': value_map.get(field.id)
            })
        
        return result