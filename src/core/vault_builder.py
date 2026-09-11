"""
Local Team & Client Vault Builder
=================================
Manages local-only identity bindings between standardized ROLE_* / CLIENT_* aliases
and real practitioner / client personnel identities.
Strictly local: never committed to Git.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.core.config import PRESETS_DIR, CLEAN_DIR


class StaffBinding(BaseModel):
    full_name: Optional[str] = None
    official_position: str
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


class ClientBinding(BaseModel):
    full_name: Optional[str] = None
    position: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class LocalVault(BaseModel):
    version: str = "1.0"
    security_classification: str = "CONFIDENTIAL - LOCAL IDENTITY VAULT ONLY"
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    staff_bindings: Dict[str, StaffBinding] = Field(default_factory=dict)
    client_bindings: Dict[str, Any] = Field(default_factory=dict)


class TeamVaultBuilder:
    """Manages creation, inspection, and updates of the local identity vault."""

    GLOBAL_VAULT_PATH: Path = PRESETS_DIR / "staff_vault.local.json"

    @classmethod
    def load_vault(cls, project_id: Optional[str] = None) -> LocalVault:
        """Load project-specific vault or fallback to global vault."""
        vault_path = cls._resolve_vault_path(project_id)
        if not vault_path.exists():
            return LocalVault()
        with open(vault_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return LocalVault.model_validate(data)

    @classmethod
    def save_vault(cls, vault: LocalVault, project_id: Optional[str] = None) -> Path:
        """Save vault locally (enforced to end with .local.json to prevent git commit)."""
        vault_path = cls._resolve_vault_path(project_id)
        vault_path.parent.mkdir(parents=True, exist_ok=True)
        vault.last_updated = datetime.now().isoformat()
        with open(vault_path, "w", encoding="utf-8") as f:
            f.write(vault.model_dump_json(indent=2))
        return vault_path

    @classmethod
    def _resolve_vault_path(cls, project_id: Optional[str] = None) -> Path:
        if project_id:
            return CLEAN_DIR / "projects" / project_id / "team_vault.local.json"
        return cls.GLOBAL_VAULT_PATH

    @classmethod
    def bind_staff(
        cls,
        role_alias: str,
        full_name: str,
        official_position: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> None:
        """Bind a real consulting staff member to a standardized ROLE_* alias."""
        alias = role_alias.upper() if role_alias.upper().startswith("ROLE_") else f"ROLE_{role_alias.upper()}"
        vault = cls.load_vault(project_id)
        vault.staff_bindings[alias] = StaffBinding(
            full_name=full_name.strip(),
            official_position=official_position.strip(),
            email=email.strip() if email else None,
            phone=phone.strip() if phone else None,
        )
        cls.save_vault(vault, project_id)

    @classmethod
    def bind_client(
        cls,
        client_alias: str,
        full_name: str,
        position: str,
        project_id: Optional[str] = None,
    ) -> None:
        """Bind a client stakeholder to a CLIENT_* alias (stored strictly locally)."""
        alias = client_alias.upper() if client_alias.upper().startswith("CLIENT_") else f"CLIENT_{client_alias.upper()}"
        vault = cls.load_vault(project_id)
        vault.client_bindings[alias] = {
            "full_name": full_name.strip(),
            "position": position.strip(),
        }
        cls.save_vault(vault, project_id)

    @classmethod
    def get_replacement_map(cls, project_id: Optional[str] = None) -> Dict[str, str]:
        """
        Generate a flat replacement map of all assigned ROLE_* and CLIENT_* aliases
        to their actual human names.
        """
        vault = cls.load_vault(project_id)
        # If project vault is checked and missing keys, fall back to global
        global_vault = cls.load_vault(None) if project_id else vault

        mapping: Dict[str, str] = {}

        # Staff mappings
        all_staff = {**global_vault.staff_bindings, **vault.staff_bindings}
        for alias, binding in all_staff.items():
            if binding.full_name:
                mapping[alias] = binding.full_name

        # Client mappings
        all_client = {**global_vault.client_bindings, **vault.client_bindings}
        for alias, binding in all_client.items():
            if isinstance(binding, dict) and "full_name" in binding:
                mapping[alias] = binding["full_name"]
            elif isinstance(binding, str):
                mapping[alias] = binding

        return mapping

    @classmethod
    def list_unassigned_roles(cls, project_id: Optional[str] = None) -> List[str]:
        """List all ROLE_* aliases in the vault that have not yet been assigned real names."""
        vault = cls.load_vault(project_id)
        unassigned = []
        for alias, binding in vault.staff_bindings.items():
            if not binding.full_name:
                unassigned.append(alias)
        return unassigned
