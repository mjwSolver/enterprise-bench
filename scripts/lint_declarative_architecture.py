#!/usr/bin/env python3
"""
lint_declarative_architecture.py — Mechanical Guardrail for Presentation Architecture

Enforces the Declarative Spec + Static Runner invariant (Directive 5 & ADR):
Rejects any new or modified Python scripts that imperatively hardcode slide
layouts, shapes, coordinates, and copy instead of decoupling content into
declarative YAML specs (specs/<topic>.yaml) and static runners.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

# Legacy scripts created prior to ADR codification that are locked
LEGACY_SCRIPT_ALLOWLIST = {
    "scripts/compile_native_databricks_jobs_pptx.py",
    "scripts/generate_before_after_comparison.py",
    "scripts/generate_current_cdsw_process.py",
    "scripts/generate_databricks_jobs_architecture.py",
    "scripts/generate_drawio_single_slide.py",
    "scripts/generate_expanded_cdsw_process.py",
    "scripts/generate_interwoven_migration.py",
    "scripts/generate_multislide_drawio_review.py",
    "scripts/generate_proposed_aws_lambda.py",
    "scripts/generate_xyz_decks.py",
    "scripts/generate_xyz_enhanced_visual_deck.py",
    "scripts/test_drawio_pptx_integration.py",
    "scripts/test_editorial_guidelines_comparison.py",
    "scripts/verify_encapsulation_pattern.py",
}

# Directories that implement engine/compiler primitives (allowed to manipulate pptx directly)
ENGINE_ALLOWLIST_DIRS = (
    "src/ppt_engine",
    "src/docx_engine",
    "src/xlsx_engine",
    "tests",
)


def is_imperative_pptx_script(path: Path) -> tuple[bool, str]:
    """
    Analyzes a Python file to determine if it is a monolithic imperative slide layout script.
    Returns (is_violation, reason).
    """
    rel_path = str(path.as_posix())

    # Skip engine core libraries and tests
    if any(rel_path.startswith(prefix) for prefix in ENGINE_ALLOWLIST_DIRS):
        return False, "Engine primitive or test"

    # Skip legacy locked scripts
    if rel_path in LEGACY_SCRIPT_ALLOWLIST:
        return False, "Legacy allowlisted script"

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"Could not read file: {e}"

    lines = content.splitlines()
    line_count = len(lines)

    # Check if pptx is imported
    has_pptx_import = bool(
        re.search(r"^\s*(import\s+pptx|from\s+pptx\b)", content, re.MULTILINE)
    )

    if not has_pptx_import:
        return False, "Does not import python-pptx"

    # Check if YAML spec is consumed
    has_yaml_consumer = bool(
        re.search(r"\b(yaml\.safe_load|yaml\.load)\b", content)
        and re.search(r"specs/.*\.ya?ml", content)
    )

    # Detect imperative shape creation calls
    imperative_shape_calls = len(
        re.findall(r"\.(add_shape|add_textbox|add_table|add_picture)\(", content)
    )

    # Violation criteria:
    # 1. Imports pptx AND has >= 100 lines AND has > 5 imperative shape additions without consuming YAML spec
    if line_count >= 100 and imperative_shape_calls >= 5 and not has_yaml_consumer:
        return True, (
            f"Monolithic imperative layout detected ({line_count} lines, "
            f"{imperative_shape_calls} imperative shape calls, zero YAML spec consumption)."
        )

    # 2. Hardcoded slide text strings + add_shape across large script
    if line_count >= 150 and not has_yaml_consumer:
        return True, (
            f"Imperative presentation script exceeds 150 lines ({line_count} lines) "
            "without consuming a declarative YAML specification (specs/<topic>.yaml)."
        )

    return False, "Passed"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify adherence to Declarative YAML-First presentation architecture."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Specific files to lint. If omitted, checks all Python files under scripts/.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on any imperative presentation script warning.",
    )
    args = parser.parse_args()

    files_to_check: list[Path] = []
    if args.files:
        for f in args.files:
            p = Path(f)
            if p.suffix == ".py" and p.is_file():
                files_to_check.append(p)
    else:
        scripts_dir = Path("scripts")
        if scripts_dir.is_dir():
            files_to_check.extend(scripts_dir.glob("*.py"))

    violations = []
    for f in sorted(files_to_check):
        is_viol, reason = is_imperative_pptx_script(f)
        if is_viol:
            violations.append((f, reason))

    if violations:
        print("\n" + "=" * 78, file=sys.stderr)
        print("🚨 [DECLARATIVE ARCHITECTURE GUARDRAIL VIOLATION]", file=sys.stderr)
        print("=" * 78, file=sys.stderr)
        for filepath, reason in violations:
            print(f"\n❌ File: {filepath}", file=sys.stderr)
            print(f"   Reason: {reason}", file=sys.stderr)
            print(
                "   Required: Decouple content into a declarative YAML specification "
                "(specs/<topic>.yaml) and execute via a reusable static compiler.",
                file=sys.stderr,
            )
            print(
                "   Reference: docs/decisions/ADR_DECLARATIVE_YAML_VS_IMPERATIVE_PYTHON.md",
                file=sys.stderr,
            )
        print("\n" + "=" * 78 + "\n", file=sys.stderr)
        return 1

    print("✓ Declarative architecture guardrail passed (zero imperative layout violations).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
