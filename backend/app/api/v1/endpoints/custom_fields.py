from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user, require_admin
from app.services.custom_field_service import CustomFieldService
from app.schemas.custom_field import (
    CustomFieldCreate, CustomFieldUpdate, CustomFieldResponse,
    CustomFieldValueCreate, CustomFieldValueUpdate, CustomFieldValueResponse,
    EntityCustomFields, EntityType
)
from app.models.user import User
from app.core.exceptions import ValidationError, NotFoundError

router = APIRouter()


@router.post("/", response_model=CustomFieldResponse, status_code=status.HTTP_201_CREATED)
def create_custom_field(
    field_data: CustomFieldCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """创建自定义字段 - 仅管理员可操作"""
    try:
        service = CustomFieldService(db)
        return service.create_field(field_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[CustomFieldResponse])
def get_custom_fields(
    entity_type: EntityType = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取自定义字段列表"""
    service = CustomFieldService(db)
    if entity_type:
        return service.get_fields_by_entity_type(entity_type)
    return service.get_all_fields()


@router.get("/{field_id}", response_model=CustomFieldResponse)
def get_custom_field(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据ID获取自定义字段"""
    try:
        service = CustomFieldService(db)
        return service.get_field_by_id(field_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{field_id}", response_model=CustomFieldResponse)
def update_custom_field(
    field_id: int,
    field_data: CustomFieldUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """更新自定义字段 - 仅管理员可操作"""
    try:
        service = CustomFieldService(db)
        return service.update_field(field_id, field_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_field(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """删除自定义字段 - 仅管理员可操作"""
    try:
        service = CustomFieldService(db)
        service.delete_field(field_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/entity/{entity_type}/{entity_id}", response_model=EntityCustomFields)
def get_entity_custom_fields(
    entity_type: EntityType,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取实体的自定义字段和值"""
    service = CustomFieldService(db)
    return service.get_entity_fields_with_values(entity_id, entity_type)


@router.put("/entity/{entity_type}/{entity_id}", response_model=EntityCustomFields)
def update_entity_custom_fields(
    entity_type: EntityType,
    entity_id: int,
    field_values: Dict[int, str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新实体的自定义字段值"""
    try:
        service = CustomFieldService(db)
        return service.update_entity_fields(entity_id, entity_type, field_values)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/entity/{entity_type}/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entity_custom_fields(
    entity_type: EntityType,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除实体的所有自定义字段值"""
    service = CustomFieldService(db)
    service.delete_entity_fields(entity_id, entity_type)


@router.post("/values", response_model=CustomFieldValueResponse, status_code=status.HTTP_201_CREATED)
def set_field_value(
    field_id: int,
    entity_id: int,
    entity_type: EntityType,
    value: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """设置字段值"""
    try:
        service = CustomFieldService(db)
        return service.set_field_value(field_id, entity_id, entity_type, value)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))