from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default='#007bff', pattern=r'^#[0-9A-Fa-f]{6}$')
    description: Optional[str] = None

    @validator('name')
    def validate_name(cls, v):
        # 标签名称只允许字母、数字、中文、连字符和下划线
        if not re.match(r'^[\w\u4e00-\u9fff\-]+$', v):
            raise ValueError('Tag name can only contain letters, numbers, Chinese characters, hyphens and underscores')
        return v.strip()


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    description: Optional[str] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not re.match(r'^[\w\u4e00-\u9fff\-]+$', v):
                raise ValueError('Tag name can only contain letters, numbers, Chinese characters, hyphens and underscores')
            return v.strip()
        return v


class TagResponse(TagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TagAssignment(BaseModel):
    entity_id: int
    entity_type: str = Field(..., pattern=r'^(ip|subnet)$')
    tag_ids: List[int]


class EntityTags(BaseModel):
    entity_id: int
    entity_type: str
    tags: List[TagResponse]