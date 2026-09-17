"""Dashboard endpoint: aggregated KPI summary."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.analytics import DashboardSummary
from app.services.analytics_service import get_dashboard_summary
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Get dashboard KPI summary",
    description=(
        "Returns aggregated platform statistics computed from live database records: "
        "total projects, sites, area, biodiversity and carbon metrics. "
        "**DEMO NOTICE**: Metric values are synthetic."
    ),
)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummary:
    return get_dashboard_summary(db)
