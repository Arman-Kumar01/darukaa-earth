"""Project service: business logic for project CRUD."""

import logging
import math

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.site import Site
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)

logger = logging.getLogger(__name__)


def _enrich_project_response(project: Project, db: Session) -> ProjectResponse:
    """Add computed fields (site_count, total_area) to a project response."""
    site_stats = (
        db.query(
            func.count(Site.id).label("site_count"),
            func.coalesce(func.sum(Site.area_hectares), 0.0).label("total_area"),
        )
        .filter(Site.project_id == project.id)
        .one()
    )
    resp = ProjectResponse.model_validate(project)
    resp.site_count = site_stats.site_count
    resp.total_area_hectares = float(site_stats.total_area)
    return resp


def get_projects(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    status: str | None = None,
    project_type: str | None = None,
) -> ProjectListResponse:
    """Return a paginated, filtered list of projects."""
    query = db.query(Project)

    if search:
        query = query.filter(
            Project.name.ilike(f"%{search}%") | Project.region.ilike(f"%{search}%")
        )
    if status:
        query = query.filter(Project.status == status)
    if project_type:
        query = query.filter(Project.project_type == project_type)

    total = query.count()
    offset = (page - 1) * page_size
    projects = query.order_by(Project.created_at.desc()).offset(offset).limit(page_size).all()

    data = [_enrich_project_response(p, db) for p in projects]

    return ProjectListResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if page_size else 1,
    )


def get_project(db: Session, project_id: int) -> ProjectResponse:
    """Get a single project by ID with site statistics."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found.",
        )
    return _enrich_project_response(project, db)


def create_project(db: Session, payload: ProjectCreate, user_id: int) -> ProjectResponse:
    """Create a new project owned by the current user."""
    project = Project(
        name=payload.name,
        description=payload.description,
        project_type=payload.project_type,
        region=payload.region,
        status=payload.status,
        start_date=payload.start_date,
        created_by=user_id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    logger.info(f"Project created: {project.name} (id={project.id})")
    return _enrich_project_response(project, db)


def update_project(db: Session, project_id: int, payload: ProjectUpdate) -> ProjectResponse:
    """Update project fields. Only provided fields are changed."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)
    return _enrich_project_response(project, db)


def delete_project(db: Session, project_id: int) -> dict:
    """Delete a project and its associated sites (cascade)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found.",
        )
    db.query(Project).filter(Project.id == project_id).delete(synchronize_session=False)
    db.commit()
    logger.info(f"Project deleted: id={project_id}")
    return {"detail": "Project deleted successfully."}
