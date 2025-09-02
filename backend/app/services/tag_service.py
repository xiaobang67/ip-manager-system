from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.tag_repository import TagRepository
from app.schemas.tag import TagCreate, TagUpdate, TagResponse, EntityTags
from app.core.exceptions import ValidationError, NotFoundError


class TagService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TagRepository(db)

    def create_tag(self, tag_data: TagCreate) -> TagResponse:
        """创建标签"""
        # 检查标签名称是否已存在
        existing_tag = self.repository.get_tag_by_name(tag_data.name)
        if existing_tag:
            raise ValidationError(f"Tag with name '{tag_data.name}' already exists")
        
        db_tag = self.repository.create_tag(tag_data)
        return TagResponse.from_orm(db_tag)

    def get_tag_by_id(self, tag_id: int) -> TagResponse:
        """根据ID获取标签"""
        db_tag = self.repository.get_tag_by_id(tag_id)
        if not db_tag:
            raise NotFoundError(f"Tag with id {tag_id} not found")
        return TagResponse.from_orm(db_tag)

    def get_all_tags(self, skip: int = 0, limit: int = 100) -> List[TagResponse]:
        """获取所有标签"""
        db_tags = self.repository.get_all_tags(skip, limit)
        return [TagResponse.from_orm(tag) for tag in db_tags]

    def search_tags(self, query: str) -> List[TagResponse]:
        """搜索标签"""
        db_tags = self.repository.search_tags(query)
        return [TagResponse.from_orm(tag) for tag in db_tags]

    def update_tag(self, tag_id: int, tag_data: TagUpdate) -> TagResponse:
        """更新标签"""
        # 检查标签是否存在
        existing_tag = self.repository.get_tag_by_id(tag_id)
        if not existing_tag:
            raise NotFoundError(f"Tag with id {tag_id} not found")
        
        # 如果更新名称，检查是否与其他标签冲突
        if tag_data.name and tag_data.name != existing_tag.name:
            name_conflict = self.repository.get_tag_by_name(tag_data.name)
            if name_conflict:
                raise ValidationError(f"Tag with name '{tag_data.name}' already exists")
        
        db_tag = self.repository.update_tag(tag_id, tag_data)
        return TagResponse.from_orm(db_tag)

    def delete_tag(self, tag_id: int) -> bool:
        """删除标签"""
        if not self.repository.get_tag_by_id(tag_id):
            raise NotFoundError(f"Tag with id {tag_id} not found")
        
        return self.repository.delete_tag(tag_id)

    def assign_tags_to_ip(self, ip_id: int, tag_ids: List[int]) -> bool:
        """为IP地址分配标签"""
        # 验证所有标签是否存在
        for tag_id in tag_ids:
            if not self.repository.get_tag_by_id(tag_id):
                raise NotFoundError(f"Tag with id {tag_id} not found")
        
        success = self.repository.assign_tags_to_ip(ip_id, tag_ids)
        if not success:
            raise NotFoundError(f"IP address with id {ip_id} not found")
        
        return success

    def assign_tags_to_subnet(self, subnet_id: int, tag_ids: List[int]) -> bool:
        """为网段分配标签"""
        # 验证所有标签是否存在
        for tag_id in tag_ids:
            if not self.repository.get_tag_by_id(tag_id):
                raise NotFoundError(f"Tag with id {tag_id} not found")
        
        success = self.repository.assign_tags_to_subnet(subnet_id, tag_ids)
        if not success:
            raise NotFoundError(f"Subnet with id {subnet_id} not found")
        
        return success

    def get_ip_tags(self, ip_id: int) -> EntityTags:
        """获取IP地址的标签"""
        db_tags = self.repository.get_ip_tags(ip_id)
        tags = [TagResponse.from_orm(tag) for tag in db_tags]
        return EntityTags(
            entity_id=ip_id,
            entity_type="ip",
            tags=tags
        )

    def get_subnet_tags(self, subnet_id: int) -> EntityTags:
        """获取网段的标签"""
        db_tags = self.repository.get_subnet_tags(subnet_id)
        tags = [TagResponse.from_orm(tag) for tag in db_tags]
        return EntityTags(
            entity_id=subnet_id,
            entity_type="subnet",
            tags=tags
        )

    def add_tag_to_ip(self, ip_id: int, tag_id: int) -> bool:
        """为IP地址添加标签"""
        # 验证标签是否存在
        if not self.repository.get_tag_by_id(tag_id):
            raise NotFoundError(f"Tag with id {tag_id} not found")
        
        success = self.repository.add_tag_to_ip(ip_id, tag_id)
        if not success:
            raise NotFoundError(f"IP address with id {ip_id} not found")
        
        return success

    def add_tag_to_subnet(self, subnet_id: int, tag_id: int) -> bool:
        """为网段添加标签"""
        # 验证标签是否存在
        if not self.repository.get_tag_by_id(tag_id):
            raise NotFoundError(f"Tag with id {tag_id} not found")
        
        success = self.repository.add_tag_to_subnet(subnet_id, tag_id)
        if not success:
            raise NotFoundError(f"Subnet with id {subnet_id} not found")
        
        return success

    def remove_tag_from_ip(self, ip_id: int, tag_id: int) -> bool:
        """从IP地址移除标签"""
        # 验证标签是否存在
        if not self.repository.get_tag_by_id(tag_id):
            raise NotFoundError(f"Tag with id {tag_id} not found")
        
        success = self.repository.remove_tag_from_ip(ip_id, tag_id)
        if not success:
            raise NotFoundError(f"IP address with id {ip_id} not found")
        
        return success

    def remove_tag_from_subnet(self, subnet_id: int, tag_id: int) -> bool:
        """从网段移除标签"""
        # 验证标签是否存在
        if not self.repository.get_tag_by_id(tag_id):
            raise NotFoundError(f"Tag with id {tag_id} not found")
        
        success = self.repository.remove_tag_from_subnet(subnet_id, tag_id)
        if not success:
            raise NotFoundError(f"Subnet with id {subnet_id} not found")
        
        return success

    def get_tags_usage_stats(self) -> List[dict]:
        """获取标签使用统计"""
        stats = self.repository.get_tags_usage_stats()
        result = []
        
        for stat in stats:
            result.append({
                'tag': TagResponse.from_orm(stat['tag']),
                'ip_count': stat['ip_count'],
                'subnet_count': stat['subnet_count'],
                'total_usage': stat['total_usage']
            })
        
        return result