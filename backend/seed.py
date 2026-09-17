"""
Darukaa.Earth — Database Seed Script
=====================================

Creates demo data for application demonstration:
- 2 user accounts (admin + regular user)
- 3 projects across different environmental types
- 9 sites with real polygon geometries
- 12-24 monthly metric observations per site (synthetic)
- Monitoring events per site

DEMO NOTICE: All metric values (carbon_value, biodiversity_score, etc.) are
SYNTHETIC and generated for application demonstration only. They do NOT
represent actual environmental measurements.

Seed data uses random.seed(42) for reproducibility.

Usage:
    cd backend
    python seed.py

To reset: drop and recreate the database, run migrations, then re-seed.
"""

import random
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.database import SessionLocal
from app.models import MonitoringEvent, Project, Site, SiteMetric, User
from app.models.monitoring_event import EventType
from app.models.project import ProjectStatus, ProjectType
from app.models.site import SiteStatus
from app.models.user import UserRole

# Deterministic seed for reproducible data
random.seed(42)


# ---------------------------------------------------------------------------
# Helper: generate a realistic polygon near a center point
# ---------------------------------------------------------------------------


def make_polygon(center_lng: float, center_lat: float, size_deg: float = 0.05) -> str:
    """
    Generate a WKT POLYGON string near the given center coordinates.
    size_deg controls the approximate size in degrees (~5km per 0.05 deg).
    """
    hw = size_deg / 2  # half-width
    hh = size_deg / 2  # half-height

    # Add slight irregularity for realism
    def jitter(val: float, amount: float = 0.005) -> float:
        return val + random.uniform(-amount, amount)

    nw = (center_lng - hw, center_lat + hh)
    ne = (center_lng + hw + jitter(0), center_lat + hh + jitter(0))
    se = (center_lng + hw, center_lat - hh + jitter(0))
    sw = (center_lng - hw + jitter(0), center_lat - hh)
    mid_e = (center_lng + hw + jitter(0.01), center_lat + jitter(0.01))

    points = [nw, ne, mid_e, se, sw, nw]  # close ring
    coords_str = ", ".join(f"{p[0]} {p[1]}" for p in points)
    return f"SRID=4326;POLYGON(({coords_str}))"


# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------

PROJECTS_DATA = [
    {
        "name": "Green Horizon Restoration",
        "description": (
            "Large-scale forest restoration project targeting degraded land across "
            "the Amazon buffer zone. Focuses on native species reintroduction and "
            "community-based carbon sequestration."
        ),
        "project_type": ProjectType.carbon_biodiversity,
        "region": "Pará, Brazil",
        "status": ProjectStatus.active,
        "start_date": date(2022, 3, 15),
        "sites": [
            {
                "name": "North Forest Corridor",
                "description": "Primary restoration zone — dense native canopy targeted.",
                "center": (-52.3, -3.1),
                "size": 0.08,
                "base_carbon": 45.0,
                "base_bio": 72.0,
            },
            {
                "name": "River Buffer Zone",
                "description": "Riparian restoration along Xingu tributary.",
                "center": (-52.1, -3.3),
                "size": 0.06,
                "base_carbon": 38.0,
                "base_bio": 68.0,
            },
            {
                "name": "Southern Degraded Plots",
                "description": "Former agricultural land converted to restoration.",
                "center": (-52.4, -3.5),
                "size": 0.07,
                "base_carbon": 22.0,
                "base_bio": 45.0,
            },
        ],
    },
    {
        "name": "Forest Carbon Initiative",
        "description": (
            "REDD+ compliant carbon offset project protecting primary forest "
            "in Borneo from deforestation. Verified carbon credits issued quarterly."
        ),
        "project_type": ProjectType.carbon,
        "region": "Kalimantan, Indonesia",
        "status": ProjectStatus.active,
        "start_date": date(2021, 7, 1),
        "sites": [
            {
                "name": "Peat Forest Reserve Alpha",
                "description": "High-carbon peatland with endangered orangutan habitat.",
                "center": (114.5, 0.8),
                "size": 0.1,
                "base_carbon": 82.0,
                "base_bio": 78.0,
            },
            {
                "name": "Dipterocarp Forest Beta",
                "description": "Mixed dipterocarp forest with high timber value protected.",
                "center": (114.7, 0.6),
                "size": 0.09,
                "base_carbon": 74.0,
                "base_bio": 71.0,
            },
            {
                "name": "Secondary Growth Zone",
                "description": "Regenerating forest with active replanting programme.",
                "center": (114.3, 0.9),
                "size": 0.07,
                "base_carbon": 41.0,
                "base_bio": 55.0,
            },
        ],
    },
    {
        "name": "Biodiversity Corridor Project",
        "description": (
            "Wildlife corridor creation connecting fragmented habitat patches "
            "across agricultural land in the Western Ghats. Targeted species include "
            "Asian elephant and Bengal tiger migration corridors."
        ),
        "project_type": ProjectType.biodiversity,
        "region": "Karnataka, India",
        "status": ProjectStatus.active,
        "start_date": date(2023, 1, 10),
        "sites": [
            {
                "name": "Elephant Corridor North",
                "description": "Critical pinch-point for elephant migration.",
                "center": (76.2, 14.8),
                "size": 0.06,
                "base_carbon": 28.0,
                "base_bio": 85.0,
            },
            {
                "name": "Tiger Reserve Buffer",
                "description": "Buffer zone adjacent to Nagarhole Tiger Reserve.",
                "center": (76.0, 14.6),
                "size": 0.07,
                "base_carbon": 31.0,
                "base_bio": 88.0,
            },
            {
                "name": "Riparian Linkage Strip",
                "description": "Riverside vegetation corridor linking two protected areas.",
                "center": (76.4, 14.9),
                "size": 0.04,
                "base_carbon": 19.0,
                "base_bio": 74.0,
            },
        ],
    },
]

EVENT_TYPES = [
    EventType.field_survey,
    EventType.satellite_review,
    EventType.drone_survey,
    EventType.data_collection,
]

EVENT_NOTES = [
    "Routine quarterly assessment. All metrics within expected range.",
    "Satellite imagery analysis — no significant canopy change detected.",
    "Drone survey completed. Vegetation health confirmed. Minor encroachment flagged.",
    "Annual biodiversity transect survey. 12 indicator species recorded.",
    "Carbon stock verification audit. Results consistent with previous assessment.",
    "Community patrol report filed. No illegal activity observed.",
    "Soil carbon sampling completed. Lab results pending.",
    "Remote sensing analysis updated. NDVI stable.",
]


def generate_metric_series(
    site_id: int,
    base_carbon: float,
    base_bio: float,
    n_months: int = 18,
    start_date: datetime = None,
) -> list[SiteMetric]:
    """
    Generate a realistic time-series of monthly site metrics.

    Trends modelled:
    - Carbon gradually increases (restoration capturing more CO2).
    - Biodiversity fluctuates with seasonal variation.
    - Vegetation index has seasonal sinusoidal variation.
    - Monitoring score gradually improves (programme maturity).
    """
    if start_date is None:
        start_date = datetime(2023, 1, 1, tzinfo=UTC)

    metrics = []
    carbon = base_carbon
    bio = base_bio
    monitoring = 60.0 + random.uniform(0, 10)

    for i in range(n_months):
        record_date = start_date + timedelta(days=30 * i)
        month_fraction = i / n_months

        # Carbon: gradual upward trend + small noise
        carbon += random.uniform(0.5, 2.5) + 0.3 * month_fraction
        carbon = min(carbon, 150.0)

        # Biodiversity: mean-reverting with seasonal fluctuation
        season_factor = 1 + 0.08 * (0.5 - abs(((i % 12) / 12) - 0.5))
        bio = bio * season_factor + random.uniform(-2.0, 2.5)
        bio = max(20.0, min(100.0, bio))

        # Vegetation index: NDVI proxy with seasonal variation
        vegetation = 0.55 + 0.2 * season_factor + random.uniform(-0.05, 0.05)
        vegetation = max(0.1, min(1.0, vegetation))

        # Monitoring score: improves over time
        monitoring = min(100.0, monitoring + random.uniform(0.2, 1.5))

        metrics.append(
            SiteMetric(
                site_id=site_id,
                recorded_at=record_date,
                carbon_value=round(carbon, 2),
                biodiversity_score=round(bio, 2),
                vegetation_index=round(vegetation, 4),
                monitoring_score=round(monitoring, 2),
            )
        )

    return metrics


def generate_monitoring_events(site_id: int, n_events: int = 6) -> list[MonitoringEvent]:
    """Generate realistic monitoring events over the past 18 months."""
    events = []
    base_date = date.today()
    for i in range(n_events):
        event_date = base_date - timedelta(days=random.randint(i * 45, (i + 1) * 60))
        events.append(
            MonitoringEvent(
                site_id=site_id,
                event_date=event_date,
                event_type=random.choice(EVENT_TYPES),
                notes=random.choice(EVENT_NOTES),
            )
        )
    return events


# ---------------------------------------------------------------------------
# Compute area/centroid using raw SQL (PostGIS)
# ---------------------------------------------------------------------------


def compute_spatial_properties(db: Session, wkt_geom: str) -> tuple[float, float, float]:
    """Calculate area in hectares and centroid using PostGIS."""
    from sqlalchemy import text

    result = db.execute(
        text("""
            SELECT
                ST_Area(ST_GeomFromText(:wkt, 4326)::geography) / 10000.0 AS area_ha,
                ST_Y(ST_Centroid(ST_GeomFromText(:wkt, 4326))) AS centroid_lat,
                ST_X(ST_Centroid(ST_GeomFromText(:wkt, 4326))) AS centroid_lng
        """),
        {"wkt": wkt_geom.replace("SRID=4326;", "")},
    ).first()

    return (
        round(float(result.area_ha), 4),
        float(result.centroid_lat),
        float(result.centroid_lng),
    )


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------


def seed(db: Session) -> None:
    """Run the complete seed — idempotent (checks for existing data)."""

    # Check if already seeded
    if db.query(User).count() > 0:
        print("⚠️  Database already contains data. Skipping seed.")
        print("   To re-seed, drop the database and run migrations again.")
        return

    print("🌱 Seeding Darukaa.Earth database...")

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    admin = User(
        name="Darukaa Admin",
        email="admin@darukaa.earth",
        password_hash=get_password_hash("DemoAdmin2024!"),
        role=UserRole.admin,
    )
    demo_user = User(
        name="Demo User",
        email="user@darukaa.earth",
        password_hash=get_password_hash("DemoUser2024!"),
        role=UserRole.user,
    )
    db.add_all([admin, demo_user])
    db.commit()
    db.refresh(admin)
    print(f"  ✅ Created users: {admin.email}, {demo_user.email}")

    # ------------------------------------------------------------------
    # Projects, Sites, Metrics
    # ------------------------------------------------------------------
    for proj_data in PROJECTS_DATA:
        project = Project(
            name=proj_data["name"],
            description=proj_data["description"],
            project_type=proj_data["project_type"],
            region=proj_data["region"],
            status=proj_data["status"],
            start_date=proj_data["start_date"],
            created_by=admin.id,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        print(f"  📁 Project: {project.name}")

        site_start_offset = 0
        for site_data in proj_data["sites"]:
            wkt_geom = make_polygon(
                site_data["center"][0], site_data["center"][1], site_data["size"]
            )

            area_ha, centroid_lat, centroid_lng = compute_spatial_properties(db, wkt_geom)

            site = Site(
                project_id=project.id,
                name=site_data["name"],
                description=site_data["description"],
                status=SiteStatus.active,
                geometry=wkt_geom,
                area_hectares=area_ha,
                centroid_lat=centroid_lat,
                centroid_lng=centroid_lng,
                monitoring_date=date.today() - timedelta(days=random.randint(30, 90)),
            )
            db.add(site)
            db.commit()
            db.refresh(site)
            print(f"    📍 Site: {site.name} ({area_ha:.1f} ha)")

            # Generate 18 monthly metrics
            start = datetime(2023, 1, 1, tzinfo=UTC) + timedelta(days=site_start_offset * 5)
            metrics = generate_metric_series(
                site.id,
                site_data["base_carbon"],
                site_data["base_bio"],
                n_months=18,
                start_date=start,
            )
            db.add_all(metrics)

            # Generate monitoring events
            events = generate_monitoring_events(site.id, n_events=6)
            db.add_all(events)

            site_start_offset += 1

        db.commit()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    total_sites = db.query(Site).count()
    total_metrics = db.query(SiteMetric).count()
    total_events = db.query(MonitoringEvent).count()

    print("\n✅ Seed complete!")
    print("   Users: 2 (admin + demo)")
    print(f"   Projects: {len(PROJECTS_DATA)}")
    print(f"   Sites: {total_sites}")
    print(f"   Metric records: {total_metrics}")
    print(f"   Monitoring events: {total_events}")
    print()
    print("📧 Demo credentials:")
    print("   Admin:    admin@darukaa.earth  /  DemoAdmin2024!")
    print("   User:     user@darukaa.earth   /  DemoUser2024!")
    print()
    print("⚠️  DEMO NOTICE: All analytics data is synthetic and does not")
    print("   represent real environmental measurements.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
