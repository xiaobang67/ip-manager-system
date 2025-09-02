from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    search_name = Column(String(100), nullable=True)
    search_params = Column(JSON, nullable=False)
    is_favorite = Column(Boolean, default=False, index=True)
    used_count = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="search_history")

    def __repr__(self):
        return f"<SearchHistory(id={self.id}, user_id={self.user_id}, name='{self.search_name}')>"