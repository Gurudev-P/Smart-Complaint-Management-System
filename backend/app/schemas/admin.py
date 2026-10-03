import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Category name must be at least 2 characters long")
        return v


class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    active_flag: bool | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    category_id: uuid.UUID
    name: str
    description: str | None
    active_flag: bool


class SLARuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    rule_id: uuid.UUID
    priority: str
    target_minutes: int
    approaching_percent: int


class SLARuleUpdateRequest(BaseModel):
    target_minutes: int | None = Field(default=None, ge=1, le=60 * 24 * 90)
    approaching_percent: int | None = Field(default=None, ge=1, le=99)


class SLACheckResult(BaseModel):
    checked: int
    approaching_notified: int
    escalated: int


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    notification_id: uuid.UUID
    complaint_id: uuid.UUID | None
    event_type: str
    message: str
    channel: str
    read_status: bool
    created_at: datetime


class NotificationPage(BaseModel):
    items: list[NotificationOut]
    unread: int
