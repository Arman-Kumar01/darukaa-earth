"""Project Pydantic schemas."""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.project import ProjectStatus, ProjectType


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    project_type: ProjectType = ProjectType.carbon
    region: Optional[str] = None
    status: ProjectStatus = ProjectStatus.active
    start_date: Optional[date] = None


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    project_type: Optional[ProjectType] = None
    region: Optional[str] = None
    status: Optional[ProjectStatus] = None
    start_date: Optional[date] = None


class ProjectResponse(BaseModel):
    """Full project data returned from API."""

    id: int
    name: str
    description: Optional[str]
    project_type: ProjectType
    region: Optional[str]
    status: ProjectStatus
    start_date: Optional[date]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    site_count: int = 0
    total_area_hectares: float = 0.0

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    """Paginated list of projects."""

    data: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
