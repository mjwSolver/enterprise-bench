"""
Enterprise Core Infrastructure Package
"""
from src.core.config import (
    ROOT_DIR,
    RAW_SOURCE_DIR,
    CLEAN_DIR,
    TEMPLATES_DIR,
    PRESETS_DIR,
    THEMES_DIR,
    DECK_CONFIGS_DIR,
    ASSETS_DIR,
    ICONS_DIR,
    IMAGES_DIR,
    OUTPUT_DIR,
    ensure_workspace_dirs,
    get_theme_path,
    get_template_path,
    validate_clean_path,
    WorkspaceSecurityError,
)
from src.core.models import (
    Stakeholder,
    ActionItem,
    Milestone,
    ProjectInfo,
    BASTPayload,
    MoMPayload,
)
from src.core.theme import (
    EnterpriseTheme,
    list_available_themes,
    parse_hex,
)
from src.core.sanitizer import (
    sanitize_text,
    sanitize_docx,
    DEFAULT_SCRUB_RULES,
)
from src.core.workspace import (
    ProjectWorkspace,
    WorkspaceRouter,
)
from src.core.change_request import (
    ChangeRequestProcessor,
    CRSubmission,
    CRProcessingResult,
)
from src.core.team import (
    StaffMember,
    StaffRoster,
    ProjectTeamMember,
    ProjectTeam,
    TeamManager,
)
from src.core.vault_builder import (
    TeamVaultBuilder,
    LocalVault,
)
from src.core.alias_linter import (
    AliasLinter,
    AliasAuditReport,
    AliasFinding,
)
from src.core.scaffold import create_project_scaffold

__all__ = [
    "create_project_scaffold",
    "ROOT_DIR",
    "RAW_SOURCE_DIR",
    "CLEAN_DIR",
    "TEMPLATES_DIR",
    "validate_clean_path",
    "WorkspaceSecurityError",
    "PRESETS_DIR",
    "THEMES_DIR",
    "DECK_CONFIGS_DIR",
    "ASSETS_DIR",
    "ICONS_DIR",
    "IMAGES_DIR",
    "OUTPUT_DIR",
    "ensure_workspace_dirs",
    "get_theme_path",
    "get_template_path",
    "Stakeholder",
    "ActionItem",
    "Milestone",
    "ProjectInfo",
    "BASTPayload",
    "MoMPayload",
    "EnterpriseTheme",
    "list_available_themes",
    "parse_hex",
    "sanitize_text",
    "sanitize_docx",
    "DEFAULT_SCRUB_RULES",
    "ProjectWorkspace",
    "WorkspaceRouter",
    "ChangeRequestProcessor",
    "CRSubmission",
    "CRProcessingResult",
    "StaffMember",
    "StaffRoster",
    "ProjectTeamMember",
    "ProjectTeam",
    "TeamManager",
    "TeamVaultBuilder",
    "LocalVault",
    "AliasLinter",
    "AliasAuditReport",
    "AliasFinding",
]
