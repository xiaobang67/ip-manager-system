from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User
from app.services.subnet_service import SubnetService
from app.schemas.subnet import (
    SubnetCreate,
    SubnetUpdate,
    SubnetResponse,
    SubnetListResponse,
    SubnetValidationRequest,
    SubnetValidationResponse
)
from app.core.exceptions import ValidationError, NotFoundError, ConflictError

router = APIRouter()


@router.post("/", response_model=SubnetResponse, status_code=status.HTTP_201_CREATED)
async def create_subnet(
    subnet_data: SubnetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """创建新网段 - 仅管理员可操作"""
    try:
        subnet_service = SubnetService(db)
        return subnet_service.create_subnet(subnet_data, current_user.id)
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/", response_model=SubnetListResponse)
async def get_subnets(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回的记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取网段列表"""
    subnet_service = SubnetService(db)
    subnets, total = subnet_service.get_subnets(skip, limit)
    
    return SubnetListResponse(
        subnets=subnets,
        total=total,
        page=skip // limit + 1,
        size=limit
    )


@router.get("/search", response_model=SubnetListResponse)
async def search_subnets(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回的记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """搜索网段"""
    subnet_service = SubnetService(db)
    subnets, total = subnet_service.search_subnets(q, skip, limit)
    
    return SubnetListResponse(
        subnets=subnets,
        total=total,
        page=skip // limit + 1,
        size=limit
    )


@router.get("/vlan/{vlan_id}", response_model=List[SubnetResponse])
async def get_subnets_by_vlan(
    vlan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据VLAN ID获取网段列表"""
    subnet_service = SubnetService(db)
    return subnet_service.get_subnets_by_vlan(vlan_id)


@router.get("/{subnet_id}", response_model=SubnetResponse)
async def get_subnet(
    subnet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个网段详情"""
    try:
        subnet_service = SubnetService(db)
        return subnet_service.get_subnet(subnet_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{subnet_id}", response_model=SubnetResponse)
async def update_subnet(
    subnet_id: int,
    subnet_data: SubnetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """更新网段 - 仅管理员可操作"""
    try:
        subnet_service = SubnetService(db)
        return subnet_service.update_subnet(subnet_id, subnet_data)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.delete("/{subnet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subnet(
    subnet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """删除网段 - 仅管理员可操作"""
    try:
        subnet_service = SubnetService(db)
        subnet_service.delete_subnet(subnet_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post("/validate", response_model=SubnetValidationResponse)
async def validate_subnet(
    validation_data: SubnetValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """验证网段格式和重叠检测"""
    subnet_service = SubnetService(db)
    return subnet_service.validate_subnet(
        validation_data.network,
        validation_data.exclude_id
    )


@router.get("/{subnet_id}/ips")
async def get_subnet_ips(
    subnet_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回的记录数"),
    status_filter: str = Query(None, description="按状态过滤: available, allocated, reserved"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取网段下的IP地址列表"""
    try:
        subnet_service = SubnetService(db)
        # 首先验证网段是否存在
        subnet_service.get_subnet(subnet_id)
        
        # 这里应该调用IP服务来获取IP列表，暂时返回占位符
        return {
            "message": "获取网段IP地址列表功能待实现",
            "subnet_id": subnet_id,
            "skip": skip,
            "limit": limit,
            "status_filter": status_filter
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{subnet_id}/sync-ips")
async def sync_subnet_ips(
    subnet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """同步网段的IP地址列表 - 根据CIDR重新生成正确的IP地址范围"""
    try:
        from app.services.ip_service import IPService
        
        # 检查网段是否存在
        subnet_service = SubnetService(db)
        subnet = subnet_service.get_subnet(subnet_id)
        
        # 同步IP地址
        ip_service = IPService(db)
        sync_result = ip_service.sync_subnet_ips(subnet_id, subnet.network)
        
        return {
            "message": f"IP地址同步完成",
            "subnet_id": subnet_id,
            "network": subnet.network,
            "stats": {
                "added": sync_result.added,
                "removed": sync_result.removed,
                "kept": sync_result.kept
            }
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"同步失败: {str(e)}"
        )