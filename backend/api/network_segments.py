"""
网段管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.connection import get_db
from services.network_segment_service import NetworkSegmentService
from app.schemas import (
    NetworkSegmentCreate, NetworkSegmentUpdate, NetworkSegmentResponse,
    MessageResponse, NetworkSegmentStats, PaginatedResponse
)

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[NetworkSegmentResponse])
async def get_network_segments(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="每页记录数"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """获取网段列表"""
    service = NetworkSegmentService(db)
    segments = service.get_network_segments(
        skip=skip, 
        limit=limit, 
        is_active=is_active,
        search=search
    )
    total = service.get_network_segments_count(
        is_active=is_active,
        search=search
    )
    
    # 计算分页信息
    page = (skip // limit) + 1
    pages = (total + limit - 1) // limit
    
    return PaginatedResponse(
        items=segments,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.get("/{segment_id}", response_model=NetworkSegmentResponse)
async def get_network_segment(segment_id: int, db: Session = Depends(get_db)):
    """根据ID获取网段详情"""
    service = NetworkSegmentService(db)
    segment = service.get_network_segment_by_id(segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="网段不存在")
    return segment


@router.post("/", response_model=NetworkSegmentResponse, status_code=201)
async def create_network_segment(
    segment_data: NetworkSegmentCreate,
    db: Session = Depends(get_db)
):
    """创建网段"""
    service = NetworkSegmentService(db)
    return service.create_network_segment(segment_data)


@router.put("/{segment_id}", response_model=NetworkSegmentResponse)
async def update_network_segment(
    segment_id: int,
    segment_data: NetworkSegmentUpdate,
    db: Session = Depends(get_db)
):
    """更新网段"""
    service = NetworkSegmentService(db)
    return service.update_network_segment(segment_id, segment_data)


@router.delete("/{segment_id}", response_model=MessageResponse)
async def delete_network_segment(segment_id: int, db: Session = Depends(get_db)):
    """删除网段"""
    service = NetworkSegmentService(db)
    service.delete_network_segment(segment_id)
    return MessageResponse(message="网段删除成功")


@router.get("/{segment_id}/statistics", response_model=NetworkSegmentStats)
async def get_network_segment_statistics(segment_id: int, db: Session = Depends(get_db)):
    """获取网段统计信息"""
    service = NetworkSegmentService(db)
    return service.get_network_segment_statistics(segment_id)


@router.get("/{segment_id}/available-ips")
async def get_available_ip_range(
    segment_id: int,
    count: int = Query(10, ge=1, le=100, description="返回IP数量"),
    db: Session = Depends(get_db)
):
    """获取网段中可用的IP地址"""
    service = NetworkSegmentService(db)
    available_ips = service.get_available_ip_range(segment_id, count)
    return {"available_ips": available_ips}