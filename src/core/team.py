"""
Team Precepts & Staff Allocation Subsystem
==========================================
Manages global practitioner profiles and per-project team assignments.
Enforces strict client privacy: only internal consulting staff members are tracked,
while client stakeholder identities remain isolated for PM review.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.core.config import CLEAN_DIR, PRESETS_DIR, ROOT_DIR


class StaffMember(BaseModel):
    """Global consulting practitioner profile."""
    staff_id: str = Field(..., description="Unique staff identifier (e.g. 'STAFF-001')")
    full_name: str = Field(..., description="Official full name of practitioner")
    official_position: str = Field(..., description="Corporate job title / grade")
    department: str = Field("Enterprise Consulting", description="Organizational unit")
    email: Optional[str] = Field(None, description="Corporate email address")
    primary_skills: List[str] = Field(default_factory=list, description="Core technical proficiencies")
    last_updated: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))


class StaffRoster(BaseModel):
    """Global directory containing all remembered staff members."""
    version: str = "1.0"
    description: str = "Global Directory of Consulting Practitioners"
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    staff: List[StaffMember] = Field(default_factory=list)


class ProjectTeamMember(BaseModel):
    """Staff member assigned to a specific engagement."""
    staff_id: str
    full_name: str
    project_role: str
    allocation_pct: int = 100
    is_key_personnel: bool = True
    assigned_deliverables: List[str] = Field(default_factory=list)


class ProjectTeam(BaseModel):
    """Scoped project team allocation."""
    project_id: str
    project_name: str = "Enterprise Project"
    client_confidentiality_policy: str = "Strict. Client identities require PM authorization."
    allocated_team: List[ProjectTeamMember] = Field(default_factory=list)


class TeamManager:
    """Manages global staff directory and project-scoped team bindings."""

    GLOBAL_ROSTER_PATH: Path = PRESETS_DIR / "staff_roster.json"

    @classmethod
    def load_global_roster(cls) -> StaffRoster:
        """Load global roster of all registered practitioners."""
        if not cls.GLOBAL_ROSTER_PATH.exists():
            return StaffRoster()
        with open(cls.GLOBAL_ROSTER_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return StaffRoster.model_validate(data)

    @classmethod
    def save_global_roster(cls, roster: StaffRoster) -> None:
        """Persist global roster to presets/."""
        cls.GLOBAL_ROSTER_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(cls.GLOBAL_ROSTER_PATH, "w", encoding="utf-8") as f:
            f.write(roster.model_dump_json(indent=2))

    @classmethod
    def find_staff(cls, query: str) -> Optional[StaffMember]:
        """Search staff by ID or substring in full name."""
        roster = cls.load_global_roster()
        q = query.strip().lower()
        for s in roster.staff:
            if s.staff_id.lower() == q or q in s.full_name.lower():
                return s
        return None

    @classmethod
    def add_staff(
        cls,
        full_name: str,
        official_position: str,
        department: str = "Enterprise Delivery",
        email: Optional[str] = None,
        primary_skills: Optional[List[str]] = None,
    ) -> StaffMember:
        """Register a new practitioner into the global directory."""
        roster = cls.load_global_roster()
        next_num = len(roster.staff) + 1
        staff_id = f"STAFF-{str(next_num).zfill(3)}"

        member = StaffMember(
            staff_id=staff_id,
            full_name=full_name.strip(),
            official_position=official_position.strip(),
            department=department.strip(),
            email=email,
            primary_skills=primary_skills or [],
        )
        roster.staff.append(member)
        roster.last_updated = datetime.now().isoformat()
        cls.save_global_roster(roster)
        return member

    @classmethod
    def get_project_team(cls, project_id: str) -> Optional[ProjectTeam]:
        """Load project-scoped team allocation."""
        team_file = CLEAN_DIR / "projects" / project_id / "team.json"
        if not team_file.exists():
            return None
        with open(team_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ProjectTeam.model_validate(data)

    @classmethod
    def save_project_team(cls, project_id: str, team: ProjectTeam) -> None:
        """Save project-scoped team allocation."""
        team_file = CLEAN_DIR / "projects" / project_id / "team.json"
        team_file.parent.mkdir(parents=True, exist_ok=True)
        with open(team_file, "w", encoding="utf-8") as f:
            f.write(team.model_dump_json(indent=2))

    @classmethod
    def assign_to_project(
        cls,
        project_id: str,
        staff_identifier: str,
        project_role: str,
        allocation_pct: int = 100,
        assigned_deliverables: Optional[List[str]] = None,
    ) -> ProjectTeamMember:
        """Assign a practitioner from global directory to a specific project."""
        staff = cls.find_staff(staff_identifier)
        if not staff:
            raise ValueError(f"Staff member '{staff_identifier}' not found in global roster.")

        team = cls.get_project_team(project_id) or ProjectTeam(project_id=project_id)

        # Check if already assigned
        existing = next((m for m in team.allocated_team if m.staff_id == staff.staff_id), None)
        if existing:
            existing.project_role = project_role
            existing.allocation_pct = allocation_pct
            if assigned_deliverables:
                existing.assigned_deliverables = assigned_deliverables
            assigned_member = existing
        else:
            assigned_member = ProjectTeamMember(
                staff_id=staff.staff_id,
                full_name=staff.full_name,
                project_role=project_role,
                allocation_pct=allocation_pct,
                assigned_deliverables=assigned_deliverables or [],
            )
            team.allocated_team.append(assigned_member)

        cls.save_project_team(project_id, team)
        return assigned_member

    @classmethod
    def get_template_context(cls, project_id: str) -> Dict[str, Any]:
        """
        Generate Jinja2 template context variables for document and presentation stamping:
        e.g. {{ vendor_pm_name }}, {{ vendor_lead_name }}, {{ team_members }}.
        """
        team = cls.get_project_team(project_id)
        if not team:
            return {}

        ctx: Dict[str, Any] = {
            "team_members": [m.model_dump() for m in team.allocated_team],
            "total_team_size": len(team.allocated_team),
        }

        # Auto-map standard enterprise consulting roles
        for m in team.allocated_team:
            role_lower = m.project_role.lower()
            if "project manager" in role_lower or "pm" in role_lower:
                ctx["vendor_pm_name"] = m.full_name
                ctx["vendor_pm_role"] = m.project_role
            elif "architect" in role_lower:
                ctx["vendor_lead_architect"] = m.full_name
            elif "steering" in role_lower:
                ctx["vendor_steering_lead"] = m.full_name
            elif "data engineer" in role_lower:
                ctx.setdefault("vendor_data_engineers", []).append(m.full_name)
            elif "analytics" in role_lower or "streamlit" in role_lower:
                ctx.setdefault("vendor_app_engineers", []).append(m.full_name)

        return ctx
