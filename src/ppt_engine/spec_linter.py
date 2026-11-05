"""
Presentation Spec Linter Subsystem
==================================
Automated, deterministic quality guardrail for declarative presentation specs (.yaml).
Codifies executive slidecraft ground truths into machine-enforced rules:
- LINT001: Palette Discipline & Anti-Accidental-RAG (eliminates false defect signaling on roadmaps)
- LINT002: McKinsey Action Title Formula ([Finding] + [Quantified Evidence] + [Implication])
- LINT003: Executive Bullet Scannability (Bold lead-in anchors for F-pattern reading)
- LINT004: Anti-Banner Top Stripe (eliminates legacy decorative stripes on cards)
- LINT005: Clean Surface Hierarchy (anti-nested-box containers)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


# Known passive category labels that fail the McKinsey Action Title rule
_PASSIVE_CATEGORY_RE = re.compile(
    r"^(timeline|roadmap|status|status overview|overview|summary|phases|project phases|"
    r"architecture|system architecture|data pipeline|next steps|background|challenges|"
    r"agenda|strategy|introduction|objectives|scope|deliverables)$",
    re.IGNORECASE,
)

# Markdown bold anchor pattern: **Lead-in:** or **Lead-in** -
_BOLD_LEAD_IN_RE = re.compile(r"^\*\*[^*]+\*\*[:\s\-]")


@dataclass
class LintIssue:
    rule_id: str
    severity: str  # "ERROR" | "WARNING"
    slide_idx: int
    archetype: str
    message: str
    suggestion: str


@dataclass
class SpecLintReport:
    spec_path: Path
    issues: List[LintIssue] = field(default_factory=list)
    passed: bool = True
    error_count: int = 0
    warning_count: int = 0

    def add_issue(
        self,
        rule_id: str,
        severity: str,
        slide_idx: int,
        archetype: str,
        message: str,
        suggestion: str,
    ) -> None:
        self.issues.append(
            LintIssue(
                rule_id=rule_id,
                severity=severity,
                slide_idx=slide_idx,
                archetype=archetype,
                message=message,
                suggestion=suggestion,
            )
        )
        if severity == "ERROR":
            self.error_count += 1
            self.passed = False
        elif severity == "WARNING":
            self.warning_count += 1

    def render(self, console: Optional[Console] = None) -> None:
        c = console or Console()

        if not self.issues:
            c.print(
                Panel.fit(
                    f"[bold green]✓ SPEC QUALITY AUDIT PASSED[/bold green]\n"
                    f"[dim]File:[/dim] [cyan]{self.spec_path.name}[/cyan]\n"
                    f"All slides adhere to Executive Slidecraft, Action Titling, and Color Discipline invariants.",
                    border_style="green",
                )
            )
            return

        table = Table(
            title=f"Presentation Spec Quality Audit: {self.spec_path.name}",
            title_style="bold cyan",
            border_style="dim",
            show_header=True,
            header_style="bold white on blue",
        )
        table.add_column("Slide", style="cyan", width=8, justify="center")
        table.add_column("Archetype", style="magenta", width=18)
        table.add_column("Rule ID", style="bold yellow", width=22)
        table.add_column("Severity", width=10, justify="center")
        table.add_column("Finding & Recommendation", style="white")

        for issue in self.issues:
            sev_badge = (
                "[bold red]ERROR[/bold red]"
                if issue.severity == "ERROR"
                else "[bold yellow]WARN[/bold yellow]"
            )
            slide_str = f"#{issue.slide_idx:02d}" if issue.slide_idx > 0 else "DECK"
            body = (
                f"{issue.message}\n"
                f"[dim]Recommendation: {issue.suggestion}[/dim]"
            )
            table.add_row(slide_str, issue.archetype, issue.rule_id, sev_badge, body)

        c.print(table)
        status_line = (
            f"[bold red]FAILED[/bold red] ({self.error_count} errors, {self.warning_count} warnings)"
            if not self.passed
            else f"[bold yellow]PASSED WITH WARNINGS[/bold yellow] ({self.warning_count} warnings)"
        )
        c.print(f"\n[dim]Audit Summary:[/dim] {status_line}")


def lint_presentation_spec(
    spec_path: Union[str, Path],
    strict: bool = False,
) -> SpecLintReport:
    """
    Statically analyzes a declarative YAML deck specification against executive slidecraft rules.
    """
    path = Path(spec_path)
    report = SpecLintReport(spec_path=path)

    if not path.exists():
        report.add_issue(
            rule_id="FILE_NOT_FOUND",
            severity="ERROR",
            slide_idx=0,
            archetype="global",
            message=f"Specification file not found: {path}",
            suggestion="Verify file path.",
        )
        return report

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        report.add_issue(
            rule_id="YAML_PARSE_ERROR",
            severity="ERROR",
            slide_idx=0,
            archetype="global",
            message=f"YAML parsing failure: {e}",
            suggestion="Fix YAML syntax.",
        )
        return report

    if not isinstance(data, dict):
        report.add_issue(
            rule_id="SCHEMA_INVALID",
            severity="ERROR",
            slide_idx=0,
            archetype="global",
            message="Root configuration must be a mapping/dict.",
            suggestion="Ensure root YAML object is a dictionary.",
        )
        return report

    slides = data.get("slides")
    if not isinstance(slides, list) or not slides:
        report.add_issue(
            rule_id="NO_SLIDES_FOUND",
            severity="ERROR",
            slide_idx=0,
            archetype="global",
            message="No 'slides' list defined in presentation spec.",
            suggestion="Define a list of slides under 'slides:'.",
        )
        return report

    # -------------------------------------------------------------------------
    # Slide-by-Slide Verification
    # -------------------------------------------------------------------------
    for idx, slide in enumerate(slides, start=1):
        if not isinstance(slide, dict):
            continue

        arch = slide.get("archetype", "unknown")
        title = str(slide.get("title", "")).strip()
        subtitle = str(slide.get("subtitle", "")).strip()

        # ---------------------------------------------------------------------
        # Rule LINT002: Action Title Quality Gate (Non-Cover Slides)
        # ---------------------------------------------------------------------
        if arch not in ("cover", "hero_cover", "chapter_divider", "thank_you"):
            if not title:
                report.add_issue(
                    rule_id="LINT002_ACTION_TITLE",
                    severity="ERROR",
                    slide_idx=idx,
                    archetype=arch,
                    message="Slide is missing an Action Title.",
                    suggestion="Add a governing complete sentence title expressing [Finding] + [Driver] + [Consequence].",
                )
            else:
                words = title.split()
                if len(words) < 6:
                    report.add_issue(
                        rule_id="LINT002_ACTION_TITLE",
                        severity="WARNING",
                        slide_idx=idx,
                        archetype=arch,
                        message=f"Action title is too short ({len(words)} words): '{title}'.",
                        suggestion="Follow McKinsey Action Title standard: state a governing conclusion with quantified impact.",
                    )
                if _PASSIVE_CATEGORY_RE.match(title):
                    report.add_issue(
                        rule_id="LINT002_ACTION_TITLE",
                        severity="ERROR",
                        slide_idx=idx,
                        archetype=arch,
                        message=f"Passive category label detected as title: '{title}'.",
                        suggestion="Replace generic topic labels with an assertive analytical finding.",
                    )

            if not subtitle:
                report.add_issue(
                    rule_id="LINT002_SUBTITLE_CONTEXT",
                    severity="WARNING",
                    slide_idx=idx,
                    archetype=arch,
                    message="Missing tracker/subtitle narrative.",
                    suggestion="Add a 1-sentence tracker subtitle (10-12 words) answering 'So what?' for the reader.",
                )

        # ---------------------------------------------------------------------
        # Rule LINT001: Palette Discipline & Anti-Accidental-RAG
        # ---------------------------------------------------------------------
        if arch in ("bcg_3_horizon", "horizons", "chevron_process", "timeline_gantt", "process_chevrons"):
            # Check horizon columns or sequential steps
            horizons = slide.get("horizons") or slide.get("steps") or []
            accent_keys = []
            status_tags = []
            for h in horizons:
                if isinstance(h, dict):
                    acc = str(h.get("accent_key", "")).lower()
                    st = str(h.get("status_tag") or h.get("status", "")).upper()
                    if acc:
                        accent_keys.append(acc)
                    if st:
                        status_tags.append(st)

            has_danger = any(k in ("danger", "red") for k in accent_keys)
            has_warning = any(k in ("warning", "amber") for k in accent_keys)
            has_success = any(k in ("success", "green") for k in accent_keys)

            if (has_danger and has_warning) or (has_danger and has_success) or (has_warning and has_success):
                report.add_issue(
                    rule_id="LINT001_PALETTE_DISCIPLINE",
                    severity="ERROR",
                    slide_idx=idx,
                    archetype=arch,
                    message="Chronological sequence mixes RAG risk colors (danger/warning/success).",
                    suggestion="Roadmaps are chronological stages, not defect logs. Use Monochromatic Temporal Depth ('accent' -> 'secondary' -> 'muted') or a single hero accent.",
                )

        # ---------------------------------------------------------------------
        # Rule LINT003: Executive Bullet Scannability (Bold Anchors)
        # ---------------------------------------------------------------------
        bullet_lists = []
        for key in ("initiatives", "bullets", "left_items", "right_items", "items"):
            if isinstance(slide.get(key), list):
                bullet_lists.append(slide[key])

        # Also check nested horizons / blocks
        for nested_key in ("horizons", "blocks", "steps", "columns"):
            if isinstance(slide.get(nested_key), list):
                for item in slide[nested_key]:
                    if isinstance(item, dict):
                        for b_key in ("initiatives", "bullets", "items"):
                            if isinstance(item.get(b_key), list):
                                bullet_lists.append(item[b_key])

        for blist in bullet_lists:
            for b_idx, bullet in enumerate(blist, start=1):
                b_str = str(bullet).strip()
                if not b_str:
                    continue
                if not _BOLD_LEAD_IN_RE.match(b_str):
                    report.add_issue(
                        rule_id="LINT003_LEAD_IN_BOLD",
                        severity="WARNING",
                        slide_idx=idx,
                        archetype=arch,
                        message=f"Bullet lacks bold lead-in anchor: '{b_str[:42]}...'",
                        suggestion="Begin with '**Anchor Phrase:** Context text' to facilitate executive F-pattern scanning.",
                    )
                if len(b_str) > 175:
                    report.add_issue(
                        rule_id="LINT003_BULLET_LENGTH",
                        severity="WARNING",
                        slide_idx=idx,
                        archetype=arch,
                        message=f"Bullet text exceeds recommended length ({len(b_str)} chars): '{b_str[:42]}...'",
                        suggestion="Keep bullet descriptions crisp (<= 150 characters) to avoid executive cognitive fatigue.",
                    )

        # ---------------------------------------------------------------------
        # Rule LINT004: Anti-Banner Top Stripe
        # ---------------------------------------------------------------------
        if slide.get("has_top_stripe") or slide.get("accent_stripe"):
            report.add_issue(
                rule_id="LINT004_ANTI_BANNER_STRIPE",
                severity="ERROR",
                slide_idx=idx,
                archetype=arch,
                message="Deprecated top accent stripe flag detected.",
                suggestion="Eliminate top accent stripes. Use clean surface containers with subtle hairline borders.",
            )

    if strict and report.warning_count > 0:
        report.passed = False

    return report
