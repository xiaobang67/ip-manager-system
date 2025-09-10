from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import io

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.services.audit_service import AuditService
from app.schemas.audit_log import (
    AuditLogSearchRequest,
    AuditLogSearchResponse,
    AuditLogResponse,
    EntityHistoryResponse,
    UserActivityResponse,
    AuditLogExportRequest,
    AuditLogStatsResponse,
    ActionType,
    EntityType
)

router = APIRouter()


@router.post("/search", response_model=AuditLogSearchResponse)
async def search_audit_logs(
    search_request: AuditLogSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """搜索审计日志"""
    audit_service = AuditService(db)
    
    logs, total = audit_service.search_audit_logs_with_count(
        user_id=search_request.user_id,
        entity_type=search_request.entity_type,
        action=search_request.action,
        entity_id=search_request.entity_id,
        start_date=search_request.start_date,
        end_date=search_request.end_date,
        skip=search_request.skip,
        limit=search_request.limit
    )
    
    return AuditLogSearchResponse(
        items=[AuditLogResponse(**log) for log in logs],
        total=total,
        skip=search_request.skip,
        limit=search_request.limit
    )


@router.get("/", response_model=List[AuditLogResponse])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    user_id: Optional[int] = Query(None),
    entity_type: Optional[EntityType] = Query(None),
    action: Optional[ActionType] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取审计日志列表"""
    audit_service = AuditService(db)
    
    logs = audit_service.search_audit_logs(
        user_id=user_id,
        entity_type=entity_type,
        action=action,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    
    return [AuditLogResponse(**log) for log in logs]


@router.get("/entity/{entity_type}/{entity_id}/history", response_model=EntityHistoryResponse)
async def get_entity_history(
    entity_type: EntityType,
    entity_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取实体的历史记录"""
    audit_service = AuditService(db)
    
    history = audit_service.get_entity_history(
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit
    )
    
    return EntityHistoryResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        history=[AuditLogResponse(**log) for log in history]
    )


@router.get("/user/{user_id}/activity", response_model=UserActivityResponse)
async def get_user_activity(
    user_id: int,
    entity_type: Optional[EntityType] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户活动记录"""
    audit_service = AuditService(db)
    
    # 检查权限：只有管理员或用户本人可以查看活动记录
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="没有权限查看其他用户的活动记录"
        )
    
    activities = audit_service.get_user_activity(
        user_id=user_id,
        entity_type=entity_type,
        limit=limit
    )
    
    # 获取用户信息
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    username = user.username if user else f"User_{user_id}"
    
    return UserActivityResponse(
        user_id=user_id,
        username=username,
        activities=[AuditLogResponse(**activity) for activity in activities]
    )


@router.get("/recent", response_model=List[AuditLogResponse])
async def get_recent_activities(
    limit: int = Query(50, ge=1, le=200),
    entity_type: Optional[EntityType] = Query(None),
    action: Optional[ActionType] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取最近的活动记录"""
    audit_service = AuditService(db)
    
    activities = audit_service.get_recent_activities(
        entity_type=entity_type,
        action=action,
        limit=limit
    )
    
    return [AuditLogResponse(**activity) for activity in activities]


@router.get("/statistics", response_model=AuditLogStatsResponse)
async def get_audit_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取审计日志统计信息"""
    # 只有管理员可以查看统计信息
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="只有管理员可以查看审计统计信息"
        )
    
    audit_service = AuditService(db)
    stats = audit_service.get_audit_statistics()
    
    return AuditLogStatsResponse(
        total_logs=stats["total_logs"],
        actions_count=stats["actions_count"],
        entities_count=stats["entities_count"],
        users_count=stats["users_count"],
        recent_activities=[AuditLogResponse(**activity) for activity in stats["recent_activities"]]
    )


@router.post("/export")
async def export_audit_logs(
    export_request: AuditLogExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出审计日志"""
    # 只有管理员可以导出审计日志
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="只有管理员可以导出审计日志"
        )
    
    audit_service = AuditService(db)
    
    try:
        data = audit_service.export_audit_logs(
            format_type=export_request.format,
            user_id=export_request.user_id,
            entity_type=export_request.entity_type,
            action=export_request.action,
            start_date=export_request.start_date,
            end_date=export_request.end_date
        )
        
        # 设置响应头
        if export_request.format.lower() == "csv":
            media_type = "text/csv"
            filename = "audit_logs.csv"
        elif export_request.format.lower() == "excel":
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = "audit_logs.xlsx"
        elif export_request.format.lower() == "json":
            media_type = "application/json"
            filename = "audit_logs.json"
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
        
        return StreamingResponse(
            io.BytesIO(data),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.delete("/archive")
async def archive_old_logs(
    days_to_keep: int = Query(365, ge=30, le=3650),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """归档旧的审计日志"""
    # 只有超级管理员可以归档日志
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="只有管理员可以归档审计日志"
        )
    
    audit_service = AuditService(db)
    
    try:
        archived_count = audit_service.archive_old_logs(days_to_keep)
        return {
            "message": f"成功归档 {archived_count} 条审计日志",
            "archived_count": archived_count,
            "days_kept": days_to_keep
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"归档失败: {str(e)}")


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个审计日志详情"""
    audit_service = AuditService(db)
    
    # 直接查询数据库获取单个日志
    from app.models.audit_log import AuditLog
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="审计日志不存在")
    
    # 获取用户信息
    user = db.query(User).filter(User.id == log.user_id).first()
    username = user.username if user else "Unknown"
    
    log_data = {
        "id": log.id,
        "action": log.action,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "user_id": log.user_id,
        "username": username,
        "old_values": log.old_values,
        "new_values": log.new_values,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "created_at": log.created_at
    }
    
    return AuditLogResponse(**log_data)