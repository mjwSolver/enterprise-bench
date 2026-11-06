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
- LINT006: Design Contract Enforcement (modular layout & diagnostic rules: executive_csuite, technical_architecture, strategic_tradeoff)
- LINT007: Raw Markdown Syntax Guardrail (detects unparsed markdown asterisks, backticks, links, headers in presentation copy)
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

# Markdown bold anchor patterns:
# 1. Lead-in anchor: **Lead-in:** or **Lead-in** -
_BOLD_LEAD_IN_RE = re.compile(r"^\*\*[^*]+\*\*[:\s\-]")
# 2. Inverted keyword bold: text containing **2-3 bold keywords** anywhere
_BOLD_INLINE_RE = re.compile(r"\*\*[^*]+\*\*")

# Raw markdown syntax detection patterns (LINT007)
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_MD_CODE_RE = re.compile(r"`([^`]+)`")
_MD_HEADER_RE = re.compile(r"(?:^|\n)\s*#{1,6}\s+\S+")
_MD_STRIKE_RE = re.compile(r"~~([^~]+)~~")
_MD_LIST_BULLET_RE = re.compile(r"(?:^|\n)\s*[-*+]\s+\S+")
_MD_BOLD_RE = re.compile(r"\*\*[^*]+\*\*|__[^_]+__")
_MD_LEADING_BULLET_RE = re.compile(r"^\s*[-*+•–]\s+")


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


VALID_DESIGN_CONTRACTS = {
    "executive_csuite",
    "technical_architecture",
    "strategic_tradeoff",
}

_CONTRACT_ALIASES = {
    "executive_csuite": "executive_csuite",
    "executive-csuite": "executive_csuite",
    "executive": "executive_csuite",
    "csuite": "executive_csuite",
    "technical_architecture": "technical_architecture",
    "technical-architecture": "technical_architecture",
    "architecture": "technical_architecture",
    "tech_arch": "technical_architecture",
    "strategic_tradeoff": "strategic_tradeoff",
    "strategic-tradeoff": "strategic_tradeoff",
    "tradeoff": "strategic_tradeoff",
    "trade-off": "strategic_tradeoff",
}


def _normalize_contract(name: Any) -> Optional[str]:
    if not isinstance(name, str):
        return None
    cleaned = name.strip().lower().replace(" ", "_")
    return _CONTRACT_ALIASES.get(cleaned)


def _lint_executive_csuite_contract(
    slide: Dict[str, Any],
    slide_idx: int,
    archetype: str,
    title: str,
    report: SpecLintReport,
) -> None:
    # 1. Max 2 bullets per container
    for key in ("bullets", "initiatives", "left_items", "right_items"):
        blist = slide.get(key)
        if isinstance(blist, list) and len(blist) > 2:
            report.add_issue(
                rule_id="LINT006_DESIGN_CONTRACT",
                severity="ERROR",
                slide_idx=slide_idx,
                archetype=archetype,
                message=f"Executive C-Suite contract limits containers to max 2 bullets (found {len(blist)} in '{key}').",
                suggestion="Executive C-Suite slides enforce max_bullets_per_container: 2. Trim narrative into <= 2 high-impact items with bold lead-ins.",
            )

    items_val = slide.get("items")
    if isinstance(items_val, list) and items_val and all(isinstance(x, str) for x in items_val):
        if len(items_val) > 2:
            report.add_issue(
                rule_id="LINT006_DESIGN_CONTRACT",
                severity="ERROR",
                slide_idx=slide_idx,
                archetype=archetype,
                message=f"Executive C-Suite contract limits containers to max 2 bullets (found {len(items_val)} in 'items').",
                suggestion="Executive C-Suite slides enforce max_bullets_per_container: 2. Trim narrative into <= 2 high-impact items with bold lead-ins.",
            )

    for nested_key in ("items", "blocks", "columns", "horizons", "cards", "steps"):
        c_list = slide.get(nested_key)
        if isinstance(c_list, list):
            for c_idx, container in enumerate(c_list, start=1):
                if isinstance(container, dict):
                    c_title = container.get("title") or container.get("label") or f"{nested_key} #{c_idx}"
                    for b_key in ("bullets", "initiatives", "items"):
                        b_sub = container.get(b_key)
                        if isinstance(b_sub, list) and len(b_sub) > 2 and all(isinstance(x, str) for x in b_sub):
                            report.add_issue(
                                rule_id="LINT006_DESIGN_CONTRACT",
                                severity="ERROR",
                                slide_idx=slide_idx,
                                archetype=archetype,
                                message=f"Executive C-Suite contract limits containers to max 2 bullets (found {len(b_sub)} in '{c_title}').",
                                suggestion="Executive C-Suite slides enforce max_bullets_per_container: 2. Trim container narrative into <= 2 high-impact items with bold lead-ins.",
                            )

    # 2. Hero Stat / KPI presence
    has_hero_stat = False
    for kpi_key in ("hero_stat", "hero_metric", "stat", "kpi", "metric", "metric_highlight"):
        if slide.get(kpi_key):
            has_hero_stat = True
            break

    if not has_hero_stat:
        if archetype in ("split_hero", "hero_metric", "kpi_grid", "metric_grid", "balanced_scorecard"):
            has_hero_stat = True

    if not has_hero_stat:
        for nested_key in ("items", "blocks", "horizons", "columns", "cards"):
            c_list = slide.get(nested_key)
            if isinstance(c_list, list):
                for container in c_list:
                    if isinstance(container, dict):
                        if any(container.get(k) for k in ("hero_stat", "stat", "kpi", "metric", "metric_highlight", "metric_badge", "value")):
                            has_hero_stat = True
                            break
            if has_hero_stat:
                break

    if not has_hero_stat:
        report.add_issue(
            rule_id="LINT006_DESIGN_CONTRACT",
            severity="ERROR",
            slide_idx=slide_idx,
            archetype=archetype,
            message="Executive C-Suite contract requires a dominant Hero Stat / KPI focal anchor.",
            suggestion="Executive C-Suite slides must feature a dominant focal anchor (hero_stat >= 36 pt, e.g., '+28%' or '$4.2M') with descriptor.",
        )

    # 3. Takeaway anti-echo check
    takeaway = slide.get("takeaway")
    if isinstance(takeaway, str) and takeaway.strip() and title:
        t_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", title.lower()))
        tk_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", takeaway.lower()))
        filtered_tk_words = {w for w in tk_words if w not in {"decision", "lever", "capital", "takeaway", "impact"}}
        if t_words and filtered_tk_words:
            overlap = len(t_words.intersection(filtered_tk_words)) / max(len(t_words), len(filtered_tk_words))
            if overlap >= 0.75:
                report.add_issue(
                    rule_id="LINT006_DESIGN_CONTRACT",
                    severity="ERROR",
                    slide_idx=slide_idx,
                    archetype=archetype,
                    message="Executive C-Suite contract violation: Takeaway bar echoes the action headline.",
                    suggestion="The headline asserts the Finding; the takeaway bar strictly delivers the Decision Lever / Capital Equation / So-What.",
                )


def _lint_strategic_tradeoff_contract(
    slide: Dict[str, Any],
    slide_idx: int,
    archetype: str,
    title: str,
    report: SpecLintReport,
) -> None:
    # 1. Reject 50/50 symmetric splits
    split_val = slide.get("split_ratio")
    if split_val is not None:
        is_symmetric = False
        if isinstance(split_val, str):
            s_clean = split_val.strip().replace(" ", "").replace("%", "")
            parts = re.split(r"[/:\-]", s_clean)
            if len(parts) == 2:
                try:
                    is_symmetric = float(parts[0]) == float(parts[1])
                except ValueError:
                    pass
            elif s_clean in ("1:1", "1/1", "0.5/0.5", "50/50"):
                is_symmetric = True
        elif isinstance(split_val, (list, tuple)) and len(split_val) == 2:
            try:
                is_symmetric = float(split_val[0]) == float(split_val[1])
            except (ValueError, TypeError):
                pass
        elif isinstance(split_val, (int, float)):
            is_symmetric = (float(split_val) == 0.5)

        if is_symmetric:
            report.add_issue(
                rule_id="LINT006_DESIGN_CONTRACT",
                severity="ERROR",
                slide_idx=slide_idx,
                archetype=archetype,
                message=f"Strategic Trade-Off contract violation: Symmetric 50/50 split rejected ('{split_val}').",
                suggestion="Enforce asymmetric layout routing: use an asymmetric split (e.g. 40/60 or 35/65) to visually prioritize the recommended path.",
            )

    if slide.get("left_width") and slide.get("right_width"):
        try:
            lw = float(str(slide["left_width"]).replace("in", "").replace('"', '').strip())
            rw = float(str(slide["right_width"]).replace("in", "").replace('"', '').strip())
            if abs(lw - rw) < 0.1:
                report.add_issue(
                    rule_id="LINT006_DESIGN_CONTRACT",
                    severity="ERROR",
                    slide_idx=slide_idx,
                    archetype=archetype,
                    message=f"Strategic Trade-Off contract violation: Equal column widths detected ({lw}'' vs {rw}'').",
                    suggestion="Enforce asymmetric layout routing: split canvas 40/60 or 35/65.",
                )
        except ValueError:
            pass

    # 2. Ensure recommended option has accent/badge
    has_recommendation = False
    if any(slide.get(k) for k in ("recommended", "recommended_option", "recommended_index", "recommendation")):
        has_recommendation = True

    option_containers = []
    for key in ("options", "items", "blocks", "columns"):
        val = slide.get(key)
        if isinstance(val, list) and len(val) >= 2 and all(isinstance(x, dict) for x in val):
            option_containers = val
            break

    if option_containers:
        for opt in option_containers:
            badge_text = " ".join([
                str(opt.get("badge") or ""),
                str(opt.get("metric_badge") or ""),
                str(opt.get("status") or ""),
                str(opt.get("status_tag") or ""),
                str(opt.get("tag") or ""),
                str(opt.get("title") or ""),
            ]).upper()
            if any(w in badge_text for w in ("RECOMMEND", "TARGET", "PREFERRED", "CHOSEN", "SELECTED")):
                has_recommendation = True
                break
            if opt.get("recommended") or opt.get("is_recommended"):
                has_recommendation = True
                break
            if str(opt.get("accent_key", "")).lower() in ("accent", "primary", "hero", "target", "recommended", "success"):
                has_recommendation = True
                break

    if not has_recommendation and (slide.get("left_title") or slide.get("right_title") or slide.get("left_items") or slide.get("right_items")):
        rt = str(slide.get("right_title") or "").upper()
        rb = str(slide.get("right_badge") or "").upper()
        if any(w in rt or w in rb for w in ("RECOMMEND", "TARGET", "AFTER", "PREFERRED", "TO-BE")):
            has_recommendation = True

    if not has_recommendation:
        report.add_issue(
            rule_id="LINT006_DESIGN_CONTRACT",
            severity="ERROR",
            slide_idx=slide_idx,
            archetype=archetype,
            message="Strategic Trade-Off contract violation: No option marked with 'RECOMMENDED' badge or primary accent.",
            suggestion="Designate the target/recommended option with badge: 'RECOMMENDED' and accent_key: 'accent' to visually anchor the decision.",
        )

    # 3. Neutral comparison title check
    if title:
        neutral_match = re.match(
            r"^(option|vendor|architecture|solution|tooling|scenario)?\s*(comparison|trade-?offs?|evaluation|analysis)$",
            title.strip(),
            re.IGNORECASE,
        )
        if neutral_match:
            report.add_issue(
                rule_id="LINT006_DESIGN_CONTRACT",
                severity="ERROR",
                slide_idx=slide_idx,
                archetype=archetype,
                message=f"Strategic Trade-Off contract violation: Neutral comparison title detected ('{title}').",
                suggestion="Follow McKinsey Action Title standard: state the decisive selection outcome (e.g., 'Target Solution Outperforms Legacy Architecture on Latency and TCO').",
            )


def _lint_technical_architecture_contract(
    slide: Dict[str, Any],
    slide_idx: int,
    archetype: str,
    title: str,
    report: SpecLintReport,
) -> None:
    # 1. Diagnostic Status Validation
    arch_containers = []
    for key in ("blocks", "items", "nodes", "steps", "containers"):
        val = slide.get(key)
        if isinstance(val, list):
            for itm in val:
                if isinstance(itm, dict):
                    arch_containers.append(itm)

    has_any_diagnostic_status = False
    for c in arch_containers:
        # Check explicit diagnostic_status field
        if "diagnostic_status" in c:
            d_val = str(c["diagnostic_status"]).strip().lower()
            if d_val in (
                "defect", "bottleneck", "error", "p1", "p2", "p3", "bug", "blocker",
                "wait", "boundary", "staging", "lock", "resource lock", "warning",
                "active", "flow", "compute", "processing", "core", "primary",
                "target", "verified", "production", "target state", "success", "stable"
            ):
                has_any_diagnostic_status = True
            else:
                report.add_issue(
                    rule_id="LINT006_DESIGN_CONTRACT",
                    severity="ERROR",
                    slide_idx=slide_idx,
                    archetype=archetype,
                    message=f"Technical Architecture contract violation: Unrecognized diagnostic_status '{c['diagnostic_status']}'.",
                    suggestion="Must adhere to 4-tier standard: Defect (Red), Boundary/Wait (Amber), Active Flow (Blue), Target State (Green).",
                )
                has_any_diagnostic_status = True

        # Check metric_badge / status_tag / status / badge
        badge_str = " ".join([
            str(c.get("metric_badge") or ""),
            str(c.get("status_tag") or ""),
            str(c.get("status") or ""),
            str(c.get("badge") or ""),
        ]).strip().lower()

        accent = str(c.get("accent_key") or "").lower()

        if badge_str:
            if any(k in badge_str for k in (
                "defect", "bottleneck", "error", "p1", "p2", "p3", "bug", "blocker", "critical",
                "wait", "boundary", "staging", "lock", "warning", "amber", "queued", "pending", "gate",
                "active", "flow", "compute", "processing", "stream", "ingest", "core",
                "target", "verified", "production", "target state", "success", "stable"
            )):
                has_any_diagnostic_status = True
            elif accent in ("danger", "warning", "info", "primary", "accent", "success", "red", "amber", "blue", "green"):
                has_any_diagnostic_status = True

        if accent in ("danger", "warning", "info", "primary", "accent", "success", "red", "amber", "blue", "green"):
            has_any_diagnostic_status = True

    if arch_containers and len(arch_containers) >= 2 and not has_any_diagnostic_status:
        report.add_issue(
            rule_id="LINT006_DESIGN_CONTRACT",
            severity="WARNING",
            slide_idx=slide_idx,
            archetype=archetype,
            message="Technical Architecture contract expects diagnostic status tracking ('defect', 'wait', 'active', 'target') on architectural components.",
            suggestion="Assign 4-tier diagnostic statuses (e.g. metric_badge: 'P1 DEFECT', 'RESOURCE LOCK', or 'TARGET STATE') to convey system lifecycle state.",
        )

    # 2. Connectors source/destination integrity
    connectors = slide.get("connectors") or slide.get("flows") or slide.get("edges")
    if isinstance(connectors, list):
        for c_idx, conn in enumerate(connectors, start=1):
            if isinstance(conn, dict):
                src = conn.get("from") or conn.get("source") or conn.get("src") or conn.get("from_node")
                dst = conn.get("to") or conn.get("target") or conn.get("dst") or conn.get("to_node")
                conn_id = conn.get("id") or f"connector #{c_idx}"
                if not (src and dst):
                    report.add_issue(
                        rule_id="LINT006_DESIGN_CONTRACT",
                        severity="ERROR",
                        slide_idx=slide_idx,
                        archetype=archetype,
                        message=f"Technical Architecture contract violation: Connector '{conn_id}' missing explicit source or destination anchor.",
                        suggestion="Every connector must specify both source ('from') and destination ('to') node anchors.",
                    )


def _lint_markdown_syntax(
    slide: Dict[str, Any],
    slide_idx: int,
    archetype: str,
    report: SpecLintReport,
) -> None:
    """
    Rule LINT007: Inline Markdown Syntax & DrawingML Compilation Guardrail
    Validates that inline typography (bold, italic, underline, monospace code spans)
    is syntactically balanced, closed, and compiles cleanly into DrawingML runs,
    while blocking unrenderable block markdown (headers, raw links, redundant bullet glyphs).
    """
    def _validate_text_spans(field_label: str, val: Any, is_bullet: bool = False) -> None:
        if not isinstance(val, str) or not val.strip():
            return
        txt = val.strip()

        # 1. Delimiter Balance & Syntax Closure (Zero Unclosed Formatting)
        if txt.count("**") % 2 != 0:
            report.add_issue(
                rule_id="LINT007_UNCLOSED_FORMATTING",
                severity="ERROR",
                slide_idx=slide_idx,
                archetype=archetype,
                message=f"Unclosed markdown bold markers '**' detected in {field_label}: '{txt[:45]}...'.",
                suggestion="Ensure all bold tags are balanced (e.g. '**Lead-in:** body text').",
            )

        if txt.count("__") % 2 != 0:
            report.add_issue(
                rule_id="LINT007_UNCLOSED_FORMATTING",
                severity="ERROR",
                slide_idx=slide_idx,
                archetype=archetype,
                message=f"Unclosed markdown underline markers '__' detected in {field_label}: '{txt[:45]}...'.",
                suggestion="Ensure all underline tags are balanced (e.g. '__underlined text__').",
            )

        if txt.count("`") % 2 != 0:
            report.add_issue(
                rule_id="LINT007_UNCLOSED_FORMATTING",
                severity="ERROR",
                slide_idx=slide_idx,
                archetype=archetype,
                message=f"Unclosed code backtick '`' detected in {field_label}: '{txt[:45]}...'.",
                suggestion="Ensure all monospace spans have opening and closing backticks (e.g. '`code`').",
            )

        if txt.count("<u>") != txt.count("</u>"):
            report.add_issue(
                rule_id="LINT007_UNCLOSED_FORMATTING",
                severity="ERROR",
                slide_idx=slide_idx,
                archetype=archetype,
                message=f"Unbalanced '<u>' underline tags detected in {field_label}.",
                suggestion="Ensure all <u> tags have matching </u> closures.",
            )

        # Single asterisk italic check (excluding *** and **)
        clean_for_italics = txt.replace("***", "").replace("**", "")
        if clean_for_italics.count("*") % 2 != 0:
            report.add_issue(
                rule_id="LINT007_UNCLOSED_FORMATTING",
                severity="ERROR",
                slide_idx=slide_idx,
                archetype=archetype,
                message=f"Unclosed markdown italic marker '*' detected in {field_label}: '{txt[:45]}...'.",
                suggestion="Ensure all single asterisk italic spans are closed (e.g. '*italic text*').",
            )

        # 2. Incompatible Block Markdown (Zero Unrenderable Punctuation)
        m_link = _MD_LINK_RE.search(txt)
        if m_link:
            report.add_issue(
                rule_id="LINT007_UNRENDERABLE_MARKDOWN",
                severity="ERROR",
                slide_idx=slide_idx,
                archetype=archetype,
                message=f"Raw markdown link syntax detected in {field_label}: '{m_link.group(0)}'.",
                suggestion="PowerPoint shapes do not render markdown link syntax. Use plain display text.",
            )

        m_hdr = _MD_HEADER_RE.search(txt)
        if m_hdr:
            report.add_issue(
                rule_id="LINT007_UNRENDERABLE_MARKDOWN",
                severity="ERROR",
                slide_idx=slide_idx,
                archetype=archetype,
                message=f"Raw markdown header '#' detected in {field_label}: '{m_hdr.group(0).strip()}'.",
                suggestion="Remove markdown header hashes. Presentation typography ramp defines visual hierarchy.",
            )

        m_st = _MD_STRIKE_RE.search(txt)
        if m_st:
            report.add_issue(
                rule_id="LINT007_UNRENDERABLE_MARKDOWN",
                severity="ERROR",
                slide_idx=slide_idx,
                archetype=archetype,
                message=f"Raw markdown strikethrough detected in {field_label}: '{m_st.group(0)}'.",
                suggestion="Remove markdown tildes '~~'.",
            )

        if is_bullet:
            m_lead = _MD_LEADING_BULLET_RE.match(txt)
            if m_lead:
                report.add_issue(
                    rule_id="LINT007_REDUNDANT_BULLET_GLYPH",
                    severity="ERROR",
                    slide_idx=slide_idx,
                    archetype=archetype,
                    message=f"Redundant leading bullet marker ('{m_lead.group(0).strip()}') in {field_label}.",
                    suggestion="PowerPoint automatically generates native vector bullets. Omit manual leading dashes, asterisks, or bullets.",
                )

        # 3. Emphasis Density Guardrail (Executive Scannability)
        if len(txt) > 85:
            bold_matches = _MD_BOLD_RE.findall(txt)
            bold_chars = sum(len(m) for m in bold_matches)
            if bold_chars / len(txt) > 0.85:
                report.add_issue(
                    rule_id="LINT007_EXCESSIVE_EMPHASIS",
                    severity="WARNING",
                    slide_idx=slide_idx,
                    archetype=archetype,
                    message=f"Over 85% of text in {field_label} is bolded ({bold_chars}/{len(txt)} chars).",
                    suggestion="Reserve bolding for lead-in anchors (first 2-4 words) or key metrics to preserve executive scannability.",
                )

    # 1. Non-bullet scalar fields on the slide
    scalar_fields = [
        ("title", slide.get("title")),
        ("action_title", slide.get("action_title")),
        ("subtitle", slide.get("subtitle")),
        ("context", slide.get("context")),
        ("tracker", slide.get("tracker")),
        ("takeaway", slide.get("takeaway")),
        ("so_what", slide.get("so_what")),
        ("decision_lever", slide.get("decision_lever")),
        ("source", slide.get("source")),
        ("footnote", slide.get("footnote")),
        ("notice", slide.get("notice")),
        ("hero_stat", slide.get("hero_stat")),
        ("hero_stat_label", slide.get("hero_stat_label")),
        ("hero_stat_subtext", slide.get("hero_stat_subtext")),
        ("left_eyebrow", slide.get("left_eyebrow")),
        ("left_title", slide.get("left_title")),
        ("left_subtitle", slide.get("left_subtitle")),
        ("right_eyebrow", slide.get("right_eyebrow")),
        ("right_title", slide.get("right_title")),
        ("right_subtitle", slide.get("right_subtitle")),
        ("center_label", slide.get("center_label")),
        ("center_title", slide.get("center_title")),
        ("center_subtitle", slide.get("center_subtitle")),
        ("badge", slide.get("badge")),
        ("metric_badge", slide.get("metric_badge")),
        ("category_tag", slide.get("category_tag")),
        ("eyebrow", slide.get("eyebrow")),
    ]

    for field_name, f_val in scalar_fields:
        _validate_text_spans(f"'{field_name}'", f_val, is_bullet=False)

    # 2. Check nested container items (blocks, cards, steps, horizons, columns, metrics, stats)
    for container_key in ("blocks", "cards", "steps", "horizons", "columns", "items", "metrics", "stats"):
        containers = slide.get(container_key)
        if isinstance(containers, list):
            for c_idx, container in enumerate(containers, start=1):
                if isinstance(container, dict):
                    c_label = container.get("title") or container.get("label") or f"{container_key}[{c_idx}]"
                    for prop in (
                        "title", "label", "name", "header", "eyebrow", "badge",
                        "metric_badge", "category_tag", "category", "timeframe",
                        "phase", "description", "subtext", "caption", "value",
                        "stat", "stat_label"
                    ):
                        val = container.get(prop)
                        if isinstance(val, str):
                            _validate_text_spans(f"{container_key} '{c_label}' -> {prop}", val, is_bullet=False)

    # 3. Check table headers & cells
    table_data = slide.get("table")
    if isinstance(table_data, dict):
        headers = table_data.get("headers")
        if isinstance(headers, list):
            for h_idx, h_text in enumerate(headers, start=1):
                if isinstance(h_text, str):
                    _validate_text_spans(f"table header #{h_idx}", h_text, is_bullet=False)
        rows = table_data.get("rows")
        if isinstance(rows, list):
            for r_idx, row in enumerate(rows, start=1):
                if isinstance(row, list):
                    for cell_idx, cell in enumerate(row, start=1):
                        if isinstance(cell, str):
                            _validate_text_spans(f"table row {r_idx} cell {cell_idx}", cell, is_bullet=False)

    # 4. Bullet & List items
    bullet_items: List[Tuple[str, str]] = []
    for b_key in ("bullets", "initiatives", "left_items", "right_items"):
        val = slide.get(b_key)
        if isinstance(val, list):
            for itm in val:
                if isinstance(itm, str):
                    bullet_items.append((f"'{b_key}' item", itm))

    for c_key in ("blocks", "cards", "steps", "horizons", "columns"):
        containers = slide.get(c_key)
        if isinstance(containers, list):
            for c_idx, container in enumerate(containers, start=1):
                if isinstance(container, dict):
                    c_label = container.get("title") or f"{c_key}[{c_idx}]"
                    for sub_b in ("bullets", "initiatives", "items"):
                        sub_val = container.get(sub_b)
                        if isinstance(sub_val, list):
                            for itm in sub_val:
                                if isinstance(itm, str):
                                    bullet_items.append((f"{c_key} '{c_label}' -> {sub_b}", itm))

    items_field = slide.get("items")
    if isinstance(items_field, list):
        for itm in items_field:
            if isinstance(itm, str):
                bullet_items.append(("item", itm))

    for field_label, bullet in bullet_items:
        _validate_text_spans(field_label, bullet, is_bullet=True)


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
    # Deck-Level Design Contract Verification
    # -------------------------------------------------------------------------
    deck_contract_raw = data.get("design_contract")
    if not deck_contract_raw and isinstance(data.get("metadata"), dict):
        deck_contract_raw = data.get("metadata", {}).get("design_contract")

    if deck_contract_raw:
        if not _normalize_contract(deck_contract_raw):
            report.add_issue(
                rule_id="LINT006_DESIGN_CONTRACT",
                severity="ERROR",
                slide_idx=0,
                archetype="deck",
                message=f"Unrecognized deck-level design_contract: '{deck_contract_raw}'.",
                suggestion=f"Supported contracts: {', '.join(sorted(VALID_DESIGN_CONTRACTS))}.",
            )

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
                if not isinstance(bullet, str):
                    continue
                b_str = bullet.strip()
                if not b_str:
                    continue
                has_lead_in = bool(_BOLD_LEAD_IN_RE.match(b_str))
                has_inline_bold = bool(_BOLD_INLINE_RE.search(b_str))
                if not (has_lead_in or has_inline_bold):
                    report.add_issue(
                        rule_id="LINT003_SCANNABLE_BOLD",
                        severity="WARNING",
                        slide_idx=idx,
                        archetype=arch,
                        message=f"Bullet lacks scannable bold text: '{b_str[:42]}...'",
                        suggestion="Begin with '**Anchor:** text' or embed '**2-3 bold keywords**' to facilitate executive F-pattern scanning.",
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

        # ---------------------------------------------------------------------
        # Rule LINT006: Redundant Card Badging / Badge Crutch
        # ---------------------------------------------------------------------
        for item_idx, itm in enumerate(slide.get("items") or []):
            if isinstance(itm, dict) and itm.get("badge"):
                badge_val = str(itm.get("badge", "")).strip().upper()
                has_widget = bool(itm.get("widget"))
                is_crutch = has_widget or any(k in badge_val for k in ("PILLAR", "STEP", "STREAM", "CATEGORY", "AUDIT", "PIPELINE"))
                if is_crutch:
                    report.add_issue(
                        rule_id="LINT006_CARD_BADGE_CRUTCH",
                        severity="WARNING",
                        slide_idx=idx,
                        archetype=arch,
                        message=f"Redundant badge '{itm.get('badge')}' on card {item_idx + 1}.",
                        suggestion="Remove redundant card badges. Cards with internal widgets or numbered headers must not use decorative corner badge pills.",
                    )

        # ---------------------------------------------------------------------
        # Rule LINT006: Design Contract Enforcement (Modular Ceilings)
        # ---------------------------------------------------------------------
        slide_contract_raw = slide.get("design_contract")
        if slide_contract_raw is not None:
            contract_id = _normalize_contract(slide_contract_raw)
            if not contract_id:
                report.add_issue(
                    rule_id="LINT006_DESIGN_CONTRACT",
                    severity="ERROR",
                    slide_idx=idx,
                    archetype=arch,
                    message=f"Unrecognized slide-level design_contract: '{slide_contract_raw}'.",
                    suggestion=f"Supported contracts: {', '.join(sorted(VALID_DESIGN_CONTRACTS))}.",
                )
            elif arch not in ("cover", "hero_cover", "chapter_divider", "thank_you"):
                if contract_id == "executive_csuite":
                    _lint_executive_csuite_contract(slide, idx, arch, title, report)
                elif contract_id == "strategic_tradeoff":
                    _lint_strategic_tradeoff_contract(slide, idx, arch, title, report)
                elif contract_id == "technical_architecture":
                    _lint_technical_architecture_contract(slide, idx, arch, title, report)
        elif deck_contract_raw is not None:
            contract_id = _normalize_contract(deck_contract_raw)
            if contract_id and arch not in ("cover", "hero_cover", "chapter_divider", "thank_you"):
                if contract_id == "executive_csuite":
                    _lint_executive_csuite_contract(slide, idx, arch, title, report)
                elif contract_id == "strategic_tradeoff":
                    _lint_strategic_tradeoff_contract(slide, idx, arch, title, report)
                elif contract_id == "technical_architecture":
                    _lint_technical_architecture_contract(slide, idx, arch, title, report)

        # ---------------------------------------------------------------------
        # Rule LINT007: Raw Markdown Syntax Guardrail
        # ---------------------------------------------------------------------
        _lint_markdown_syntax(slide, idx, arch, report)

    if strict and report.warning_count > 0:
        report.passed = False

    return report
