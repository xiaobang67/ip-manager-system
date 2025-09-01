"""
网段管理服务
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models import NetworkSegment, Department, User, IPAddress
from app.schemas import NetworkSegmentCreate, NetworkSegmentUpdate
from fastapi import HTTPException
import ipaddress


class NetworkSegmentService:
    """网段管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_network_segments(self, skip: int = 0, limit: int = 100,
                           is_active: Optional[bool] = None,
                           search: Optional[str] = None) -> List[NetworkSegment]:
        """获取网段列表"""
        query = self.db.query(NetworkSegment)
        
        # 按激活状态筛选，默认只显示活跃的网段
        if is_active is None:
            query = query.filter(NetworkSegment.is_active == True)
        elif is_active is not None:
            query = query.filter(NetworkSegment.is_active == is_active)
        
        # 搜索功能
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    NetworkSegment.name.like(search_pattern),
                    NetworkSegment.network.like(search_pattern),
                    NetworkSegment.purpose.like(search_pattern),
                    NetworkSegment.location.like(search_pattern)
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    def get_network_segments_count(self, is_active: Optional[bool] = None,
                                  search: Optional[str] = None) -> int:
        """获取网段总数"""
        query = self.db.query(NetworkSegment)
        
        # 按激活状态筛选，默认只统计活跃的网段
        if is_active is None:
            query = query.filter(NetworkSegment.is_active == True)
        elif is_active is not None:
            query = query.filter(NetworkSegment.is_active == is_active)
        
        # 搜索功能
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    NetworkSegment.name.like(search_pattern),
                    NetworkSegment.network.like(search_pattern),
                    NetworkSegment.purpose.like(search_pattern),
                    NetworkSegment.location.like(search_pattern)
                )
            )
        
        return query.count()
    
    def get_network_segment_by_id(self, segment_id: int) -> Optional[NetworkSegment]:
        """根据ID获取网段"""
        return self.db.query(NetworkSegment).filter(NetworkSegment.id == segment_id).first()
    
    def create_network_segment(self, segment_data: NetworkSegmentCreate) -> NetworkSegment:
        """创建网段"""
        try:
            # 验证IP地址格式
            self._validate_ip_addresses(segment_data)
            
            # 检查网段是否重叠
            if self._check_network_overlap(segment_data.start_ip, segment_data.end_ip):
                raise HTTPException(status_code=400, detail="网段与现有网段重叠")
            
            # 检查负责部门是否存在
            if segment_data.responsible_department_id:
                dept = self.db.query(Department).filter(Department.id == segment_data.responsible_department_id).first()
                if not dept:
                    raise HTTPException(status_code=400, detail="负责部门不存在")
            
            # 检查负责人是否存在
            if segment_data.responsible_user_id:
                user = self.db.query(User).filter(User.id == segment_data.responsible_user_id).first()
                if not user:
                    raise HTTPException(status_code=400, detail="负责人不存在")
            
            # 创建网段
            db_segment = NetworkSegment(**segment_data.model_dump())
            self.db.add(db_segment)
            self.db.commit()
            self.db.refresh(db_segment)
            
            # 自动生成IP地址记录（异步处理，不影响网段创建成功响应）
            try:
                self._generate_ip_addresses(db_segment)
            except Exception as e:
                # IP地址生成失败不应该影响网段创建的成功
                print(f"警告：IP地址生成失败，但网段创建成功: {str(e)}")
            
            # 重新刷新对象以确保关联数据正确加载
            self.db.refresh(db_segment)
            
            return db_segment
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"创建网段失败: {str(e)}")
    
    def update_network_segment(self, segment_id: int, segment_data: NetworkSegmentUpdate) -> NetworkSegment:
        """更新网段"""
        db_segment = self.get_network_segment_by_id(segment_id)
        if not db_segment:
            raise HTTPException(status_code=404, detail="网段不存在")
        
        # 如果修改了IP范围，需要验证
        if segment_data.start_ip or segment_data.end_ip:
            start_ip = segment_data.start_ip or db_segment.start_ip
            end_ip = segment_data.end_ip or db_segment.end_ip
            
            # 验证IP地址格式
            try:
                ipaddress.ip_address(start_ip)
                ipaddress.ip_address(end_ip)
            except ValueError:
                raise HTTPException(status_code=400, detail="IP地址格式不正确")
            
            # 检查是否与其他网段重叠（排除自己）
            if self._check_network_overlap(start_ip, end_ip, exclude_id=segment_id):
                raise HTTPException(status_code=400, detail="网段与现有网段重叠")
        
        # 检查负责部门
        if segment_data.responsible_department_id:
            dept = self.db.query(Department).filter(Department.id == segment_data.responsible_department_id).first()
            if not dept:
                raise HTTPException(status_code=400, detail="负责部门不存在")
        
        # 检查负责人
        if segment_data.responsible_user_id:
            user = self.db.query(User).filter(User.id == segment_data.responsible_user_id).first()
            if not user:
                raise HTTPException(status_code=400, detail="负责人不存在")
        
        # 更新字段
        update_data = segment_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_segment, field, value)
        
        self.db.commit()
        self.db.refresh(db_segment)
        
        return db_segment
    
    def delete_network_segment(self, segment_id: int) -> bool:
        """删除网段"""
        db_segment = self.get_network_segment_by_id(segment_id)
        if not db_segment:
            raise HTTPException(status_code=404, detail="网段不存在")
        
        # 检查是否有已分配的IP地址
        allocated_ips = self.db.query(IPAddress).filter(
            and_(
                IPAddress.network_segment_id == segment_id,
                IPAddress.status == 'allocated'
            )
        ).count()
        
        if allocated_ips > 0:
            raise HTTPException(status_code=400, detail="网段中存在已分配的IP地址，无法删除")
        
        # 软删除
        db_segment.is_active = False
        self.db.commit()
        
        return True
    
    def get_network_segment_statistics(self, segment_id: int) -> dict:
        """获取网段统计信息"""
        segment = self.get_network_segment_by_id(segment_id)
        if not segment:
            raise HTTPException(status_code=404, detail="网段不存在")
        
        # 统计IP地址状态
        ip_stats = self.db.query(IPAddress.status, self.db.func.count(IPAddress.id)).filter(
            IPAddress.network_segment_id == segment_id
        ).group_by(IPAddress.status).all()
        
        stats = {
            'total_ips': 0,
            'available_ips': 0,
            'allocated_ips': 0,
            'reserved_ips': 0,
            'blacklisted_ips': 0,
            'utilization_rate': 0.0
        }
        
        for status, count in ip_stats:
            stats['total_ips'] += count
            if status == 'available':
                stats['available_ips'] = count
            elif status == 'allocated':
                stats['allocated_ips'] = count
            elif status == 'reserved':
                stats['reserved_ips'] = count
            elif status == 'blacklisted':
                stats['blacklisted_ips'] = count
        
        # 计算利用率
        if stats['total_ips'] > 0:
            used_ips = stats['allocated_ips'] + stats['reserved_ips']
            stats['utilization_rate'] = round((used_ips / stats['total_ips']) * 100, 2)
        
        return stats
    
    def _validate_ip_addresses(self, segment_data: NetworkSegmentCreate):
        """验证IP地址格式和范围"""
        try:
            start_ip = ipaddress.ip_address(segment_data.start_ip)
            end_ip = ipaddress.ip_address(segment_data.end_ip)
            
            if start_ip >= end_ip:
                raise HTTPException(status_code=400, detail="起始IP地址必须小于结束IP地址")
            
            # 验证网关地址
            if segment_data.gateway:
                gateway_ip = ipaddress.ip_address(segment_data.gateway)
                if not (start_ip <= gateway_ip <= end_ip):
                    raise HTTPException(status_code=400, detail="网关地址必须在网段范围内")
                    
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"IP地址格式不正确: {str(e)}")
    
    def _check_network_overlap(self, start_ip: str, end_ip: str, exclude_id: Optional[int] = None) -> bool:
        """检查网段是否与现有网段重叠"""
        query = self.db.query(NetworkSegment).filter(NetworkSegment.is_active == True)
        
        if exclude_id:
            query = query.filter(NetworkSegment.id != exclude_id)
        
        existing_segments = query.all()
        
        new_start = ipaddress.ip_address(start_ip)
        new_end = ipaddress.ip_address(end_ip)
        
        for segment in existing_segments:
            existing_start = ipaddress.ip_address(segment.start_ip)
            existing_end = ipaddress.ip_address(segment.end_ip)
            
            # 检查是否重叠
            if not (new_end < existing_start or new_start > existing_end):
                return True
        
        return False
    
    def _generate_ip_addresses(self, segment: NetworkSegment):
        """为网段生成IP地址记录"""
        try:
            start_ip = ipaddress.ip_address(segment.start_ip)
            end_ip = ipaddress.ip_address(segment.end_ip)
            
            # 计算IP地址数量，如果超过1000个，只生成关键IP
            ip_count = int(end_ip) - int(start_ip) + 1
            
            if ip_count > 1000:
                # 只生成前10个和后10个IP
                ips_to_generate = []
                for i in range(10):
                    ips_to_generate.append(start_ip + i)
                for i in range(10):
                    ips_to_generate.append(end_ip - i)
            else:
                # 生成所有IP
                ips_to_generate = [start_ip + i for i in range(ip_count)]
            
            # 检查现有IP地址，避免重复
            existing_ips = set()
            existing_ip_records = self.db.query(IPAddress.ip_address).filter(
                IPAddress.network_segment_id == segment.id
            ).all()
            for record in existing_ip_records:
                existing_ips.add(record.ip_address)
            
            # 批量插入IP地址记录，跳过已存在的IP
            ip_records = []
            for ip in ips_to_generate:
                ip_str = str(ip)
                if ip_str not in existing_ips:
                    ip_record = IPAddress(
                        ip_address=ip_str,
                        network_segment_id=segment.id,
                        status='available'
                    )
                    ip_records.append(ip_record)
            
            if ip_records:
                # 使用新的数据库会话来插入IP地址，不影响主事务
                from sqlalchemy.orm import sessionmaker
                Session = sessionmaker(bind=self.db.bind)
                new_session = Session()
                try:
                    new_session.bulk_save_objects(ip_records)
                    new_session.commit()
                    print(f"成功为网段 {segment.name} 生成了 {len(ip_records)} 个IP地址")
                except Exception as inner_e:
                    new_session.rollback()
                    print(f"为网段 {segment.name} 生成IP地址时出错: {str(inner_e)}")
                finally:
                    new_session.close()
            
        except Exception as e:
            # 即使IP生成失败，也不影响网段创建
            print(f"生成IP地址记录失败: {str(e)}")
            # 回滚IP生成相关的更改，但保留网段创建
            try:
                self.db.rollback()
            except:
                pass
    
    def get_available_ip_range(self, segment_id: int, count: int = 1) -> List[str]:
        """获取网段中可用的IP地址"""
        segment = self.get_network_segment_by_id(segment_id)
        if not segment:
            raise HTTPException(status_code=404, detail="网段不存在")
        
        available_ips = self.db.query(IPAddress).filter(
            and_(
                IPAddress.network_segment_id == segment_id,
                IPAddress.status == 'available'
            )
        ).limit(count).all()
        
        return [ip.ip_address for ip in available_ips]