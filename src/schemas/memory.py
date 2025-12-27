"""Memory schema definitions."""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class MemoryBase(BaseModel):
    """Base memory schema."""

    content: str = Field(..., description="Content of the memory")
    category: str = Field("fact", description="Category: fact, preference, context")
    source_conversation_id: Optional[str] = Field(None, description="Source conversation for provenance")


class MemoryCreate(MemoryBase):
    """Schema for creating a memory."""
    pass


class MemoryUpdate(BaseModel):
    """Schema for updating a memory."""

    content: Optional[str] = Field(None, description="Updated content")
    category: Optional[str] = Field(None, description="Updated category")
    is_active: Optional[bool] = Field(None, description="Whether the memory is active")


class MemoryResponse(MemoryBase):
    """Schema for memory response."""

    id: str = Field(..., description="Memory ID")
    user_id: str = Field(..., description="User ID")
    is_active: bool = Field(..., description="Whether the memory is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True