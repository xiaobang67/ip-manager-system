from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.ip_repository import IPRepository
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.schemas.ip_address import IPAddressResponse, IPStatisticsResponse
from app.core.exceptions import ValidationError, NotFoundError, ConflictError
from datetime import datetime, timedelta
from app.core.timezone_config import now_beijing
import ipaddress


class IPLifecycleService:
    """IP地址生命周期管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ip_repo = IPRepository(db)

    def track_ip_lifecycle(self, ip_id: int) -> Dict[str, Any]:
        """跟踪IP地址的生命周期状态"""
        ip_record = self.ip_repo.get_by_id(ip_id)
        if not ip_record:
            raise NotFoundError(f"IP地址记录不存在: {ip_id}")
        
        lifecycle_info = {
            'ip_address': ip_record.ip_address,
            'current_status': ip_record.status,
            'created_at': ip_record.created_at,
            'updated_at': ip_record.updated_at,
            'allocated_at': ip_record.allocated_at,
            'allocated_by': ip_record.allocated_by,
            'lifecycle_stage': self._determine_lifecycle_stage(ip_record),
            'usage_duration': self._calculate_usage_duration(ip_record),
            'next_actions': self._suggest_next_actions(ip_record)
        }
        
        return lifecycle_info

    def get_ip_lifecycle_history(self, ip_address: str) -> List[Dict[str, Any]]:
        """获取IP地址的生命周期历史记录"""
        # 这里应该从审计日志中获取历史记录
        # 为了演示，我们返回当前状态的简化历史
        ip_record = self.ip_repo.get_by_ip_address(ip_address)
        if not ip_record:
            raise NotFoundError(f"IP地址不存在: {ip_address}")
        
        history = [
            {
                'timestamp': ip_record.created_at,
                'action': 'CREATED',
                'status': 'available',
                'user_id': None,
                'details': '系统自动生成'
            }
        ]
        
        if ip_record.allocated_at:
            history.append({
                'timestamp': ip_record.allocated_at,
                'action': 'ALLOCATED' if ip_record.status == IPStatus.ALLOCATED else 'RESERVED',
                'status': ip_record.status,
                'user_id': ip_record.allocated_by,
                'details': f'分配给: {ip_record.assigned_to}' if ip_record.assigned_to else '状态变更'
            })
        
        return sorted(history, key=lambda x: x['timestamp'])

    def manage_ip_expiration(self, days_threshold: int = 30) -> Dict[str, List[str]]:
        """管理IP地址过期"""
        expiration_date = now_beijing() - timedelta(days=days_threshold)
        
        # 查找长期未使用的已分配IP
        long_term_allocated = (
            self.db.query(IPAddress)
            .filter(
                IPAddress.status == IPStatus.ALLOCATED,
                IPAddress.allocated_at < expiration_date
            )
            .all()
        )
        
        # 查找长期保留的IP
        long_term_reserved = (
            self.db.query(IPAddress)
            .filter(
                IPAddress.status == IPStatus.RESERVED,
                IPAddress.allocated_at < expiration_date
            )
            .all()
        )
        
        result = {
            'long_term_allocated': [ip.ip_address for ip in long_term_allocated],
            'long_term_reserved': [ip.ip_address for ip in long_term_reserved],
            'suggestions': []
        }
        
        if long_term_allocated:
            result['suggestions'].append(f"发现 {len(long_term_allocated)} 个长期分配的IP地址，建议检查是否仍在使用")
        
        if long_term_reserved:
            result['suggestions'].append(f"发现 {len(long_term_reserved)} 个长期保留的IP地址，建议检查是否可以释放")
        
        return result

    def auto_cleanup_expired_reservations(self, days_threshold: int = 90) -> Dict[str, int]:
        """自动清理过期的保留IP地址"""
        expiration_date = now_beijing() - timedelta(days=days_threshold)
        
        # 查找过期的保留IP
        expired_reserved = (
            self.db.query(IPAddress)
            .filter(
                IPAddress.status == IPStatus.RESERVED,
                IPAddress.allocated_at < expiration_date
            )
            .all()
        )
        
        cleaned_count = 0
        for ip in expired_reserved:
            # 将过期保留的IP释放为可用状态
            ip.status = IPStatus.AVAILABLE
            ip.allocated_at = None
            ip.allocated_by = None
            ip.assigned_to = None
            ip.description = f"自动清理过期保留 - {now_beijing().strftime('%Y-%m-%d')}"
            cleaned_count += 1
        
        self.db.commit()
        
        return {
            'cleaned_count': cleaned_count,
            'threshold_days': days_threshold
        }

    def validate_ip_state_transition(self, ip_address: str, target_status: IPStatus) -> bool:
        """验证IP地址状态转换的合法性"""
        ip_record = self.ip_repo.get_by_ip_address(ip_address)
        if not ip_record:
            raise NotFoundError(f"IP地址不存在: {ip_address}")
        
        current_status = ip_record.status
        
        # 定义合法的状态转换
        valid_transitions = {
            IPStatus.AVAILABLE: [IPStatus.ALLOCATED, IPStatus.RESERVED],
            IPStatus.ALLOCATED: [IPStatus.AVAILABLE, IPStatus.RESERVED],
            IPStatus.RESERVED: [IPStatus.AVAILABLE, IPStatus.ALLOCATED],
            IPStatus.CONFLICT: [IPStatus.AVAILABLE, IPStatus.ALLOCATED, IPStatus.RESERVED]
        }
        
        return target_status in valid_transitions.get(current_status, [])

    def get_subnet_lifecycle_summary(self, subnet_id: int) -> Dict[str, Any]:
        """获取网段的IP生命周期摘要"""
        subnet = self.db.query(Subnet).filter(Subnet.id == subnet_id).first()
        if not subnet:
            raise NotFoundError(f"网段不存在: {subnet_id}")
        
        # 获取网段统计
        stats = self.ip_repo.get_ip_statistics(subnet_id)
        
        # 计算生命周期指标
        total_ips = stats['total']
        utilization_rate = (stats.get(IPStatus.ALLOCATED, 0) / total_ips * 100) if total_ips > 0 else 0
        
        # 获取最近分配的IP
        recent_allocated = (
            self.db.query(IPAddress)
            .filter(
                IPAddress.subnet_id == subnet_id,
                IPAddress.status == IPStatus.ALLOCATED,
                IPAddress.allocated_at.isnot(None)
            )
            .order_by(IPAddress.allocated_at.desc())
            .limit(5)
            .all()
        )
        
        # 获取长期未使用的IP
        thirty_days_ago = now_beijing() - timedelta(days=30)
        long_term_allocated = (
            self.db.query(IPAddress)
            .filter(
                IPAddress.subnet_id == subnet_id,
                IPAddress.status == IPStatus.ALLOCATED,
                IPAddress.allocated_at < thirty_days_ago
            )
            .count()
        )
        
        return {
            'subnet_id': subnet_id,
            'network': subnet.network,
            'total_ips': total_ips,
            'utilization_rate': round(utilization_rate, 2),
            'status_distribution': stats,
            'recent_allocations': [
                {
                    'ip_address': ip.ip_address,
                    'allocated_at': ip.allocated_at,
                    'assigned_to': ip.assigned_to
                }
                for ip in recent_allocated
            ],
            'long_term_allocated_count': long_term_allocated,
            'health_score': self._calculate_subnet_health_score(stats, utilization_rate)
        }

    def detect_ip_usage_patterns(self, subnet_id: Optional[int] = None) -> Dict[str, Any]:
        """检测IP地址使用模式"""
        query = self.db.query(IPAddress)
        if subnet_id:
            query = query.filter(IPAddress.subnet_id == subnet_id)
        
        all_ips = query.all()
        
        patterns = {
            'peak_usage_hours': [],  # 这需要更详细的日志数据
            'frequent_allocations': [],  # 频繁分配释放的IP
            'stable_allocations': [],   # 长期稳定分配的IP
            'unused_ranges': [],        # 未使用的IP范围
            'allocation_trends': {
                'daily_average': 0,
                'weekly_trend': 'stable',
                'monthly_growth': 0
            }
        }
        
        # 分析稳定分配的IP（分配超过30天且未变更）
        thirty_days_ago = now_beijing() - timedelta(days=30)
        stable_ips = [
            ip for ip in all_ips
            if ip.status == IPStatus.ALLOCATED 
            and ip.allocated_at 
            and ip.allocated_at < thirty_days_ago
        ]
        
        patterns['stable_allocations'] = [
            {
                'ip_address': ip.ip_address,
                'allocated_at': ip.allocated_at,
                'assigned_to': ip.assigned_to,
                'duration_days': (now_beijing() - ip.allocated_at).days
            }
            for ip in stable_ips[:10]  # 取前10个
        ]
        
        # 分析未使用的IP范围
        if subnet_id:
            subnet = self.db.query(Subnet).filter(Subnet.id == subnet_id).first()
            if subnet:
                patterns['unused_ranges'] = self._find_unused_ip_ranges(subnet.network, all_ips)
        
        return patterns

    def _determine_lifecycle_stage(self, ip_record: IPAddress) -> str:
        """确定IP地址的生命周期阶段"""
        if ip_record.status == IPStatus.AVAILABLE:
            return 'available'
        elif ip_record.status == IPStatus.CONFLICT:
            return 'conflict'
        elif ip_record.allocated_at:
            days_allocated = (now_beijing() - ip_record.allocated_at).days
            if days_allocated < 7:
                return 'newly_allocated'
            elif days_allocated < 30:
                return 'short_term'
            elif days_allocated < 90:
                return 'medium_term'
            else:
                return 'long_term'
        else:
            return 'unknown'

    def _calculate_usage_duration(self, ip_record: IPAddress) -> Optional[int]:
        """计算IP地址的使用时长（天数）"""
        if ip_record.allocated_at:
            return (now_beijing() - ip_record.allocated_at).days
        return None

    def _suggest_next_actions(self, ip_record: IPAddress) -> List[str]:
        """建议下一步操作"""
        suggestions = []
        
        if ip_record.status == IPStatus.CONFLICT:
            suggestions.append("解决IP地址冲突")
        elif ip_record.status == IPStatus.AVAILABLE:
            suggestions.append("可以分配给新设备")
        elif ip_record.status in [IPStatus.ALLOCATED, IPStatus.RESERVED]:
            if ip_record.allocated_at:
                days_allocated = (now_beijing() - ip_record.allocated_at).days
                if days_allocated > 90:
                    suggestions.append("检查是否仍在使用，考虑释放")
                elif days_allocated > 30:
                    suggestions.append("验证使用状态")
        
        return suggestions

    def _calculate_subnet_health_score(self, stats: Dict[str, int], utilization_rate: float) -> int:
        """计算网段健康评分（0-100）"""
        score = 100
        
        # 利用率过高或过低都会降低评分
        if utilization_rate > 90:
            score -= 20  # 利用率过高
        elif utilization_rate < 10:
            score -= 10  # 利用率过低
        
        # 冲突IP会降低评分
        conflict_count = stats.get(IPStatus.CONFLICT, 0)
        if conflict_count > 0:
            score -= min(30, conflict_count * 5)
        
        # 保留IP过多会降低评分
        reserved_count = stats.get(IPStatus.RESERVED, 0)
        total_count = stats.get('total', 1)
        reserved_rate = reserved_count / total_count * 100
        if reserved_rate > 20:
            score -= 10
        
        return max(0, score)

    def _find_unused_ip_ranges(self, network: str, ip_records: List[IPAddress]) -> List[Dict[str, str]]:
        """查找未使用的IP地址范围"""
        try:
            net = ipaddress.ip_network(network, strict=False)
        except ValueError:
            return []
        
        # 获取所有已管理的IP地址
        managed_ips = {ipaddress.ip_address(ip.ip_address) for ip in ip_records}
        
        # 查找连续的未使用IP范围
        unused_ranges = []
        range_start = None
        
        for ip in net.hosts():
            if ip not in managed_ips:
                if range_start is None:
                    range_start = ip
            else:
                if range_start is not None:
                    # 结束当前范围
                    range_end = ip - 1
                    if range_start <= range_end:
                        unused_ranges.append({
                            'start_ip': str(range_start),
                            'end_ip': str(range_end),
                            'count': int(range_end) - int(range_start) + 1
                        })
                    range_start = None
        
        # 处理最后一个范围
        if range_start is not None:
            last_ip = list(net.hosts())[-1]
            unused_ranges.append({
                'start_ip': str(range_start),
                'end_ip': str(last_ip),
                'count': int(last_ip) - int(range_start) + 1
            })
        
        return unused_ranges[:5]  # 返回前5个范围