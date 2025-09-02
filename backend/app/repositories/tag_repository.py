from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.tag import Tag
from app.models.ip_address import IPAddress
from app.models.subnet import Subnet
from app.schemas.tag import TagCreate, TagUpdate


class TagRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_tag(self, tag_data: TagCreate) -> Tag:
        """创建标签"""
        db_tag = Tag(**tag_data.dict())
        self.db.add(db_tag)
        self.db.commit()
        self.db.refresh(db_tag)
        return db_tag

    def get_tag_by_id(self, tag_id: int) -> Optional[Tag]:
        """根据ID获取标签"""
        return self.db.query(Tag).filter(Tag.id == tag_id).first()

    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """根据名称获取标签"""
        return self.db.query(Tag).filter(Tag.name == name).first()

    def get_all_tags(self, skip: int = 0, limit: int = 100) -> List[Tag]:
        """获取所有标签"""
        return self.db.query(Tag).offset(skip).limit(limit).all()

    def search_tags(self, query: str) -> List[Tag]:
        """搜索标签"""
        return self.db.query(Tag).filter(Tag.name.ilike(f"%{query}%")).all()

    def update_tag(self, tag_id: int, tag_data: TagUpdate) -> Optional[Tag]:
        """更新标签"""
        db_tag = self.get_tag_by_id(tag_id)
        if not db_tag:
            return None
        
        update_data = tag_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_tag, key, value)
        
        self.db.commit()
        self.db.refresh(db_tag)
        return db_tag

    def delete_tag(self, tag_id: int) -> bool:
        """删除标签"""
        db_tag = self.get_tag_by_id(tag_id)
        if not db_tag:
            return False
        
        self.db.delete(db_tag)
        self.db.commit()
        return True

    def assign_tags_to_ip(self, ip_id: int, tag_ids: List[int]) -> bool:
        """为IP地址分配标签"""
        ip_address = self.db.query(IPAddress).filter(IPAddress.id == ip_id).first()
        if not ip_address:
            return False
        
        # 获取标签对象
        tags = self.db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        if len(tags) != len(tag_ids):
            return False  # 某些标签不存在
        
        # 清除现有标签并设置新标签
        ip_address.tags.clear()
        ip_address.tags.extend(tags)
        
        self.db.commit()
        return True

    def assign_tags_to_subnet(self, subnet_id: int, tag_ids: List[int]) -> bool:
        """为网段分配标签"""
        subnet = self.db.query(Subnet).filter(Subnet.id == subnet_id).first()
        if not subnet:
            return False
        
        # 获取标签对象
        tags = self.db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        if len(tags) != len(tag_ids):
            return False  # 某些标签不存在
        
        # 清除现有标签并设置新标签
        subnet.tags.clear()
        subnet.tags.extend(tags)
        
        self.db.commit()
        return True

    def get_ip_tags(self, ip_id: int) -> List[Tag]:
        """获取IP地址的标签"""
        ip_address = self.db.query(IPAddress).filter(IPAddress.id == ip_id).first()
        if not ip_address:
            return []
        return ip_address.tags

    def get_subnet_tags(self, subnet_id: int) -> List[Tag]:
        """获取网段的标签"""
        subnet = self.db.query(Subnet).filter(Subnet.id == subnet_id).first()
        if not subnet:
            return []
        return subnet.tags

    def remove_tag_from_ip(self, ip_id: int, tag_id: int) -> bool:
        """从IP地址移除标签"""
        ip_address = self.db.query(IPAddress).filter(IPAddress.id == ip_id).first()
        tag = self.db.query(Tag).filter(Tag.id == tag_id).first()
        
        if not ip_address or not tag:
            return False
        
        if tag in ip_address.tags:
            ip_address.tags.remove(tag)
            self.db.commit()
        
        return True

    def remove_tag_from_subnet(self, subnet_id: int, tag_id: int) -> bool:
        """从网段移除标签"""
        subnet = self.db.query(Subnet).filter(Subnet.id == subnet_id).first()
        tag = self.db.query(Tag).filter(Tag.id == tag_id).first()
        
        if not subnet or not tag:
            return False
        
        if tag in subnet.tags:
            subnet.tags.remove(tag)
            self.db.commit()
        
        return True

    def add_tag_to_ip(self, ip_id: int, tag_id: int) -> bool:
        """为IP地址添加标签"""
        ip_address = self.db.query(IPAddress).filter(IPAddress.id == ip_id).first()
        tag = self.db.query(Tag).filter(Tag.id == tag_id).first()
        
        if not ip_address or not tag:
            return False
        
        if tag not in ip_address.tags:
            ip_address.tags.append(tag)
            self.db.commit()
        
        return True

    def add_tag_to_subnet(self, subnet_id: int, tag_id: int) -> bool:
        """为网段添加标签"""
        subnet = self.db.query(Subnet).filter(Subnet.id == subnet_id).first()
        tag = self.db.query(Tag).filter(Tag.id == tag_id).first()
        
        if not subnet or not tag:
            return False
        
        if tag not in subnet.tags:
            subnet.tags.append(tag)
            self.db.commit()
        
        return True

    def get_tags_usage_stats(self) -> List[dict]:
        """获取标签使用统计"""
        tags = self.get_all_tags()
        stats = []
        
        for tag in tags:
            ip_count = len(tag.ip_addresses)
            subnet_count = len(tag.subnets)
            stats.append({
                'tag': tag,
                'ip_count': ip_count,
                'subnet_count': subnet_count,
                'total_usage': ip_count + subnet_count
            })
        
        return stats