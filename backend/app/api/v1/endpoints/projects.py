"""Project CRUD endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectListResponse, ProjectResponse, ProjectUpdate
from app.services.auth_service import get_current_user
from app.services.project_service import (
    create_project,
    delete_project,
    get_project,
    get_projects,
    update_project,
)

router = APIRouter()


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="List all projects",
    description="Returns a paginated list of projects with optional search, status, and type filtering.",
)
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, description="Search by name or region"),
    status: str | None = Query(None, description="Filter by status"),
    project_type: str | None = Query(None, description="Filter by type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectListResponse:
    return get_projects(db, page, page_size, search, status, project_type)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=201,
    summary="Create a new project",
)
def create_new_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    return create_project(db, payload, current_user.id)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a project by ID",
)
def get_project_by_id(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    return get_project(db, project_id)


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project",
)
def update_project_by_id(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    return update_project(db, project_id, payload)


@router.delete(
    "/{project_id}",
    summary="Delete a project",
    description="Permanently deletes a project and all its associated sites.",
)
def delete_project_by_id(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return delete_project(db, project_id)
