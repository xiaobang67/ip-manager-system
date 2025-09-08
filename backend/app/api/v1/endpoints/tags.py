from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user, require_admin
from app.services.tag_service import TagService
from app.schemas.tag import TagCreate, TagUpdate, TagResponse, TagAssignment, EntityTags
from app.models.user import User
from app.core.exceptions import ValidationError, NotFoundError

router = APIRouter()


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """创建标签 - 仅管理员可操作"""
    try:
        service = TagService(db)
        return service.create_tag(tag_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[TagResponse])
def get_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None, description="搜索标签名称"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取标签列表"""
    service = TagService(db)
    if search:
        return service.search_tags(search)
    return service.get_all_tags(skip, limit)


@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据ID获取标签"""
    try:
        service = TagService(db)
        return service.get_tag_by_id(tag_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """更新标签 - 仅管理员可操作"""
    try:
        service = TagService(db)
        return service.update_tag(tag_id, tag_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """删除标签 - 仅管理员可操作"""
    try:
        service = TagService(db)
        service.delete_tag(tag_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/assign", status_code=status.HTTP_200_OK)
def assign_tags(
    assignment: TagAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为实体分配标签"""
    try:
        service = TagService(db)
        if assignment.entity_type == "ip":
            service.assign_tags_to_ip(assignment.entity_id, assignment.tag_ids)
        elif assignment.entity_type == "subnet":
            service.assign_tags_to_subnet(assignment.entity_id, assignment.tag_ids)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid entity type")
        
        return {"message": "Tags assigned successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/entity/ip/{ip_id}", response_model=EntityTags)
def get_ip_tags(
    ip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取IP地址的标签"""
    service = TagService(db)
    return service.get_ip_tags(ip_id)


@router.get("/entity/subnet/{subnet_id}", response_model=EntityTags)
def get_subnet_tags(
    subnet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取网段的标签"""
    service = TagService(db)
    return service.get_subnet_tags(subnet_id)


@router.post("/entity/ip/{ip_id}/tags/{tag_id}", status_code=status.HTTP_200_OK)
def add_tag_to_ip(
    ip_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为IP地址添加标签"""
    try:
        service = TagService(db)
        service.add_tag_to_ip(ip_id, tag_id)
        return {"message": "Tag added to IP successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/entity/subnet/{subnet_id}/tags/{tag_id}", status_code=status.HTTP_200_OK)
def add_tag_to_subnet(
    subnet_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为网段添加标签"""
    try:
        service = TagService(db)
        service.add_tag_to_subnet(subnet_id, tag_id)
        return {"message": "Tag added to subnet successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/entity/ip/{ip_id}/tags/{tag_id}", status_code=status.HTTP_200_OK)
def remove_tag_from_ip(
    ip_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从IP地址移除标签"""
    try:
        service = TagService(db)
        service.remove_tag_from_ip(ip_id, tag_id)
        return {"message": "Tag removed from IP successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/entity/subnet/{subnet_id}/tags/{tag_id}", status_code=status.HTTP_200_OK)
def remove_tag_from_subnet(
    subnet_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从网段移除标签"""
    try:
        service = TagService(db)
        service.remove_tag_from_subnet(subnet_id, tag_id)
        return {"message": "Tag removed from subnet successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/stats/usage", response_model=List[dict])
def get_tags_usage_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取标签使用统计"""
    service = TagService(db)
    return service.get_tags_usage_stats()