"""Initial schema: users, projects, sites (PostGIS), site_metrics, monitoring_events.

Revision ID: 001_initial_schema
Revises:
Create Date: 2024-01-01

"""

from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa

from alembic import op

revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable PostGIS extension (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology")

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "user", name="userrole"),
            nullable=False,
            server_default="user",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # --- projects ---
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "project_type",
            sa.Enum("carbon", "biodiversity", "carbon_biodiversity", name="projecttype"),
            nullable=False,
            server_default="carbon",
        ),
        sa.Column("region", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "completed", "planned", "paused", name="projectstatus"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_id", "projects", ["id"])
    op.create_index("ix_projects_name", "projects", ["name"])

    # --- sites ---
    op.create_table(
        "sites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "completed", "planned", "inactive", name="sitestatus"),
            nullable=False,
            server_default="active",
        ),
        # PostGIS geometry: POLYGON in WGS84 (SRID=4326)
        sa.Column(
            "geometry",
            geoalchemy2.types.Geometry(geometry_type="POLYGON", srid=4326),
            nullable=False,
        ),
        sa.Column("area_hectares", sa.Float(), nullable=True),
        sa.Column("centroid_lat", sa.Float(), nullable=True),
        sa.Column("centroid_lng", sa.Float(), nullable=True),
        sa.Column("monitoring_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sites_id", "sites", ["id"])
    op.create_index("ix_sites_name", "sites", ["name"])
    op.create_index("ix_sites_project_id", "sites", ["project_id"])
    # Spatial GIST index for efficient geospatial queries
    op.create_index("ix_sites_geometry", "sites", ["geometry"], postgresql_using="gist")

    # --- site_metrics ---
    op.create_table(
        "site_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("carbon_value", sa.Float(), nullable=False),
        sa.Column("biodiversity_score", sa.Float(), nullable=False),
        sa.Column("vegetation_index", sa.Float(), nullable=False),
        sa.Column("monitoring_score", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_site_metrics_id", "site_metrics", ["id"])
    op.create_index("ix_site_metrics_site_id", "site_metrics", ["site_id"])
    op.create_index("ix_site_metrics_recorded_at", "site_metrics", ["recorded_at"])

    # --- monitoring_events ---
    op.create_table(
        "monitoring_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "field_survey",
                "satellite_review",
                "drone_survey",
                "data_collection",
                "stakeholder_meeting",
                "incident",
                name="eventtype",
            ),
            nullable=False,
            server_default="field_survey",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitoring_events_id", "monitoring_events", ["id"])
    op.create_index("ix_monitoring_events_site_id", "monitoring_events", ["site_id"])


def downgrade() -> None:
    op.drop_table("monitoring_events")
    op.drop_table("site_metrics")
    op.drop_table("sites")
    op.drop_table("projects")
    op.drop_table("users")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS eventtype")
    op.execute("DROP TYPE IF EXISTS sitestatus")
    op.execute("DROP TYPE IF EXISTS projectstatus")
    op.execute("DROP TYPE IF EXISTS projecttype")
    op.execute("DROP TYPE IF EXISTS userrole")
