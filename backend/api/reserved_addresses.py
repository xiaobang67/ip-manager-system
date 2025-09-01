"""
地址保留管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from database.connection import get_db
from services.reserved_address_service import ReservedAddressService
from app.schemas import (
    ReservedAddressCreate, ReservedAddressUpdate, ReservedAddressResponse,
    MessageResponse
)

router = APIRouter()


@router.get("/", response_model=List[ReservedAddressResponse])
async def get_reserved_addresses(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="每页记录数"),
    network_segment_id: Optional[int] = Query(None, description="网段ID"),
    reserved_by_user_id: Optional[int] = Query(None, description="保留用户ID"),
    reserved_by_department_id: Optional[int] = Query(None, description="保留部门ID"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """获取地址保留列表"""
    service = ReservedAddressService(db)
    reservations = service.get_reserved_addresses(
        skip=skip,
        limit=limit,
        network_segment_id=network_segment_id,
        reserved_by_user_id=reserved_by_user_id,
        reserved_by_department_id=reserved_by_department_id,
        is_active=is_active,
        search=search
    )
    return reservations


@router.get("/{reservation_id}", response_model=ReservedAddressResponse)
async def get_reserved_address(reservation_id: int, db: Session = Depends(get_db)):
    """根据ID获取地址保留详情"""
    service = ReservedAddressService(db)
    reservation = service.get_reserved_address_by_id(reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="地址保留不存在")
    return reservation


@router.get("/by-ip/{ip_address}", response_model=ReservedAddressResponse)
async def get_reserved_address_by_ip(ip_address: str, db: Session = Depends(get_db)):
    """根据IP地址获取保留详情"""
    service = ReservedAddressService(db)
    reservation = service.get_reserved_address_by_ip(ip_address)
    if not reservation:
        raise HTTPException(status_code=404, detail="该IP地址没有保留记录")
    return reservation


@router.post("/", response_model=ReservedAddressResponse, status_code=201)
async def create_reserved_address(
    reservation_data: ReservedAddressCreate,
    db: Session = Depends(get_db)
):
    """创建地址保留"""
    service = ReservedAddressService(db)
    return service.create_reserved_address(reservation_data)


@router.put("/{reservation_id}", response_model=ReservedAddressResponse)
async def update_reserved_address(
    reservation_id: int,
    reservation_data: ReservedAddressUpdate,
    db: Session = Depends(get_db)
):
    """更新地址保留"""
    service = ReservedAddressService(db)
    return service.update_reserved_address(reservation_id, reservation_data)


@router.delete("/{reservation_id}", response_model=MessageResponse)
async def delete_reserved_address(reservation_id: int, db: Session = Depends(get_db)):
    """删除地址保留"""
    service = ReservedAddressService(db)
    service.delete_reserved_address(reservation_id)
    return MessageResponse(message="地址保留删除成功")


@router.post("/{reservation_id}/activate", response_model=ReservedAddressResponse)
async def activate_reservation(reservation_id: int, db: Session = Depends(get_db)):
    """激活地址保留"""
    service = ReservedAddressService(db)
    return service.activate_reservation(reservation_id)


@router.post("/{reservation_id}/deactivate", response_model=ReservedAddressResponse)
async def deactivate_reservation(reservation_id: int, db: Session = Depends(get_db)):
    """停用地址保留"""
    service = ReservedAddressService(db)
    return service.deactivate_reservation(reservation_id)


@router.get("/expired/list", response_model=List[ReservedAddressResponse])
async def get_expired_reservations(db: Session = Depends(get_db)):
    """获取已过期的地址保留"""
    service = ReservedAddressService(db)
    return service.get_expired_reservations()


@router.post("/expired/cleanup", response_model=MessageResponse)
async def cleanup_expired_reservations(db: Session = Depends(get_db)):
    """清理过期的地址保留"""
    service = ReservedAddressService(db)
    cleaned_count = service.auto_cleanup_expired_reservations()
    return MessageResponse(message=f"已清理 {cleaned_count} 个过期保留")


@router.get("/upcoming/expiration", response_model=List[ReservedAddressResponse])
async def get_upcoming_expirations(
    days: int = Query(7, ge=1, le=365, description="天数"),
    db: Session = Depends(get_db)
):
    """获取即将过期的地址保留"""
    service = ReservedAddressService(db)
    return service.get_upcoming_expirations(days)


@router.post("/{reservation_id}/extend", response_model=ReservedAddressResponse)
async def extend_reservation(
    reservation_id: int,
    new_end_date: date,
    db: Session = Depends(get_db)
):
    """延长地址保留期限"""
    service = ReservedAddressService(db)
    return service.extend_reservation(reservation_id, new_end_date)


@router.get("/statistics/overview")
async def get_reservation_statistics(db: Session = Depends(get_db)):
    """获取地址保留统计信息"""
    service = ReservedAddressService(db)
    return service.get_reservation_statistics()