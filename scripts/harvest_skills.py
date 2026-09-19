#!/usr/bin/env python3
"""
harvest_skills.py — Universal Multi-Project Skill Harvester & AGENTS.md Indexer

Discovers skills across local workspace, user global config, and system directories,
categorizes them into 5 standardized tracks, and generates/stamps a compact
pre-flight index (<= 80 lines) into AGENTS.md.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DiscoveredSkill:
    name: str
    description: str
    source_path: Path
    relative_link: str
    origin: str  # 'local', 'global', 'plugin', 'builtin'
    target_role: str = ""
    when_to_check: str = ""
    key_protocol: str = ""
    track: str = "Track D: Administrative & Subagent Delegation"


TRACK_MAPPING = {
    "enterprise-bench-ops": "Track A: Operational Workflows (Building Deliverables)",
    "enterprise-bench-dev": "Track B: Platform & Engine Engineering (Extending Infrastructure)",
    "local-app-preview": "Track C: Desktop Review & Fast Turnaround (Local App Launching)",
    "setup-agents": "Track D: Administrative, Checkpoint & Subagent Delegation",
    "session-checkpoint": "Track D: Administrative, Checkpoint & Subagent Delegation",
    "presentation-maker": "Track E: Presentation & Visual Design Systems",
    "slide-image-prompter": "Track E: Presentation & Visual Design Systems",
}

DEFAULT_METADATA = {
    "enterprise-bench-ops": {
        "role": "Deliverable Producer, Engagement PMO, Solutions Consultant.",
        "when": "Whenever tasked with stamping contracts, drafting FSD/TSD specs, generating status decks, filling BAST milestones, or running the bench CLI.",
        "protocol": "Enforces stage-gate validity via LIFECYCLE.md and requires locating the 38 production-ready master templates in clean_workspace/ via CATALOG.md before generation.",
    },
    "enterprise-bench-dev": {
        "role": "Core Platform Engineer, Engine Developer, Python Maintainer.",
        "when": "Whenever tasked with modifying src/docx_engine (OpenXML tables, Jinja2 stamping), src/ppt_engine (visual cards, collision logic), src/xlsx_engine (calculators, S-curves), src/core (schemas, PII regex), or src/cli.py.",
        "protocol": "Strictly enforces the ZERO INTERMEDIATE UNIT TESTING guardrail, environment execution via uv, and architectural separation of concerns.",
    },
    "local-app-preview": {
        "role": "Review Coordinator, Enterprise Consultant, Pair Programming Assistant.",
        "when": "Whenever tasked with opening or previewing Word (.docx), Excel (.xlsx), PowerPoint (.pptx), PDF, or diagram (.drawio, .png) deliverables on the user's local machine, or proactively suggesting desktop reviews to accelerate feedback.",
        "protocol": "Uses open -a and osascript to focus application windows without blocking subshells.",
    },
    "setup-agents": {
        "role": "Repository Administrator, Multi-Agent Architect, Pair Programming Coordinator.",
        "when": "Initializing or updating repository operating contracts, harvesting skills, setting up subagent delegation patterns, or maintaining AGENTS.md.",
        "protocol": "Enforces <= 80 line budget for pre-flight indexes, cognitive separation of concerns, and universal discovery hierarchy.",
    },
    "session-checkpoint": {
        "role": "Session Architect, Cognitive Phase-Shift Gatekeeper.",
        "when": "Wrapping up milestones, finishing intensive research/brainstorming, or when task complexity warrants clean-slate execution across files.",
        "protocol": "Generates copy-paste resume prompt adhering strictly to the standard session handover schema.",
    },
    "presentation-maker": {
        "role": "Slide Designer, Deck Automation Engineer.",
        "when": "Building, styling, or automating PowerPoint decks (python-pptx). Provides consulting frameworks (McKinsey/BCG), executive visual card archetypes, typography rules, and collision prevention.",
        "protocol": "Enforces sharp top stripes on containers, unified title/subtitle flow, and balanced multi-column aspect ratios.",
    },
    "slide-image-prompter": {
        "role": "Visual Prompt Engineer, Presentation Concept Designer.",
        "when": "Generating high-fidelity AI visual prompts for presentation backgrounds, custom infographics, or full-slide concept diagrams.",
        "protocol": "Specifies aspect ratio, visual weight, negative space, and lighting conditions.",
    },
}


def parse_frontmatter(content: str) -> Dict[str, str]:
    """Extract YAML frontmatter between --- markers."""
    meta = {}
    if not content.startswith("---"):
        return meta
    parts = content.split("---", 2)
    if len(parts) < 3:
        return meta
    yaml_block = parts[1]
    current_key = None
    accumulated_lines = []

    for raw_line in yaml_block.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line and not raw_line.startswith(" "):
            if current_key and accumulated_lines:
                meta[current_key] = " ".join(accumulated_lines).strip()
                accumulated_lines = []
            key, val = line.split(":", 1)
            current_key = key.strip()
            val = val.strip()
            if val in (">", ">-", "|", "|-"):
                accumulated_lines = []
            elif val:
                accumulated_lines.append(val.strip("\"'"))
        elif current_key:
            accumulated_lines.append(line.strip("\"'"))

    if current_key and accumulated_lines:
        meta[current_key] = " ".join(accumulated_lines).strip()

    return meta


def discover_skills(workspace_root: Path, include_all_global: bool = False) -> Dict[str, DiscoveredSkill]:
    """Discover skills across local, global, plugin, and builtin paths."""
    skills: Dict[str, DiscoveredSkill] = {}

    search_dirs = [
        # 1. Local Workspace (Highest Priority)
        ("local", workspace_root / ".agents" / "skills"),
        ("local", workspace_root / "skills"),
        # 2. User Global
        ("global", Path.home() / ".gemini" / "config" / "skills"),
    ]

    if include_all_global:
        search_dirs.append(("builtin", Path.home() / ".gemini" / "antigravity" / "builtin" / "skills"))
        plugins_dir = Path.home() / ".gemini" / "config" / "plugins"
        if plugins_dir.exists():
            for plugin_skill in plugins_dir.glob("**/skills/*"):
                if (plugin_skill / "SKILL.md").is_file():
                    search_dirs.append(("plugin", plugin_skill.parent))

    for origin, base_dir in search_dirs:
        if not base_dir.exists():
            continue
        for skill_dir in base_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                continue

            skill_name = skill_dir.name
            real_skill_file = skill_file.resolve()

            if skill_name in skills:
                continue

            # If global/plugin and not in DEFAULT_METADATA and not include_all_global, skip non-workspace skills
            if origin != "local" and not include_all_global and skill_name not in DEFAULT_METADATA:
                continue

            try:
                content = skill_file.read_text(encoding="utf-8")
            except Exception:
                continue

            meta = parse_frontmatter(content)
            name = meta.get("name", skill_name)
            desc = meta.get("description", "").strip()

            if origin == "local":
                rel_link = f"skills/{name}/SKILL.md"
            else:
                rel_link = f"~/{real_skill_file.relative_to(Path.home())}"

            enriched = DEFAULT_METADATA.get(name, {})
            role = enriched.get("role", "Specialized Agent Workflow")
            when = enriched.get("when", desc or "When tasked with workflows defined in this skill.")
            protocol = enriched.get("protocol", "Follow procedures outlined in skill specification.")
            track = TRACK_MAPPING.get(name, "Track D: Administrative, Checkpoint & Subagent Delegation")

            skills[name] = DiscoveredSkill(
                name=name,
                description=desc,
                source_path=real_skill_file,
                relative_link=rel_link,
                origin=origin,
                target_role=role,
                when_to_check=when,
                key_protocol=protocol,
                track=track,
            )

    return skills


def render_skills_markdown(skills: Dict[str, DiscoveredSkill]) -> str:
    """Render high-density markdown pre-flight index conforming strictly to <= 80 line budget."""
    lines = [
        "## 🧰 MANDATORY PRE-FLIGHT: SPECIALIZED LOCAL & GLOBAL SKILLS",
        "",
        "> **DIRECTIVE: REVIEW SPECIALIZED SKILLS BEFORE ACTING ON CREATIVE CAPACITY**",
        "",
        "Before generating code, authoring new deliverables, designing presentations, or creating custom templates from scratch, **agents must check and activate existing specialized skills**. Primary skills index (`.agents/skills/`, symlinked via `skills/` and `.skills/`, plus global admin skills):",
        "",
    ]

    tracks_order = [
        "Track A: Operational Workflows (Building Deliverables with Existing Tools)",
        "Track B: Platform & Engine Engineering (Extending Infrastructure)",
        "Track C: Desktop Review & Fast Turnaround (Local App Launching)",
        "Track D: Administrative, Checkpoint & Subagent Delegation",
        "Track E: Presentation & Visual Design Systems",
    ]

    grouped: Dict[str, List[DiscoveredSkill]] = {
        "Track A: Operational Workflows (Building Deliverables with Existing Tools)": [],
        "Track B: Platform & Engine Engineering (Extending Infrastructure)": [],
        "Track C: Desktop Review & Fast Turnaround (Local App Launching)": [],
        "Track D: Administrative, Checkpoint & Subagent Delegation": [],
        "Track E: Presentation & Visual Design Systems": [],
    }

    for skill in skills.values():
        if "Track A" in skill.track:
            grouped["Track A: Operational Workflows (Building Deliverables with Existing Tools)"].append(skill)
        elif "Track B" in skill.track:
            grouped["Track B: Platform & Engine Engineering (Extending Infrastructure)"].append(skill)
        elif "Track C" in skill.track:
            grouped["Track C: Desktop Review & Fast Turnaround (Local App Launching)"].append(skill)
        elif "Track E" in skill.track or "Visual" in skill.track:
            grouped["Track E: Presentation & Visual Design Systems"].append(skill)
        else:
            grouped["Track D: Administrative, Checkpoint & Subagent Delegation"].append(skill)

    skill_counter = 1
    for track in tracks_order:
        items = grouped[track]
        if not items:
            continue
        lines.append(f"#### {track}")
        for item in sorted(items, key=lambda x: x.name):
            lines.append(f"{skill_counter}. **`{item.name}`** ([`{item.relative_link}`]({item.relative_link})):")
            lines.append(f"   - **Target Role:** {item.target_role}")
            lines.append(f"   - **When to check:** {item.when_to_check}")
            lines.append(f"   - **Key Protocol:** {item.key_protocol}")
            skill_counter += 1
        lines.append("")

    lines.append(
        "**First Action Protocol:** Identify whether your goal is **Operational (Track A)**, **Development (Track B)**, **Review & Preview (Track C)**, **Administrative (Track D)**, or **Design (Track E)** and **inspect the corresponding skill file first** before proceeding."
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Harvest skills and update AGENTS.md")
    parser.add_argument("--dry-run", action="store_true", help="Print discovered skills and formatted markdown")
    parser.add_argument("--stamp", action="store_true", help="Update AGENTS.md in-place")
    parser.add_argument("--all", action="store_true", help="Include all global plugins and builtin skills")
    args = parser.parse_args()

    workspace_root = Path.cwd()
    skills = discover_skills(workspace_root, include_all_global=args.all)

    md_output = render_skills_markdown(skills)

    if args.dry_run or not args.stamp:
        print(f"Discovered {len(skills)} skills across local and global environments:")
        for name, sk in sorted(skills.items()):
            print(f" - [{sk.origin.upper()}] {name} ({sk.track})")
        print("\n--- GENERATED MARKDOWN SNIPPET ---")
        print(md_output)
        line_count = len(md_output.splitlines())
        print(f"--- END SNIPPET ({line_count} lines) ---")
        return

    agents_path = workspace_root / "AGENTS.md"
    if not agents_path.is_file():
        print(f"Error: {agents_path} not found.", file=sys.stderr)
        sys.exit(1)

    content = agents_path.read_text(encoding="utf-8")
    pattern = r"(## 🧰 MANDATORY PRE-FLIGHT:.*?\n)(?=## 🏛 Repository Conventions)"
    if re.search(pattern, content, flags=re.DOTALL):
        new_content = re.sub(pattern, md_output + "\n\n---\n\n", content, flags=re.DOTALL)
        agents_path.write_text(new_content, encoding="utf-8")
        print(f"Successfully stamped updated pre-flight skills into {agents_path}")
    else:
        print("Warning: Could not locate standard pre-flight header in AGENTS.md", file=sys.stderr)


if __name__ == "__main__":
    main()
