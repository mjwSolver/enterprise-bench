"""
Unit Tests for Core Module
"""
import pytest
from src.core.config import ROOT_DIR, THEMES_DIR, TEMPLATES_DIR, get_theme_path
from src.core.theme import EnterpriseTheme, list_available_themes, parse_hex
from src.core.sanitizer import sanitize_text
from src.core.models import ProjectInfo, BASTPayload, Stakeholder


def test_theme_listing():
    themes = list_available_themes()
    assert "brickred" in themes
    assert "snowblue" in themes
    assert "default" in themes


def test_theme_loading():
    theme = EnterpriseTheme.from_yaml("brickred")
    assert theme.name.lower() == "brickred"
    assert theme.accent_primary.upper() == "#DC2626"
    assert theme.rgb_primary == (220, 38, 38)


def test_parse_hex():
    assert parse_hex("#FFFFFF") == (255, 255, 255)
    assert parse_hex("000000") == (0, 0, 0)
    assert parse_hex("#F00") == (255, 0, 0)


def test_sanitizer_text():
    sample = "Contract between PT Toyota Tsusho Indonesia and PT Mitra Integrasi Informatika."
    cleaned = sanitize_text(sample)
    assert "Toyota Tsusho" not in cleaned
    assert "{{ client_company }}" in cleaned
    assert "{{ vendor_company }}" in cleaned


def test_models():
    stakeholder = Stakeholder(name="Alice", role="PM", organization="Client Corp")
    proj = ProjectInfo(
        project_name="Digital Transformation",
        stakeholders=[stakeholder],
    )
    assert proj.project_name == "Digital Transformation"
    assert len(proj.stakeholders) == 1


def test_clean_workspace_security_boundary():
    from src.core.config import (
        RAW_SOURCE_DIR,
        CLEAN_DIR,
        validate_clean_path,
        WorkspaceSecurityError,
        get_template_path,
    )
    # Reading from clean directory is allowed
    clean_sample = CLEAN_DIR / "01_presales" / "Account_POC_Scope_Template.docx"
    if clean_sample.exists():
        assert validate_clean_path(clean_sample) == clean_sample.resolve()

    # Reading from raw directory directly raises WorkspaceSecurityError
    raw_sample = RAW_SOURCE_DIR / "01_presales" / "Account_POC_Scope_Template.docx"
    with pytest.raises(WorkspaceSecurityError):
        validate_clean_path(raw_sample)

    # get_template_path returns path inside clean_workspace
    found = get_template_path("Account_POC_Scope_Template.docx")
    assert found is not None
    assert str(CLEAN_DIR.resolve()) in str(found.resolve())

