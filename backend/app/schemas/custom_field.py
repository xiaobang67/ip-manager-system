from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from app.models.custom_field import EntityType, FieldType


class CustomFieldBase(BaseModel):
    entity_type: EntityType
    field_name: str = Field(..., min_length=1, max_length=50)
    field_type: FieldType
    field_options: Optional[Dict[str, Any]] = None
    is_required: bool = False

    @validator('field_options')
    def validate_field_options(cls, v, values):
        if values.get('field_type') == FieldType.SELECT and not v:
            raise ValueError('field_options is required for SELECT type fields')
        if values.get('field_type') == FieldType.SELECT and v:
            if not isinstance(v, dict) or 'options' not in v:
                raise ValueError('field_options must contain "options" key for SELECT type')
            if not isinstance(v['options'], list) or len(v['options']) == 0:
                raise ValueError('options must be a non-empty list')
        return v


class CustomFieldCreate(CustomFieldBase):
    pass


class CustomFieldUpdate(BaseModel):
    field_name: Optional[str] = Field(None, min_length=1, max_length=50)
    field_type: Optional[FieldType] = None
    field_options: Optional[Dict[str, Any]] = None
    is_required: Optional[bool] = None


class CustomFieldResponse(CustomFieldBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CustomFieldValueBase(BaseModel):
    field_id: int
    entity_id: int
    entity_type: EntityType
    field_value: Optional[str] = None


class CustomFieldValueCreate(CustomFieldValueBase):
    pass


class CustomFieldValueUpdate(BaseModel):
    field_value: Optional[str] = None


class CustomFieldValueResponse(CustomFieldValueBase):
    id: int
    field: Optional[CustomFieldResponse] = None

    class Config:
        from_attributes = True


class CustomFieldWithValue(CustomFieldResponse):
    value: Optional[str] = None


class EntityCustomFields(BaseModel):
    entity_id: int
    entity_type: EntityType
    fields: List[CustomFieldWithValue]