"""
Project Workspace Manager & Path Router
========================================
Abstracts multi-project isolation for enterprise deliverables.
Enforces that raw files from one project never collide with another, and dictates
output routing so the sanitization and generation engines do not need to guess paths.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.core.config import (
    CLEAN_DIR,
    RAW_SOURCE_DIR,
    validate_clean_path,
)

STANDARD_STAGES = [
    "01_presales",
    "02_initiating",
    "03_planning",
    "04_executing",
    "05_monitoring",
    "06_closing",
    "07_internal_legal_contracts",
]


class ProjectWorkspace:
    """Represents an isolated enterprise project with mirrored raw and clean trees."""

    def __init__(self, project_id: str):
        self.project_id = project_id.strip()
        self.raw_dir: Path = RAW_SOURCE_DIR / "projects" / self.project_id
        self.clean_dir: Path = CLEAN_DIR / "projects" / self.project_id

    def ensure_dirs(self, custom_stages: Optional[List[str]] = None) -> None:
        """Provision lifecycle stage directories for both raw and clean trees."""
        stages = custom_stages or STANDARD_STAGES
        for s in stages:
            (self.raw_dir / s).mkdir(parents=True, exist_ok=True)
            (self.clean_dir / s).mkdir(parents=True, exist_ok=True)

    def get_stage_dir(self, stage_name: str, is_raw: bool = False) -> Path:
        """Get the directory path for a specific lifecycle stage."""
        base = self.raw_dir if is_raw else self.clean_dir
        return base / stage_name

    def list_raw_files(self, stage: Optional[str] = None) -> List[Path]:
        """List all inbound un-sanitized files for this project."""
        base = self.raw_dir / stage if stage else self.raw_dir
        if not base.exists():
            return []
        return [p for p in base.rglob("*") if p.is_file() and not p.name.startswith(".")]

    def list_clean_files(self, stage: Optional[str] = None) -> List[Path]:
        """List all production-ready sanitized files for this project."""
        base = self.clean_dir / stage if stage else self.clean_dir
        if not base.exists():
            return []
        return [p for p in base.rglob("*") if p.is_file() and not p.name.startswith(".")]

    def resolve_clean_file(self, filename: str) -> Optional[Path]:
        """Find a file inside this project's clean workspace."""
        for p in self.clean_dir.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                if p.name.lower() == filename.lower() or filename.lower() in p.name.lower():
                    return validate_clean_path(p)
        return None

    def resolve_raw_file(self, filename: str) -> Optional[Path]:
        """Find a file inside this project's raw intake (internal use only)."""
        for p in self.raw_dir.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                if p.name.lower() == filename.lower() or filename.lower() in p.name.lower():
                    return p
        return None

    def get_team(self):
        """Retrieve team allocation for this project."""
        from src.core.team import TeamManager
        return TeamManager.get_project_team(self.project_id)

    def get_template_context(self) -> Dict[str, Any]:
        """Generate Jinja context variables for this project's team."""
        from src.core.team import TeamManager
        return TeamManager.get_template_context(self.project_id)

    def sanitize(self, engine=None, mapping=None):
        """
        Execute sanitization strictly from this project's raw folder
        into this project's clean folder.
        """
        if engine is None:
            from src.core.pii.engine import PiiEngine
            engine = PiiEngine()
        return engine.sanitize_directory(
            source_dir=self.raw_dir,
            output_dir=self.clean_dir,
            mapping=mapping,
            recursive=True,
            copy_non_matching=True,
        )


class WorkspaceRouter:
    """Central manager coordinating active projects and ingestion paths."""

    @classmethod
    def get_incoming_dir(cls) -> Path:
        """Global intake directory for newly received files prior to project triage."""
        p = RAW_SOURCE_DIR / "incoming"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def get_project(cls, project_id: str) -> ProjectWorkspace:
        """Get or initialize a ProjectWorkspace handle."""
        return ProjectWorkspace(project_id)

    @classmethod
    def list_projects(cls) -> List[str]:
        """List all projects that exist in raw or clean repositories."""
        projects = set()
        raw_proj = RAW_SOURCE_DIR / "projects"
        if raw_proj.exists():
            for d in raw_proj.iterdir():
                if d.is_dir() and not d.name.startswith("."):
                    projects.add(d.name)
        clean_proj = CLEAN_DIR / "projects"
        if clean_proj.exists():
            for d in clean_proj.iterdir():
                if d.is_dir() and not d.name.startswith("."):
                    projects.add(d.name)
        return sorted(list(projects))

    @classmethod
    def create_project(
        cls,
        project_id: str,
        client_name: str = "Enterprise Client",
        vendor_name: str = "Consulting Partner",
        stages: Optional[List[str]] = None,
    ) -> ProjectWorkspace:
        """Provision a new project with its raw and clean directory clusters."""
        proj = cls.get_project(project_id)
        proj.ensure_dirs(custom_stages=stages)

        meta = {
            "project_id": project_id,
            "client_name": client_name,
            "vendor_name": vendor_name,
            "created_at": datetime.now().isoformat(),
        }
        with open(proj.clean_dir / "project.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        return proj

    @classmethod
    def route_sanitization(
        cls,
        project_id: str,
        engine=None,
        mapping=None,
    ):
        """Sanitize an entire project using the workspace router."""
        proj = cls.get_project(project_id)
        return proj.sanitize(engine=engine, mapping=mapping)
