"""Project Pydantic schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.project import ProjectStatus, ProjectType


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    project_type: ProjectType = ProjectType.carbon
    region: str | None = None
    status: ProjectStatus = ProjectStatus.active
    start_date: date | None = None


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    project_type: ProjectType | None = None
    region: str | None = None
    status: ProjectStatus | None = None
    start_date: date | None = None


class ProjectResponse(BaseModel):
    """Full project data returned from API."""

    id: int
    name: str
    description: str | None
    project_type: ProjectType
    region: str | None
    status: ProjectStatus
    start_date: date | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime
    site_count: int = 0
    total_area_hectares: float = 0.0

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    """Paginated list of projects."""

    data: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
