import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

PRIORITY_PATTERN = "^(LOW|MEDIUM|HIGH|CRITICAL)$"
STATUS_PATTERN = "^(SUBMITTED|ASSIGNED|IN_PROGRESS|ESCALATED|RESOLVED|CLOSED)$"


def _clean_text(v: str, minimum: int, label: str) -> str:
    v = v.strip()
    if len(v) < minimum:
        raise ValueError(f"{label} must be at least {minimum} characters long")
    return v


class ComplaintCreateRequest(BaseModel):
    category_id: uuid.UUID
    priority: str = Field(pattern=PRIORITY_PATTERN)
    description: str = Field(max_length=2000)

    @field_validator("description")
    @classmethod
    def check_description(cls, v: str) -> str:
        return _clean_text(v, 10, "Description")


class ComplaintUpdateRequest(BaseModel):
    category_id: uuid.UUID | None = None
    priority: str | None = Field(default=None, pattern=PRIORITY_PATTERN)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("description")
    @classmethod
    def check_description(cls, v: str | None) -> str | None:
        return None if v is None else _clean_text(v, 10, "Description")


class StatusUpdateRequest(BaseModel):
    new_status: str = Field(pattern=STATUS_PATTERN)
    expected_status: str | None = Field(default=None, pattern=STATUS_PATTERN)


class AssignmentRequest(BaseModel):
    staff_id: uuid.UUID


class ResolutionRequest(BaseModel):
    resolution_details: str = Field(max_length=4000)

    @field_validator("resolution_details")
    @classmethod
    def check_details(cls, v: str) -> str:
        return _clean_text(v, 5, "Resolution details")


class PersonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: uuid.UUID
    name: str
    email: str


class CategoryRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    category_id: uuid.UUID
    name: str


class SLAOut(BaseModel):
    target_duration: int
    deadline: datetime
    escalation_level: int
    escalated_at: datetime | None
    state: str  # ON_TRACK | APPROACHING | OVERDUE | MET | BREACHED


class HistoryOut(BaseModel):
    old_status: str
    new_status: str
    changed_at: datetime
    changed_by: PersonOut


class ResolutionOut(BaseModel):
    resolution_details: str
    resolved_at: datetime
    resolver: PersonOut


class ComplaintSummary(BaseModel):
    complaint_id: uuid.UUID
    reference: str
    description: str
    priority: str
    status: str
    category: CategoryRef
    creator: PersonOut
    assignee: PersonOut | None
    created_at: datetime
    updated_at: datetime
    sla: SLAOut | None


class ComplaintDetail(ComplaintSummary):
    history: list[HistoryOut]
    resolution: ResolutionOut | None
    permissions: dict[str, bool]


class ComplaintPage(BaseModel):
    items: list[ComplaintSummary]
    total: int
    limit: int
    offset: int
