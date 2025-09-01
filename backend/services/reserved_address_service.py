"""
地址保留管理服务
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models import ReservedAddress, NetworkSegment, User, Department, IPAddress
from app.schemas import ReservedAddressCreate, ReservedAddressUpdate, PriorityEnum
from fastapi import HTTPException
from datetime import datetime, date
import ipaddress


class ReservedAddressService:
    """地址保留管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_reserved_addresses(self, skip: int = 0, limit: int = 100,
                             network_segment_id: Optional[int] = None,
                             reserved_by_user_id: Optional[int] = None,
                             reserved_by_department_id: Optional[int] = None,
                             is_active: Optional[bool] = None,
                             search: Optional[str] = None) -> List[ReservedAddress]:
        """获取地址保留列表"""
        query = self.db.query(ReservedAddress)
        
        # 按网段筛选
        if network_segment_id:
            query = query.filter(ReservedAddress.network_segment_id == network_segment_id)
        
        # 按保留用户筛选
        if reserved_by_user_id:
            query = query.filter(ReservedAddress.reserved_by_user_id == reserved_by_user_id)
        
        # 按保留部门筛选
        if reserved_by_department_id:
            query = query.filter(ReservedAddress.reserved_by_department_id == reserved_by_department_id)
        
        # 按激活状态筛选
        if is_active is not None:
            query = query.filter(ReservedAddress.is_active == is_active)
        
        # 搜索功能
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    ReservedAddress.ip_address.like(search_pattern),
                    ReservedAddress.reserved_for.like(search_pattern),
                    ReservedAddress.notes.like(search_pattern)
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    def get_reserved_address_by_id(self, reservation_id: int) -> Optional[ReservedAddress]:
        """根据ID获取地址保留"""
        return self.db.query(ReservedAddress).filter(ReservedAddress.id == reservation_id).first()
    
    def get_reserved_address_by_ip(self, ip_address: str) -> Optional[ReservedAddress]:
        """根据IP地址获取保留记录"""
        return self.db.query(ReservedAddress).filter(
            and_(
                ReservedAddress.ip_address == ip_address,
                ReservedAddress.is_active == True
            )
        ).first()
    
    def create_reserved_address(self, reservation_data: ReservedAddressCreate) -> ReservedAddress:
        """创建地址保留"""
        try:
            # 验证IP地址格式
            try:
                ipaddress.ip_address(reservation_data.ip_address)
            except ValueError:
                raise HTTPException(status_code=400, detail="IP地址格式不正确")
            
            # 检查网段是否存在
            segment = self.db.query(NetworkSegment).filter(NetworkSegment.id == reservation_data.network_segment_id).first()
            if not segment:
                raise HTTPException(status_code=400, detail="网段不存在")
            
            # 验证IP地址是否在指定网段范围内
            if not self._is_ip_in_segment(reservation_data.ip_address, segment):
                raise HTTPException(status_code=400, detail="IP地址不在指定网段范围内")
            
            # 检查IP地址是否已被保留
            existing_reservation = self.get_reserved_address_by_ip(reservation_data.ip_address)
            if existing_reservation:
                raise HTTPException(status_code=400, detail="IP地址已被保留")
            
            # 检查IP地址是否已被分配
            ip_record = self.db.query(IPAddress).filter(IPAddress.ip_address == reservation_data.ip_address).first()
            if ip_record and ip_record.status == 'allocated':
                raise HTTPException(status_code=400, detail="IP地址已被分配，无法保留")
            
            # 检查保留用户是否存在
            user = self.db.query(User).filter(User.id == reservation_data.reserved_by_user_id).first()
            if not user:
                raise HTTPException(status_code=400, detail="保留用户不存在")
            
            # 检查保留部门是否存在
            if reservation_data.reserved_by_department_id:
                dept = self.db.query(Department).filter(Department.id == reservation_data.reserved_by_department_id).first()
                if not dept:
                    raise HTTPException(status_code=400, detail="保留部门不存在")
            
            # 验证日期
            if reservation_data.end_date and reservation_data.start_date >= reservation_data.end_date:
                raise HTTPException(status_code=400, detail="结束日期必须晚于开始日期")
            
            # 创建保留记录
            db_reservation = ReservedAddress(**reservation_data.model_dump())
            self.db.add(db_reservation)
            
            # 更新IP地址状态为保留
            if ip_record:
                ip_record.status = 'reserved'
            else:
                # 如果IP记录不存在，创建一个
                new_ip = IPAddress(
                    ip_address=reservation_data.ip_address,
                    network_segment_id=reservation_data.network_segment_id,
                    status='reserved'
                )
                self.db.add(new_ip)
            
            self.db.commit()
            self.db.refresh(db_reservation)
            
            return db_reservation
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"创建地址保留失败: {str(e)}")
    
    def update_reserved_address(self, reservation_id: int, reservation_data: ReservedAddressUpdate) -> ReservedAddress:
        """更新地址保留"""
        db_reservation = self.get_reserved_address_by_id(reservation_id)
        if not db_reservation:
            raise HTTPException(status_code=404, detail="地址保留不存在")
        
        # 检查保留部门
        if reservation_data.reserved_by_department_id:
            dept = self.db.query(Department).filter(Department.id == reservation_data.reserved_by_department_id).first()
            if not dept:
                raise HTTPException(status_code=400, detail="保留部门不存在")
        
        # 验证日期
        start_date = reservation_data.start_date or db_reservation.start_date
        end_date = reservation_data.end_date or db_reservation.end_date
        
        if end_date and start_date >= end_date:
            raise HTTPException(status_code=400, detail="结束日期必须晚于开始日期")
        
        # 更新字段
        update_data = reservation_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_reservation, field, value)
        
        self.db.commit()
        self.db.refresh(db_reservation)
        
        return db_reservation
    
    def delete_reserved_address(self, reservation_id: int) -> bool:
        """删除地址保留"""
        db_reservation = self.get_reserved_address_by_id(reservation_id)
        if not db_reservation:
            raise HTTPException(status_code=404, detail="地址保留不存在")
        
        # 更新相关IP地址状态
        ip_record = self.db.query(IPAddress).filter(IPAddress.ip_address == db_reservation.ip_address).first()
        if ip_record and ip_record.status == 'reserved':
            ip_record.status = 'available'
        
        # 删除保留记录
        self.db.delete(db_reservation)
        self.db.commit()
        
        return True
    
    def activate_reservation(self, reservation_id: int) -> ReservedAddress:
        """激活地址保留"""
        db_reservation = self.get_reserved_address_by_id(reservation_id)
        if not db_reservation:
            raise HTTPException(status_code=404, detail="地址保留不存在")
        
        # 检查IP地址是否已被分配
        ip_record = self.db.query(IPAddress).filter(IPAddress.ip_address == db_reservation.ip_address).first()
        if ip_record and ip_record.status == 'allocated':
            raise HTTPException(status_code=400, detail="IP地址已被分配，无法激活保留")
        
        # 激活保留
        db_reservation.is_active = True
        
        # 更新IP状态
        if ip_record:
            ip_record.status = 'reserved'
        
        self.db.commit()
        self.db.refresh(db_reservation)
        
        return db_reservation
    
    def deactivate_reservation(self, reservation_id: int) -> ReservedAddress:
        """停用地址保留"""
        db_reservation = self.get_reserved_address_by_id(reservation_id)
        if not db_reservation:
            raise HTTPException(status_code=404, detail="地址保留不存在")
        
        # 停用保留
        db_reservation.is_active = False
        
        # 更新IP状态为可用
        ip_record = self.db.query(IPAddress).filter(IPAddress.ip_address == db_reservation.ip_address).first()
        if ip_record and ip_record.status == 'reserved':
            ip_record.status = 'available'
        
        self.db.commit()
        self.db.refresh(db_reservation)
        
        return db_reservation
    
    def get_expired_reservations(self) -> List[ReservedAddress]:
        """获取已过期的地址保留"""
        today = date.today()
        return self.db.query(ReservedAddress).filter(
            and_(
                ReservedAddress.is_active == True,
                ReservedAddress.is_permanent == False,
                ReservedAddress.end_date < today
            )
        ).all()
    
    def auto_cleanup_expired_reservations(self) -> int:
        """自动清理过期的地址保留"""
        expired_reservations = self.get_expired_reservations()
        cleaned_count = 0
        
        for reservation in expired_reservations:
            try:
                self.deactivate_reservation(reservation.id)
                cleaned_count += 1
            except Exception as e:
                print(f"清理过期保留失败 (ID: {reservation.id}): {str(e)}")
        
        return cleaned_count
    
    def get_upcoming_expirations(self, days: int = 7) -> List[ReservedAddress]:
        """获取即将过期的地址保留"""
        from datetime import timedelta
        future_date = date.today() + timedelta(days=days)
        
        return self.db.query(ReservedAddress).filter(
            and_(
                ReservedAddress.is_active == True,
                ReservedAddress.is_permanent == False,
                ReservedAddress.end_date <= future_date,
                ReservedAddress.end_date >= date.today()
            )
        ).all()
    
    def extend_reservation(self, reservation_id: int, new_end_date: date) -> ReservedAddress:
        """延长地址保留期限"""
        db_reservation = self.get_reserved_address_by_id(reservation_id)
        if not db_reservation:
            raise HTTPException(status_code=404, detail="地址保留不存在")
        
        if new_end_date <= db_reservation.start_date:
            raise HTTPException(status_code=400, detail="新的结束日期必须晚于开始日期")
        
        if db_reservation.end_date and new_end_date <= db_reservation.end_date:
            raise HTTPException(status_code=400, detail="新的结束日期必须晚于当前结束日期")
        
        db_reservation.end_date = new_end_date
        self.db.commit()
        self.db.refresh(db_reservation)
        
        return db_reservation
    
    def get_reservation_statistics(self) -> dict:
        """获取地址保留统计信息"""
        # 总保留数
        total = self.db.query(ReservedAddress).count()
        
        # 活跃保留数
        active = self.db.query(ReservedAddress).filter(ReservedAddress.is_active == True).count()
        
        # 永久保留数
        permanent = self.db.query(ReservedAddress).filter(
            and_(ReservedAddress.is_active == True, ReservedAddress.is_permanent == True)
        ).count()
        
        # 即将过期数（7天内）
        upcoming_expired = len(self.get_upcoming_expirations(7))
        
        # 已过期数
        expired = len(self.get_expired_reservations())
        
        # 按优先级统计
        priority_stats = self.db.query(
            ReservedAddress.priority, 
            self.db.func.count(ReservedAddress.id)
        ).filter(ReservedAddress.is_active == True).group_by(ReservedAddress.priority).all()
        
        priority_dict = {priority: count for priority, count in priority_stats}
        
        return {
            'total': total,
            'active': active,
            'permanent': permanent,
            'upcoming_expired': upcoming_expired,
            'expired': expired,
            'priority_stats': priority_dict
        }
    
    def _is_ip_in_segment(self, ip_address: str, segment: NetworkSegment) -> bool:
        """检查IP地址是否在网段范围内"""
        try:
            ip = ipaddress.ip_address(ip_address)
            start_ip = ipaddress.ip_address(segment.start_ip)
            end_ip = ipaddress.ip_address(segment.end_ip)
            return start_ip <= ip <= end_ip
        except ValueError:
            return False