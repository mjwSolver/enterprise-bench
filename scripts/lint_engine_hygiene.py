#!/usr/bin/env python3
"""
lint_engine_hygiene.py — Automated Engine & Neutrality Hygiene Guardrail

Blocks common hardcoded leaks and invariant regressions in `src/` at lint and commit time:
  1. Hardcoded workstation home paths (`/Users/...`, `/home/...`, `C:\\Users\\...`)
  2. Client-specific names/domains inside project-neutral `src/` modules
  3. Sub-8.0pt font assignments in `src/ppt_engine/`
  4. Literal Unicode emojis in `src/ppt_engine/`
  5. Shapes added via `.add_shape(` in archetypes/widgets without `strip_shape_shadows(...)`
  6. Synthetic metadata fallbacks (`dict.get("impact"|"business_impact"|"tracker"|"subtitle", "<str>")`)
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import List, Tuple

WORKSTATION_PATH_RE = re.compile(r"(?:/Users/|/home/|C:\\\\Users\\\\)[^\s\"']+")
CLIENT_LEAK_RE = re.compile(
    r"\b(?:morula(?:ivf)?|bsim(?:_migration)?|toyota|tsusho|teramedik|embryo|oocyte|blastocyst)\b",
    re.IGNORECASE,
)
_PII_SCRUBBER_FILES = {
    "src/core/slug_registry.py",
    "src/core/pii/detectors.py",
    "src/core/pii/engine.py",
}
# Aligned with src/ppt_engine/archetypes/common.py EMOJI_PATTERN (excludes U+2794 arrow ➔)
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u2793\u2795-\u27BF\uFE0F]")
OPT_IN_META_KEYS = {"impact", "business_impact", "tracker", "subtitle"}

# Modules whose regex/range definitions legitimately contain emoji codepoint patterns
_EMOJI_DEF_FILES = {
    "src/ppt_engine/archetypes/common.py",
    "src/ppt_engine/spec_linter.py",
    "src/ppt_engine/diagram_v2/auditor.py",
}
_RENDERING_EMOJI_PREFIXES = (
    "src/ppt_engine/archetypes/",
    "src/ppt_engine/widgets/",
    "src/ppt_engine/pitch_deck.py",
    "src/ppt_engine/diagram_v2/models.py",
    "src/ppt_engine/diagram_v2/pptx_compiler.py",
)


def _const_float(node: ast.AST) -> float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return float(node.value)
    return None


def _lint_file(path: Path) -> Tuple[List[str], List[str]]:
    """Inspect a single Python file under `src/`. Returns (errors, warnings)."""
    rel = path.as_posix()
    errors: List[str] = []
    warnings: List[str] = []

    if not rel.startswith("src/") and "/src/" not in rel:
        return errors, warnings
    if "src/" in rel and not rel.startswith("src/"):
        rel = rel[rel.index("src/"):]

    try:
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=rel)
    except Exception as e:
        return [f"{rel}: AST parse failed ({e})"], warnings

    lines = content.splitlines()
    is_ppt = rel.startswith("src/ppt_engine/")
    is_archetype_or_widget = rel.startswith(("src/ppt_engine/archetypes/", "src/ppt_engine/widgets/"))

    # Line/AST checks on string constants & assignments
    for node in ast.walk(tree):
        lineno = getattr(node, "lineno", 0)
        line_txt = lines[lineno - 1] if 0 < lineno <= len(lines) else ""
        if "hygiene: ignore" in line_txt:
            continue

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value
            if WORKSTATION_PATH_RE.search(val):
                errors.append(
                    f"[WORKSTATION_PATH_LEAK] {rel}:{lineno} hardcodes workstation path literal; derive dynamically from repo root or CWD."
                )
            if CLIENT_LEAK_RE.search(val) and rel not in _PII_SCRUBBER_FILES:
                errors.append(
                    f"[PROJECT_NEUTRALITY_LEAK] {rel}:{lineno} embeds client-specific term inside core src/; move to external YAML specs."
                )
            if rel.startswith(_RENDERING_EMOJI_PREFIXES) and rel not in _EMOJI_DEF_FILES and EMOJI_RE.search(val):
                if not re.match(r"^\s*(print|rprint|logger\.)", line_txt):
                    errors.append(
                        f"[ZERO_EMOJI_INVARIANT] {rel}:{lineno} embeds forbidden Unicode emoji inside rendering module."
                    )

        if is_ppt and isinstance(node, ast.Assign):
            # Detect `*.font.size = Pt(<8.0)` or `font.size = Pt(<8.0)`
            for tgt in node.targets:
                is_font_sz = (
                    isinstance(tgt, ast.Attribute)
                    and tgt.attr == "size"
                    and (
                        (isinstance(tgt.value, ast.Attribute) and tgt.value.attr == "font")
                        or (isinstance(tgt.value, ast.Name) and tgt.value.id == "font")
                    )
                )
                if is_font_sz:
                    if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "Pt" and node.value.args:
                        sz = _const_float(node.value.args[0])
                        if sz is not None and sz < 8.0:
                            errors.append(
                                f"[SUB_8PT_FONT_FLOOR] {rel}:{lineno} sets .font.size = Pt({sz}) below 8.0pt floor."
                            )

        if is_ppt and isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "font_size_pt":
                    sz = _const_float(kw.value)
                    if sz is not None and sz < 8.0:
                        errors.append(
                            f"[SUB_8PT_FONT_FLOOR] {rel}:{lineno} passes font_size_pt={sz} below 8.0pt floor."
                        )

            # Flag synthetic defaults like row.get("impact", "HIGH")
            if isinstance(node.func, ast.Attribute) and node.func.attr == "get" and len(node.args) == 2:
                k_node, d_node = node.args
                if isinstance(k_node, ast.Constant) and isinstance(k_node.value, str) and k_node.value in OPT_IN_META_KEYS:
                    if isinstance(d_node, ast.Constant) and isinstance(d_node.value, str) and d_node.value.strip():
                        warnings.append(
                            f"[SYNTHETIC_METADATA_FALLBACK] {rel}:{lineno} injects hardcoded default '{d_node.value}' for opt-in key '{k_node.value}'."
                        )

    # Function-level shadow stripping check inside archetypes, widgets & pitch_deck
    if is_archetype_or_widget:
        for fn in ast.walk(tree):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                seg = ast.get_source_segment(content, fn) or ""
                adds = seg.count(".add_shape(")
                strips = seg.count("strip_shape_shadows(") + seg.count("_flatten(")
                has_loop_strip = "for s in slide.shapes" in seg or "for sh in " in seg
                if adds > 0 and strips == 0 and not has_loop_strip:
                    errors.append(
                        f"[UNSTRIPPED_SHADOW] {rel}:{fn.lineno} (`{fn.name}`) calls `.add_shape()` ({adds}x) without `strip_shape_shadows(...)`."
                    )
                elif adds > strips and "for " not in seg and not has_loop_strip:
                    errors.append(
                        f"[UNSTRIPPED_SHADOW] {rel}:{fn.lineno} (`{fn.name}`) adds {adds} shapes but only strips shadows on {strips}."
                    )
                for m in re.finditer(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\.shadow\.inherit\s*=\s*False\b", seg, re.MULTILINE):
                    var = m.group(1)
                    if f"strip_shape_shadows({var})" not in seg and f"_flatten({var})" not in seg and not has_loop_strip:
                        errors.append(
                            f"[UNSTRIPPED_SHADOW] {rel}:{fn.lineno} (`{fn.name}`) sets `{var}.shadow.inherit = False` without `strip_shape_shadows({var})` (leaves `<a:effectRef>`)."
                        )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Enforce engine hygiene, project neutrality, and anti-hardcoding invariants.")
    parser.add_argument("files", nargs="*", help="Specific files to lint; defaults to all *.py under src/.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    args = parser.parse_args()

    targets: List[Path] = []
    if args.files:
        for f in args.files:
            p = Path(f)
            if p.suffix == ".py" and p.is_file():
                targets.append(p)
    else:
        src_dir = Path("src")
        if src_dir.is_dir():
            targets.extend(sorted(src_dir.rglob("*.py")))

    all_errors: List[str] = []
    all_warnings: List[str] = []
    for p in targets:
        errs, warns = _lint_file(p)
        all_errors.extend(errs)
        all_warnings.extend(warns)

    for w in all_warnings:
        print(f"⚠ {w}", file=sys.stderr)
    for e in all_errors:
        print(f"❌ {e}", file=sys.stderr)

    if all_errors or (args.strict and all_warnings):
        print(
            f"\n🚨 Engine hygiene guardrail failed ({len(all_errors)} errors, {len(all_warnings)} warnings).",
            file=sys.stderr,
        )
        return 1

    print("✓ Engine hygiene guardrail passed (zero leaks, sub-8pt fonts, emojis, or unstripped shapes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
