from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.ip_service import IPService
from app.services.audit_service import AuditService
from app.schemas.ip_address import (
    IPAddressResponse, IPAllocationRequest, IPReservationRequest, 
    IPReleaseRequest, IPSearchRequest, IPStatisticsResponse,
    IPConflictResponse, IPRangeStatusRequest, IPRangeStatusResponse,
    BulkIPOperationRequest, BulkIPOperationResponse,
    SearchHistoryRequest, SearchHistoryResponse, IPDeleteRequest
)
from app.core.exceptions import ValidationError, NotFoundError, ConflictError

router = APIRouter()


@router.get("/", response_model=List[IPAddressResponse])
async def get_ip_addresses(
    subnet_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取IP地址列表"""
    try:
        ip_service = IPService(db)
        search_request = IPSearchRequest(
            subnet_id=subnet_id,
            status=status,
            skip=skip,
            limit=limit
        )
        ips, total = ip_service.search_ips(search_request)
        return ips
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取IP地址列表失败: {str(e)}"
        )


@router.post("/allocate", response_model=IPAddressResponse)
async def allocate_ip(
    request: IPAllocationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    http_request: Request = None
):
    """分配IP地址"""
    try:
        ip_service = IPService(db)
        audit_service = AuditService(db)
        
        # 执行IP分配
        allocated_ip = ip_service.allocate_ip(request, current_user.id)
        
        # 记录审计日志
        audit_service.log_operation(
            user_id=current_user.id,
            action="ALLOCATE",
            entity_type="ip",
            entity_id=allocated_ip.id,
            new_values={
                "ip_address": allocated_ip.ip_address,
                "subnet_id": allocated_ip.subnet_id,
                "status": allocated_ip.status,
                "mac_address": allocated_ip.mac_address,
                "hostname": allocated_ip.hostname,
                "assigned_to": allocated_ip.assigned_to
            },
            ip_address=http_request.client.host if http_request else None,
            user_agent=http_request.headers.get("user-agent") if http_request else None
        )
        
        return allocated_ip
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配IP地址失败: {str(e)}"
        )


@router.post("/reserve", response_model=IPAddressResponse)
async def reserve_ip(
    request: IPReservationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    http_request: Request = None
):
    """保留IP地址"""
    try:
        ip_service = IPService(db)
        audit_service = AuditService(db)
        
        # 执行IP保留
        reserved_ip = ip_service.reserve_ip(request, current_user.id)
        
        # 记录审计日志
        audit_service.log_operation(
            user_id=current_user.id,
            action="RESERVE",
            entity_type="ip",
            entity_id=reserved_ip.id,
            new_values={
                "ip_address": reserved_ip.ip_address,
                "status": reserved_ip.status,
                "reason": request.reason
            },
            ip_address=http_request.client.host if http_request else None,
            user_agent=http_request.headers.get("user-agent") if http_request else None
        )
        
        return reserved_ip
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保留IP地址失败: {str(e)}"
        )


@router.post("/release", response_model=IPAddressResponse)
async def release_ip(
    request: IPReleaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    http_request: Request = None
):
    """释放IP地址"""
    try:
        ip_service = IPService(db)
        audit_service = AuditService(db)
        
        # 获取释放前的IP信息用于审计
        ip_before = ip_service.ip_repo.get_by_ip_address(request.ip_address)
        old_values = {
            "status": ip_before.status,
            "mac_address": ip_before.mac_address,
            "hostname": ip_before.hostname,
            "assigned_to": ip_before.assigned_to
        } if ip_before else None
        
        # 执行IP释放
        released_ip = ip_service.release_ip(request, current_user.id)
        
        # 记录审计日志
        audit_service.log_operation(
            user_id=current_user.id,
            action="RELEASE",
            entity_type="ip",
            entity_id=released_ip.id,
            old_values=old_values,
            new_values={
                "ip_address": released_ip.ip_address,
                "status": released_ip.status,
                "reason": request.reason
            },
            ip_address=http_request.client.host if http_request else None,
            user_agent=http_request.headers.get("user-agent") if http_request else None
        )
        
        return released_ip
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"释放IP地址失败: {str(e)}"
        )


@router.delete("/delete")
async def delete_ip(
    request: IPDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    http_request: Request = None
):
    """删除IP地址"""
    try:
        ip_service = IPService(db)
        audit_service = AuditService(db)
        
        # 获取删除前的IP信息用于审计
        ip_before = ip_service.ip_repo.get_by_ip_address(request.ip_address)
        old_values = {
            "ip_address": ip_before.ip_address,
            "status": ip_before.status,
            "mac_address": ip_before.mac_address,
            "hostname": ip_before.hostname,
            "assigned_to": ip_before.assigned_to,
            "description": ip_before.description
        } if ip_before else None
        
        # 执行IP删除
        result = ip_service.delete_ip(request, current_user.id)
        
        # 记录审计日志
        audit_service.log_operation(
            user_id=current_user.id,
            action="DELETE",
            entity_type="ip",
            entity_id=ip_before.id if ip_before else None,
            old_values=old_values,
            new_values={
                "reason": request.reason,
                "deleted": True
            },
            ip_address=http_request.client.host if http_request else None,
            user_agent=http_request.headers.get("user-agent") if http_request else None
        )
        
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除IP地址失败: {str(e)}"
        )


@router.get("/search", response_model=List[IPAddressResponse])
async def search_ips(
    query: Optional[str] = None,
    subnet_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """搜索IP地址 - 简单搜索接口（保持向后兼容）"""
    try:
        print(f"搜索参数: query={query}, subnet_id={subnet_id}, status={status}, skip={skip}, limit={limit}")  # 调试信息
        
        ip_service = IPService(db)
        search_request = IPSearchRequest(
            query=query,
            subnet_id=subnet_id,
            status=status,
            skip=skip,
            limit=limit
        )
        ips, total = ip_service.search_ips(search_request)
        
        print(f"搜索结果: 找到 {len(ips)} 条记录")  # 调试信息
        
        return ips
    except Exception as e:
        print(f"搜索错误: {str(e)}")  # 调试信息
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索IP地址失败: {str(e)}"
        )


@router.post("/advanced-search")
async def advanced_search_ips(
    search_request: IPSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """高级搜索IP地址"""
    try:
        ip_service = IPService(db)
        result = ip_service.advanced_search_ips(search_request, current_user.id)
        return result
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"高级搜索失败: {str(e)}"
        )


@router.get("/statistics", response_model=IPStatisticsResponse)
async def get_ip_statistics(
    subnet_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取IP地址统计信息"""
    try:
        ip_service = IPService(db)
        return ip_service.get_ip_statistics(subnet_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取IP统计信息失败: {str(e)}"
        )


@router.get("/conflicts", response_model=List[IPConflictResponse])
async def get_ip_conflicts(
    subnet_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检测IP地址冲突"""
    try:
        ip_service = IPService(db)
        return ip_service.detect_ip_conflicts(subnet_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检测IP冲突失败: {str(e)}"
        )


@router.post("/range-status", response_model=List[IPRangeStatusResponse])
async def get_ip_range_status(
    request: IPRangeStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取IP地址范围状态"""
    try:
        ip_service = IPService(db)
        return ip_service.get_ip_range_status(request)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取IP范围状态失败: {str(e)}"
        )


@router.post("/bulk-operation", response_model=BulkIPOperationResponse)
async def bulk_ip_operation(
    request: BulkIPOperationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    http_request: Request = None
):
    """批量IP地址操作"""
    try:
        ip_service = IPService(db)
        audit_service = AuditService(db)
        
        # 执行批量操作
        result = ip_service.bulk_ip_operation(request, current_user.id)
        
        # 记录审计日志
        audit_service.log_operation(
            user_id=current_user.id,
            action=f"BULK_{request.operation.upper()}",
            entity_type="ip",
            entity_id=None,
            new_values={
                "operation": request.operation,
                "ip_count": len(request.ip_addresses),
                "success_count": result.success_count,
                "failed_count": result.failed_count,
                "reason": request.reason
            },
            ip_address=http_request.client.host if http_request else None,
            user_agent=http_request.headers.get("user-agent") if http_request else None
        )
        
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量操作失败: {str(e)}"
        )


@router.get("/{ip_address}/history")
async def get_ip_history(
    ip_address: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取IP地址历史记录"""
    try:
        audit_service = AuditService(db)
        
        # 首先验证IP地址是否存在
        ip_service = IPService(db)
        ip_record = ip_service.ip_repo.get_by_ip_address(ip_address)
        if not ip_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"IP地址 {ip_address} 不存在"
            )
        
        # 获取IP地址的历史记录
        history = audit_service.get_entity_history("ip", ip_record.id)
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取IP历史记录失败: {str(e)}"
        )


@router.get("/search-history", response_model=List[SearchHistoryResponse])
async def get_search_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户搜索历史"""
    try:
        from app.services.query_builder import SearchHistoryService
        
        search_history_service = SearchHistoryService(db)
        history = search_history_service.get_user_search_history(current_user.id, limit)
        
        return [
            SearchHistoryResponse(
                id=item.id,
                search_name=item.search_name,
                search_params=item.search_params,
                is_favorite=item.is_favorite,
                created_at=item.created_at,
                used_count=item.used_count
            )
            for item in history
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取搜索历史失败: {str(e)}"
        )


@router.get("/search-favorites", response_model=List[SearchHistoryResponse])
async def get_search_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户收藏的搜索"""
    try:
        from app.services.query_builder import SearchHistoryService
        
        search_history_service = SearchHistoryService(db)
        favorites = search_history_service.get_user_favorite_searches(current_user.id)
        
        return [
            SearchHistoryResponse(
                id=item.id,
                search_name=item.search_name,
                search_params=item.search_params,
                is_favorite=item.is_favorite,
                created_at=item.created_at,
                used_count=item.used_count
            )
            for item in favorites
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取收藏搜索失败: {str(e)}"
        )


@router.post("/search-history", response_model=dict)
async def save_search_history(
    request: SearchHistoryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存搜索历史"""
    try:
        from app.services.query_builder import SearchHistoryService
        
        search_history_service = SearchHistoryService(db)
        search_id = search_history_service.save_search(
            current_user.id, 
            request.search_params, 
            request.search_name
        )
        
        return {"id": search_id, "message": "搜索历史保存成功"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存搜索历史失败: {str(e)}"
        )


@router.put("/search-history/{search_id}/favorite")
async def toggle_search_favorite(
    search_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换搜索收藏状态"""
    try:
        from app.services.query_builder import SearchHistoryService
        
        search_history_service = SearchHistoryService(db)
        is_favorite = search_history_service.toggle_favorite(current_user.id, search_id)
        
        return {
            "is_favorite": is_favorite,
            "message": "收藏" if is_favorite else "取消收藏"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换收藏状态失败: {str(e)}"
        )


@router.put("/search-history/{search_id}/name")
async def update_search_name(
    search_id: int,
    search_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新搜索名称"""
    try:
        from app.services.query_builder import SearchHistoryService
        
        search_history_service = SearchHistoryService(db)
        success = search_history_service.update_search_name(current_user.id, search_id, search_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="搜索记录不存在"
            )
        
        return {"message": "搜索名称更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新搜索名称失败: {str(e)}"
        )


@router.delete("/search-history/{search_id}")
async def delete_search_history(
    search_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除搜索历史"""
    try:
        from app.services.query_builder import SearchHistoryService
        
        search_history_service = SearchHistoryService(db)
        success = search_history_service.delete_search(current_user.id, search_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="搜索记录不存在"
            )
        
        return {"message": "搜索历史删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除搜索历史失败: {str(e)}"
        )


@router.get("/departments")
async def get_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取分配部门列表"""
    try:
        ip_service = IPService(db)
        departments = ip_service.get_departments()
        return {"departments": departments}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取部门列表失败: {str(e)}"
        )