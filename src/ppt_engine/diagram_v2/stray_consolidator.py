"""
Diagram Engine V2 - Model 2.1 Stray Visualization Harvester & Theme Consolidator
================================================================================
Discovers scattered single-slide visualization artifacts (.yaml, .pptx, .png, .svg, .drawio),
auto-clusters them by domain theme using lexical + AST subgraph inclusion V(A) ⊂ V(B),
detects evolutionary lineage (LATEST / expanded vs. OUTDATED / unexpanded), renames files
with LATEST_ / OUTDATED_ prefixes, merges slides losslessly into 1 PPTX per domain theme,
archives standalone PPTXs to .archive/strays/, and maintains STRAY_BACKLOG.md.
"""

from __future__ import annotations

import copy
import datetime
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from pptx import Presentation
from pptx.util import Inches

from src.ppt_engine.diagram_v2.compiler import compile_diagram, load_diagram_spec
from src.ppt_engine.diagram_v2.models import DiagramSpec, DeckHeaderContract
from src.ppt_engine.diagram_v2.auditor import AuditIssue


STOPWORDS: Set[str] = {
    "diagram", "diagrams", "v1", "v2", "v3", "expanded", "unexpanded",
    "proposed", "architecture", "system", "flow", "layout", "layout1",
    "layout2", "layout3", "layout4", "layout5", "baseline", "clean",
    "adaptive", "heights", "vertical", "balance", "dual", "column",
    "device", "linear", "highway", "test", "draft", "final", "latest",
    "outdated", "slide", "deck", "visual", "visuals", "spec",
}

EVOLUTION_EXPANDED_CUES: Set[str] = {"expanded", "interwoven", "full", "complete", "v2", "v3", "final"}
EVOLUTION_UNEXPANDED_CUES: Set[str] = {
    "unexpanded", "baseline", "simple", "v1", "initial", "draft",
    "layout1", "layout2", "layout3", "layout4", "layout5",
}

IGNORED_DIRS: Set[str] = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".archive", "bundles", "icon_cache", ".gemini", "doc_files",
}


_LIFECYCLE_PREFIX_RE = re.compile(r"^(LATEST|OUTDATED)_(.+)$", flags=re.IGNORECASE)
_TOKEN_SPLIT_RE = re.compile(r"[^a-zA-Z0-9]+")
_LAYOUT_TOKEN_RE = re.compile(r"^layout\d+$")
_ARCH_SUFFIX_RE = re.compile(r"_(architecture|diagram|visuals|slide|visualization)$")
_LAYOUT_SEARCH_RE = re.compile(r"layout\d+")
_SLUG_CLEAN_RE = re.compile(r"[^a-zA-Z0-9_-]+")
_SLUG_PREFIX_RE = re.compile(r"^(proposed|draft|final)_+")
_SLUG_SUFFIX_RE = re.compile(r"_(expanded|unexpanded|architecture|layout\d+.*|v\d+|draft|covers|visualization)$")
_ARCHIVE_DIR_SUFFIX_RE = re.compile(r"_(temp|presentations|diagrams_v2)$", flags=re.IGNORECASE)


def _safe_mtime(p: Path) -> float:
    """Return file mtime with a single stat syscall, or 0.0 if missing."""
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def strip_lifecycle_prefix(stem: str) -> Tuple[str, Optional[str]]:
    """Strip leading LATEST_ or OUTDATED_ prefix from a filename stem."""
    m = _LIFECYCLE_PREFIX_RE.match(stem)
    if m:
        return m.group(2), m.group(1).upper()
    return stem, None


def normalize_stem_key(stem: str) -> str:
    """Normalize stem for grouping companion files (.yaml, .pptx, .png, .svg, .drawio)."""
    clean, _ = strip_lifecycle_prefix(stem)
    # Strip trailing _architecture if a shorter YAML stem exists
    return clean.lower()


def extract_domain_tokens(text: str) -> Set[str]:
    """Tokenize identifier/title into meaningful domain keywords."""
    clean, _ = strip_lifecycle_prefix(text)
    raw_tokens = _TOKEN_SPLIT_RE.split(clean.lower())
    return {
        t for t in raw_tokens
        if len(t) >= 3 and t not in STOPWORDS and not _LAYOUT_TOKEN_RE.match(t)
    }


@dataclass
class VisualizationPod:
    """Represents a single logical visualization and its companion file artifacts."""
    base_stem: str
    yaml_path: Optional[Path] = None
    pptx_paths: List[Path] = field(default_factory=list)
    png_path: Optional[Path] = None
    svg_path: Optional[Path] = None
    drawio_path: Optional[Path] = None
    spec: Optional[DiagramSpec] = None
    node_ids: Set[str] = field(default_factory=set)
    container_ids: Set[str] = field(default_factory=set)
    domain_tokens: Set[str] = field(default_factory=set)
    explicit_bundle: Optional[str] = None
    inferred_theme: str = "unassigned"
    status: str = "LATEST"  # "LATEST" | "OUTDATED"
    variant_kind: str = "standard"  # "expanded" | "unexpanded" | "experiment" | "standard"
    superseded_by: Optional[str] = None
    mtime: float = 0.0
    is_experiment_dir: bool = False

    @property
    def primary_pptx(self) -> Optional[Path]:
        if not self.pptx_paths:
            return None
        return max(self.pptx_paths, key=_safe_mtime)

    @property
    def all_files(self) -> List[Path]:
        files: List[Path] = []
        if self.yaml_path:
            files.append(self.yaml_path)
        files.extend(self.pptx_paths)
        if self.png_path:
            files.append(self.png_path)
        if self.svg_path:
            files.append(self.svg_path)
        if self.drawio_path:
            files.append(self.drawio_path)
        return [f for f in files if f.exists()]

    @property
    def complexity_score(self) -> int:
        """Graph complexity score |V| + |C| + |E| + expanded cue bonus."""
        base = len(self.node_ids) * 3 + len(self.container_ids) * 2
        if self.spec:
            base += len(self.spec.flows)
        stem_lower = self.base_stem.lower()
        if any(cue in stem_lower for cue in EVOLUTION_EXPANDED_CUES):
            base += 15
        if self.is_experiment_dir or any(cue in stem_lower for cue in EVOLUTION_UNEXPANDED_CUES):
            base -= 10
        return base


@dataclass
class ThemeCluster:
    """Domain theme cluster grouping related visualization pods."""
    theme_slug: str
    pods: List[VisualizationPod] = field(default_factory=list)
    bundle_pptx_path: Optional[Path] = None
    confidence: str = "HIGH"  # "HIGH" | "NEEDS_CONFIRMATION"
    lineage_summary: str = ""


@dataclass
class ConsolidationReport:
    """Result summary from scanning or consolidating stray visualizations."""
    workspace: Path
    clusters: List[ThemeCluster] = field(default_factory=list)
    renamed_files: List[Tuple[Path, Path]] = field(default_factory=list)
    archived_pptx_files: List[Tuple[Path, Path]] = field(default_factory=list)
    bundle_decks: List[Path] = field(default_factory=list)
    header_issues: List[AuditIssue] = field(default_factory=list)
    backlog_path: Optional[Path] = None


def validate_bundle_headers(specs: List[DiagramSpec]) -> List[AuditIssue]:
    """
    Verifies that all constituent slides in a multi-slide presentation share
    identical header coordinates under DeckHeaderContract:
    - Delta y_stripes <= 0.005 in
    - Delta y_title <= 0.005 in
    - Delta x_title <= 0.005 in
    Emits DECK_HEADER_DRIFT (CRITICAL) if any slide deviates.
    """
    issues: List[AuditIssue] = []

    header_specs = [s for s in specs if s.header and s.header.show]
    if len(header_specs) <= 1:
        return issues

    slide_coords: List[Dict[str, Any]] = []
    for s in header_specs:
        h = s.header
        y_stripes = h.y if h.y is not None else DeckHeaderContract.STRIPES_TOP_IN
        x_base = h.x if h.x is not None else DeckHeaderContract.STRIPES_LEFT_IN
        y_title = y_stripes - 0.050
        x_title = (x_base + 0.250) if h.brand_stripes else x_base
        slide_coords.append({
            "spec": s,
            "y_stripes": y_stripes,
            "x_base": x_base,
            "y_title": y_title,
            "x_title": x_title,
        })

    y_stripes_vals = [sc["y_stripes"] for sc in slide_coords]
    y_title_vals = [sc["y_title"] for sc in slide_coords]
    x_title_vals = [sc["x_title"] for sc in slide_coords]

    delta_y_stripes = max(y_stripes_vals) - min(y_stripes_vals)
    delta_y_title = max(y_title_vals) - min(y_title_vals)
    delta_x_title = max(x_title_vals) - min(x_title_vals)

    tolerance = 0.005

    if delta_y_stripes > tolerance or delta_y_title > tolerance or delta_x_title > tolerance:
        ref_y_stripes = DeckHeaderContract.STRIPES_TOP_IN
        ref_y_title = DeckHeaderContract.TITLE_TOP_IN
        min_ys = min(y_stripes_vals)
        min_yt = min(y_title_vals)
        min_xt = min(x_title_vals)

        for sc in slide_coords:
            s = sc["spec"]
            ys = sc["y_stripes"]
            yt = sc["y_title"]
            xt = sc["x_title"]

            drift_y_stripes = abs(ys - ref_y_stripes)
            drift_y_title = abs(yt - ref_y_title)
            spread_ys = abs(ys - min_ys)
            spread_yt = abs(yt - min_yt)
            spread_xt = abs(xt - min_xt)

            if (spread_ys > tolerance or spread_yt > tolerance or spread_xt > tolerance or
                drift_y_stripes > tolerance or drift_y_title > tolerance):
                issues.append(AuditIssue(
                    severity="CRITICAL",
                    category="DECK_HEADER_DRIFT",
                    element_id=s.id,
                    description=(
                        f"Multi-slide deck header drift detected on slide '{s.id}': "
                        f"y_stripes={ys:.3f}in, y_title={yt:.3f}in, x_title={xt:.3f}in "
                        f"(bundle spread: Δy_stripes={delta_y_stripes:.3f}in, Δy_title={delta_y_title:.3f}in, Δx_title={delta_x_title:.3f}in "
                        f"exceeds tolerance of {tolerance:.3f}in)."
                    ),
                    suggested_fix=(
                        f"Standardize slide '{s.id}' header coordinates to DeckHeaderContract "
                        f"(stripes top={DeckHeaderContract.STRIPES_TOP_IN:.3f}in, left={DeckHeaderContract.STRIPES_LEFT_IN:.3f}in; "
                        f"title top={DeckHeaderContract.TITLE_TOP_IN:.3f}in) across all constituent deck slides."
                    ),
                ))

    return issues


def _is_single_slide_visualization_pptx(pptx_path: Path) -> bool:
    """Verify whether a PPTX is a 1-slide visualization (rather than a multi-slide consulting deck)."""
    try:
        prs = Presentation(str(pptx_path))
        return len(prs.slides) <= 2
    except Exception:
        return False


def _rel_parts_lower(p: Path, workspace: Optional[Path] = None) -> Tuple[str, ...]:
    """Extract lowercase path components relative to workspace when possible."""
    if workspace is not None:
        try:
            return tuple(part.lower() for part in p.relative_to(workspace).parts)
        except ValueError:
            pass
    return tuple(part.lower() for part in p.parts)


def _is_ignored_path(p: Path, workspace: Optional[Path] = None) -> bool:
    for part_l in _rel_parts_lower(p, workspace):
        if part_l in IGNORED_DIRS or part_l.endswith("_archive") or part_l == "archive":
            return True
    return False


def scan_stray_visualizations(workspace: Path) -> List[VisualizationPod]:
    """Scan workspace for stray YAML, PPTX, PNG, SVG, and DrawIO visualization files."""
    pods_by_key: Dict[str, VisualizationPod] = {}

    candidate_files: List[Tuple[Path, Set[str]]] = []
    for p in workspace.rglob("*"):
        if p.name.startswith("~$") or p.name.startswith("."):
            continue
        if p.suffix.lower() not in {".yaml", ".yml", ".pptx", ".png", ".svg", ".drawio"}:
            continue
        if _is_ignored_path(p, workspace):
            continue
        if not p.is_file():
            continue
        candidate_files.append((p, set(_rel_parts_lower(p, workspace))))

    candidate_files.sort(key=lambda item: item[0])

    # First pass: register YAML diagram specs
    for p, rel_parts in candidate_files:
        if p.suffix.lower() not in {".yaml", ".yml"}:
            continue
        try:
            spec = load_diagram_spec(p)
        except Exception:
            continue

        clean_stem, _ = strip_lifecycle_prefix(p.stem)
        key = clean_stem.lower()
        pod = pods_by_key.get(key)
        if not pod:
            pod = VisualizationPod(base_stem=clean_stem)
            pods_by_key[key] = pod

        pod.yaml_path = p
        pod.spec = spec
        pod.is_experiment_dir = "experiments" in rel_parts
        pod.node_ids = {n.id.lower() for n in spec.nodes} | {n.title.lower() for n in spec.nodes}
        pod.container_ids = {c.id.lower() for c in spec.containers}
        pod.explicit_bundle = spec.bundle

        tokens = extract_domain_tokens(clean_stem)
        if spec.header and spec.header.action_title:
            tokens |= extract_domain_tokens(spec.header.action_title)
        for c in spec.containers:
            tokens |= extract_domain_tokens(c.id)
        pod.domain_tokens = tokens
        pod.mtime = max(pod.mtime, _safe_mtime(p))

    # Second pass: attach PPTX, PNG, SVG, DrawIO files
    for p, rel_parts in candidate_files:
        ext = p.suffix.lower()
        if ext in {".yaml", ".yml"}:
            continue
        # Skip standalone SVG icons in assets/
        if "assets" in rel_parts:
            continue

        clean_stem, _ = strip_lifecycle_prefix(p.stem)
        key = clean_stem.lower()

        # Fuzzy stem match if e.g. databricks_jobs_api_architecture.pptx matches databricks_jobs_api.yaml
        matched_key = key if key in pods_by_key else None
        is_exact_match = matched_key is not None
        if not matched_key:
            stripped_arch = _ARCH_SUFFIX_RE.sub("", key)
            if stripped_arch in pods_by_key:
                matched_key = stripped_arch

        if ext == ".pptx":
            if not _is_single_slide_visualization_pptx(p):
                continue

        if not matched_key:
            # Create standalone pod if it's a PPTX or sits in diagrams_v2 / visuals
            if ext == ".pptx" or "diagrams_v2" in rel_parts:
                matched_key = key
                is_exact_match = True
                pod = VisualizationPod(
                    base_stem=clean_stem,
                    domain_tokens=extract_domain_tokens(clean_stem),
                )
                # Also infer domain tokens from parent subdirectory name if inside doc_output/<topic>/
                if p.parent.name.lower() not in {"output", "presentations", "diagrams_v2", "temp", "doc_output"}:
                    pod.domain_tokens |= extract_domain_tokens(p.parent.name)
                pods_by_key[matched_key] = pod
            else:
                continue

        pod = pods_by_key[matched_key]
        file_mtime = _safe_mtime(p)
        pod.mtime = max(pod.mtime, file_mtime)
        if ext == ".pptx":
            pod.pptx_paths.append(p)
        elif ext == ".png":
            if pod.png_path is None or is_exact_match or file_mtime > _safe_mtime(pod.png_path):
                pod.png_path = p
        elif ext == ".svg":
            if pod.svg_path is None or is_exact_match or file_mtime > _safe_mtime(pod.svg_path):
                pod.svg_path = p
        elif ext == ".drawio":
            if pod.drawio_path is None or is_exact_match or file_mtime > _safe_mtime(pod.drawio_path):
                pod.drawio_path = p

    # Classify variant_kind for each pod
    for pod in pods_by_key.values():
        stem_l = pod.base_stem.lower()
        if pod.is_experiment_dir or _LAYOUT_SEARCH_RE.search(stem_l):
            pod.variant_kind = "unexpanded (experiment)"
        elif "draft" in stem_l or "covers" in stem_l:
            pod.variant_kind = "unexpanded (draft)"
        elif "expanded" in stem_l and "unexpanded" not in stem_l:
            pod.variant_kind = "expanded"
        elif "unexpanded" in stem_l or "visualization" in stem_l:
            pod.variant_kind = "unexpanded"
        else:
            pod.variant_kind = "standard"

    return list(pods_by_key.values())


def _pod_similarity(a: VisualizationPod, b: VisualizationPod) -> Tuple[float, bool]:
    """
    Calculate (affinity_score, is_subgraph_evolution) between two VisualizationPods.
    Uses lexical stem prefix + domain token overlap + YAML node AST intersection V(A) ∩ V(B).
    """
    if a.explicit_bundle and b.explicit_bundle:
        return (1.0 if a.explicit_bundle == b.explicit_bundle else 0.0), False

    stem_a = a.base_stem.lower().split("_", 1)[0]
    stem_b = b.base_stem.lower().split("_", 1)[0]
    same_leading_anchor = (len(stem_a) >= 3 and stem_a == stem_b and stem_a not in STOPWORDS)

    # Node AST overlap & Subgraph Inclusion V(A) ⊂ V(B)
    node_overlap = 0.0
    is_subgraph = False
    if a.node_ids and b.node_ids:
        inter = len(a.node_ids & b.node_ids)
        smaller = min(len(a.node_ids), len(b.node_ids))
        union = len(a.node_ids | b.node_ids)
        if smaller > 0:
            inclusion_ratio = inter / smaller
            if inclusion_ratio >= 0.65:
                is_subgraph = True
            node_overlap = inter / union if union > 0 else 0.0

    # Lexical token overlap
    lex_overlap = 0.0
    if a.domain_tokens and b.domain_tokens:
        inter_t = len(a.domain_tokens & b.domain_tokens)
        smaller_t = min(len(a.domain_tokens), len(b.domain_tokens))
        if smaller_t > 0:
            lex_overlap = inter_t / smaller_t

    score = max(node_overlap, lex_overlap * 0.85)
    if same_leading_anchor:
        score = max(score, 0.75)

    return score, is_subgraph


def _derive_theme_slug(pods: List[VisualizationPod]) -> str:
    """Derive a clean human-readable theme slug for a cluster of pods."""
    for p in pods:
        if p.explicit_bundle:
            return _SLUG_CLEAN_RE.sub("_", p.explicit_bundle.lower()).strip("_")

    # Check if there is a common leading token or shared domain token (e.g. cdsw / whitelist / databricks)
    token_counts: Dict[str, int] = {}
    for p in pods:
        for t in extract_domain_tokens(p.base_stem):
            token_counts[t] = token_counts.get(t, 0) + 1

    primary = max(pods, key=lambda x: (x.complexity_score, x.mtime))
    slug = primary.base_stem.lower()
    slug = _SLUG_PREFIX_RE.sub("", slug)
    slug = _SLUG_SUFFIX_RE.sub("", slug)
    if len(pods) > 1 and token_counts:
        top_token = max(token_counts.items(), key=lambda kv: (kv[1], len(kv[0])))[0]
        if top_token not in slug:
            slug = f"{top_token}_{slug}"
    return slug.strip("_") or "general_visuals"


def cluster_and_rank_pods(pods: List[VisualizationPod]) -> List[ThemeCluster]:
    """
    Group stray pods into Domain Theme clusters and rank LATEST vs OUTDATED within each cluster.
    Allows distinct expanded sibling architectures in the same theme (e.g. As-Is CDSW Expanded
    and To-Be AWS Lambda Expanded) to both carry LATEST status while marking unexpanded/draft/layout
    predecessors as OUTDATED.
    """
    if not pods:
        return []

    n = len(pods)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    for i in range(n):
        for j in range(i + 1, n):
            score, is_sub = _pod_similarity(pods[i], pods[j])
            if score >= 0.55 or is_sub:
                union(i, j)

    groups: Dict[int, List[VisualizationPod]] = {}
    for idx, pod in enumerate(pods):
        groups.setdefault(find(idx), []).append(pod)

    clusters: List[ThemeCluster] = []
    for group_pods in groups.values():
        theme_slug = _derive_theme_slug(group_pods)
        ranked = sorted(
            group_pods,
            key=lambda p: (
                not p.is_experiment_dir,
                "unexpanded" not in p.variant_kind,
                "expanded" in p.variant_kind,
                p.complexity_score,
                p.mtime,
            ),
            reverse=True,
        )

        winner = ranked[0]
        winner.inferred_theme = theme_slug
        winner.status = "LATEST"
        winner.superseded_by = None

        has_expanded = any(p.variant_kind == "expanded" for p in ranked)

        for other in ranked[1:]:
            other.inferred_theme = theme_slug
            # If this pod is ALSO an explicitly expanded architecture (e.g. As-Is cdsw_expanded vs To-Be aws_lambda_expanded),
            # keep it as LATEST alongside the winner; otherwise mark as OUTDATED evolution.
            if (
                has_expanded
                and other.variant_kind == "expanded"
                and not other.is_experiment_dir
                and other.base_stem.lower() != winner.base_stem.lower()
            ):
                other.status = "LATEST"
                other.superseded_by = None
            else:
                other.status = "OUTDATED"
                other.superseded_by = winner.base_stem

        confidence = "HIGH" if (len(ranked) > 1 or winner.explicit_bundle) else "NEEDS_CONFIRMATION"
        latest_names = [p.base_stem for p in ranked if p.status == "LATEST"]
        outdated_count = sum(1 for p in ranked if p.status == "OUTDATED")
        if len(ranked) > 1:
            lineage_summary = (
                f"LATEST: {', '.join(latest_names)} ⟵ "
                f"{outdated_count} outdated/unexpanded variant(s)"
            )
        else:
            lineage_summary = f"LATEST: {winner.base_stem} (singleton theme — confirm bundle tag by EOD)"

        clusters.append(
            ThemeCluster(
                theme_slug=theme_slug,
                pods=ranked,
                confidence=confidence,
                lineage_summary=lineage_summary,
            )
        )

    return sorted(clusters, key=lambda c: c.theme_slug)


def apply_lifecycle_prefixes(
    clusters: List[ThemeCluster],
    dry_run: bool = False,
) -> List[Tuple[Path, Path]]:
    """
    Rename visualization files on disk with LATEST_ or OUTDATED_ prefixes so the active
    file immediately stands out in Finder / IDE.
    """
    renames: List[Tuple[Path, Path]] = []

    def _rename_path(p: Path, prefix: str) -> Path:
        clean_stem, _ = strip_lifecycle_prefix(p.stem)
        target_name = f"{prefix}_{clean_stem}{p.suffix}"
        target_path = p.with_name(target_name)
        if target_path == p or not p.exists():
            return p
        renames.append((p, target_path))
        if not dry_run:
            p.replace(target_path)
            return target_path
        return p

    for cluster in clusters:
        for pod in cluster.pods:
            prefix = pod.status.upper()  # "LATEST" or "OUTDATED"
            if pod.yaml_path:
                pod.yaml_path = _rename_path(pod.yaml_path, prefix)
            if pod.png_path:
                pod.png_path = _rename_path(pod.png_path, prefix)
            if pod.svg_path:
                pod.svg_path = _rename_path(pod.svg_path, prefix)
            if pod.drawio_path:
                pod.drawio_path = _rename_path(pod.drawio_path, prefix)
            new_pptxs: List[Path] = []
            for pptx_p in pod.pptx_paths:
                new_pptxs.append(_rename_path(pptx_p, prefix))
            pod.pptx_paths = new_pptxs

    return renames



def _clone_slide_into_presentation(
    src_pptx: Path,
    dst_prs: Presentation,
    pod: VisualizationPod,
    slide_seq: int = 1,
) -> None:
    """
    Losslessly clone slide 1 shapes and image relationships from src_pptx into dst_prs.
    Re-packages media parts with unique PackURIs so multi-slide merges never collide on ppt/media/image1.png.
    """
    from pptx.opc.package import Part
    from pptx.opc.packuri import PackURI

    src_prs = Presentation(str(src_pptx))
    if len(src_prs.slides) == 0:
        return
    src_slide = src_prs.slides[0]
    blank_layout = dst_prs.slide_layouts[6] if len(dst_prs.slide_layouts) > 6 else dst_prs.slide_layouts[0]
    dst_slide = dst_prs.slides.add_slide(blank_layout)

    # Clear any default placeholders on blank layout
    for shp in list(dst_slide.shapes):
        sp_el = shp._element
        sp_el.getparent().remove(sp_el)

    # Map relationships (images, SVGs) from src_slide to dst_slide with unique media partnames
    rId_map: Dict[str, str] = {}
    media_counter = 1
    dst_pkg = dst_slide.part.package
    for rId, rel in src_slide.part.rels.items():
        if "notesSlide" in rel.reltype or "slideLayout" in rel.reltype:
            continue
        if rel.is_external:
            new_rId = dst_slide.part.rels.get_or_add_ext_rel(rel.reltype, rel.target_ref)
            rId_map[rId] = new_rId
        else:
            try:
                src_part = rel.target_part
                orig_name = Path(str(src_part.partname)).name
                unique_uri = PackURI(f"/ppt/media/s{slide_seq}_m{media_counter}_{orig_name}")
                media_counter += 1
                cloned_part = Part(
                    unique_uri,
                    src_part.content_type,
                    dst_pkg,
                    blob=src_part.blob,
                )
                new_rId = dst_slide.part.rels.get_or_add(rel.reltype, cloned_part)
                rId_map[rId] = new_rId
            except Exception:
                pass


    # Clone shapes in spTree
    dst_spTree = dst_slide.shapes._spTree
    for child in src_slide.shapes._spTree:
        tag_local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag_local in {"nvGrpSpPr", "grpSpPr"}:
            continue
        cloned_el = copy.deepcopy(child)
        # Remap any r:embed or r:link attributes
        for elem in cloned_el.iter():
            for attr_key, attr_val in list(elem.attrib.items()):
                if attr_val in rId_map and (attr_key.endswith("}embed") or attr_key.endswith("}link") or attr_key.endswith("}id")):
                    elem.set(attr_key, rId_map[attr_val])
        dst_spTree.append(cloned_el)

    # Stamp provenance in slide notes for traceability without polluting the visual canvas
    try:
        notes_slide = dst_slide.notes_slide
        yaml_ref = str(pod.yaml_path) if pod.yaml_path else "N/A"
        notes_slide.notes_text_frame.text = (
            f"[diagram_v2_bundle] status={pod.status} | theme={pod.inferred_theme} | "
            f"stem={pod.base_stem} | variant={pod.variant_kind} | yaml={yaml_ref}"
        )
    except Exception:
        pass


def merge_cluster_into_theme_pptx(
    cluster: ThemeCluster,
    bundles_dir: Path,
    temp_compile_dir: Path,
    dry_run: bool = False,
) -> Optional[Path]:
    """
    Merge all pods in a ThemeCluster into 1 consolidated PPTX:
    output/bundles/LATEST_<theme_slug>_visuals.pptx
    Places LATEST slide(s) first, followed by OUTDATED evolutionary slides.
    """
    bundle_path = bundles_dir / f"LATEST_{cluster.theme_slug}_visuals.pptx"
    cluster.bundle_pptx_path = bundle_path
    if dry_run:
        return bundle_path

    bundles_dir.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    archive_strays_dir = bundles_dir.parent.parent / ".archive" / "strays"
    archived_pptxs: List[Path] = (
        sorted(archive_strays_dir.rglob("*.pptx"), reverse=True)
        if archive_strays_dir.exists()
        else []
    )

    for idx, pod in enumerate(cluster.pods, start=1):
        src_pptx = pod.primary_pptx
        temp_generated: Optional[Path] = None
        if (src_pptx is None or not src_pptx.exists()) and archived_pptxs:
            # Check if standalone PPTX was already moved to .archive/strays/ in a previous run
            pod_stem_lower = pod.base_stem.lower()
            for arch_p in archived_pptxs:
                arch_clean, _ = strip_lifecycle_prefix(arch_p.stem)
                arch_clean = _ARCHIVE_DIR_SUFFIX_RE.sub("", arch_clean)
                if arch_clean.lower() == pod_stem_lower:
                    src_pptx = arch_p
                    break

        try:
            if (src_pptx is None or not src_pptx.exists()) and pod.yaml_path and pod.yaml_path.exists():
                # Compile YAML to a temporary PPTX so it can be merged losslessly
                temp_compile_dir.mkdir(parents=True, exist_ok=True)
                res = compile_diagram(
                    pod.yaml_path,
                    output_dir_or_file=temp_compile_dir / f"{pod.base_stem}.pptx",
                    formats=["pptx"],
                )
                src_pptx = res.pptx_path
                temp_generated = src_pptx

            if src_pptx and src_pptx.exists():
                _clone_slide_into_presentation(src_pptx, prs, pod, slide_seq=idx)
        finally:
            if temp_generated and temp_generated.exists():
                try:
                    temp_generated.unlink()
                except Exception:
                    pass

    prs.save(str(bundle_path))
    return bundle_path


def archive_standalone_pptx_files(
    clusters: List[ThemeCluster],
    archive_root: Path,
    dry_run: bool = False,
) -> List[Tuple[Path, Path]]:
    """
    Move standalone 1-slide PPTX files into .archive/strays/<YYYY-MM-DD>/ once merged
    into the theme bundle PPTX, minimizing PPTX clutter in the workspace.
    """
    date_folder = archive_root / datetime.date.today().isoformat()
    archived: List[Tuple[Path, Path]] = []
    used_targets: Set[Path] = set()

    for cluster in clusters:
        for pod in cluster.pods:
            updated_paths: List[Path] = []
            for pptx_p in list(pod.pptx_paths):
                if not pptx_p.exists():
                    updated_paths.append(pptx_p)
                    continue
                target_p = date_folder / pptx_p.name
                # Avoid overwriting if duplicate filename from TEMP/ and output/ or previous runs
                if target_p.exists() or target_p in used_targets:
                    base_candidate = f"{pptx_p.stem}_{pptx_p.parent.name}"
                    target_p = date_folder / f"{base_candidate}{pptx_p.suffix}"
                    counter = 2
                    while target_p.exists() or target_p in used_targets:
                        target_p = date_folder / f"{base_candidate}_{counter}{pptx_p.suffix}"
                        counter += 1
                used_targets.add(target_p)
                archived.append((pptx_p, target_p))
                if not dry_run:
                    date_folder.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(pptx_p), str(target_p))
                    updated_paths.append(target_p)
                else:
                    updated_paths.append(pptx_p)
            pod.pptx_paths = updated_paths

    return archived


def write_stray_backlog_md(
    workspace: Path,
    report: ConsolidationReport,
    dry_run: bool = False,
) -> Path:
    """
    Write STRAY_BACKLOG.md tracking consolidated domain theme bundles, LATEST vs OUTDATED
    lineage, archived standalone PPTXs awaiting EOD deletion, and untagged items needing sorting.
    """
    backlog_path = workspace / "STRAY_BACKLOG.md"
    report.backlog_path = backlog_path
    if dry_run:
        return backlog_path

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: List[str] = [
        "# Stray Visualization Registry & End-of-Day Triage Backlog",
        "",
        f"> **Last Scanned:** `{now_str}` | **Model:** `2.1 (Auto-Theme Clustering + LATEST/OUTDATED Lineage)`",
        "> **Action Required:** Confirm `[NEEDS_CONFIRMATION]` theme assignments below and purge `.archive/strays/` once merged decks are verified.",
        "",
        "---",
        "",
        "## 1. Consolidated Domain Theme Decks (`output/bundles/`)",
        "",
        "| Domain Theme | Consolidated PPTX | Slide Order & Lineage (`LATEST` ➔ `OUTDATED`) | Triage Status |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for cluster in report.clusters:
        deck_rel = (
            cluster.bundle_pptx_path.relative_to(workspace)
            if cluster.bundle_pptx_path and cluster.bundle_pptx_path.is_relative_to(workspace)
            else cluster.bundle_pptx_path
        )
        slide_desc = "<br>".join(
            f"**Slide {idx + 1} (`{p.status}`):** `{p.base_stem}` *({p.variant_kind})*"
            for idx, p in enumerate(cluster.pods)
        )
        badge = "✅ `AUTO-MERGED`" if cluster.confidence == "HIGH" else "⚠️ `NEEDS_CONFIRMATION`"
        lines.append(f"| **`{cluster.theme_slug}`** | [`{deck_rel}`]({deck_rel}) | {slide_desc} | {badge} |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. EOD Sorting Queue (Untagged / Singleton Visualizations)",
        "",
    ])

    unconfirmed = [c for c in report.clusters if c.confidence == "NEEDS_CONFIRMATION"]
    if not unconfirmed:
        lines.append("- *All visualizations matched multi-file theme clusters or explicit `bundle:` tags.*")
    else:
        for c in unconfirmed:
            p = c.pods[0]
            yaml_rel = p.yaml_path.relative_to(workspace) if p.yaml_path and p.yaml_path.is_relative_to(workspace) else p.yaml_path
            lines.append(
                f"- [ ] **`{p.base_stem}`** (Proposed Theme: `{c.theme_slug}`) — "
                f"Add `bundle: <theme_name>` to [`{yaml_rel}`]({yaml_rel}) if it belongs to another deliverable group."
            )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Quarantined Standalone PPTXs (`.archive/strays/` — Ready for EOD Purge)",
        "",
    ])

    archive_dir = workspace / ".archive" / "strays"
    existing_archived = sorted(archive_dir.rglob("*.pptx")) if archive_dir.exists() else []
    if report.archived_pptx_files:
        for src_p, dst_p in report.archived_pptx_files:
            src_rel = src_p.relative_to(workspace) if src_p.is_relative_to(workspace) else src_p
            dst_rel = dst_p.relative_to(workspace) if dst_p.is_relative_to(workspace) else dst_p
            lines.append(f"- `{src_rel}` ➔ [`{dst_rel}`]({dst_rel})")
    elif existing_archived:
        for dst_p in existing_archived:
            dst_rel = dst_p.relative_to(workspace) if dst_p.is_relative_to(workspace) else dst_p
            lines.append(f"- Quarantined: [`{dst_rel}`]({dst_rel})")
    else:
        lines.append("- *No standalone `.pptx` files currently in `.archive/strays/`.*")

    lines.append("")
    backlog_path.write_text("\n".join(lines), encoding="utf-8")
    return backlog_path



def consolidate_stray_visualizations(
    workspace: Path,
    rename_files: bool = True,
    archive_pptx: bool = True,
    dry_run: bool = False,
) -> ConsolidationReport:
    """
    Full Model 2.1 execution pipeline:
    1. Scan workspace for stray visualization pods (.yaml, .pptx, .png, .svg, .drawio).
    2. Auto-cluster into Domain Themes via lexical + AST subgraph inclusion V(A) ⊂ V(B).
    3. Prefix files on disk with LATEST_ / OUTDATED_.
    4. Merge each theme into 1 PPTX (`output/bundles/LATEST_<theme>_visuals.pptx`).
    5. Move standalone 1-slide PPTXs to `.archive/strays/<date>/`.
    6. Emit `STRAY_BACKLOG.md` for EOD sorting.
    """
    workspace = workspace.resolve()
    report = ConsolidationReport(workspace=workspace)

    pods = scan_stray_visualizations(workspace)
    clusters = cluster_and_rank_pods(pods)
    report.clusters = clusters

    if rename_files:
        report.renamed_files = apply_lifecycle_prefixes(clusters, dry_run=dry_run)

    bundles_dir = workspace / "output" / "bundles"
    temp_compile_dir = workspace / ".archive" / "_tmp_compile"

    for cluster in clusters:
        deck_p = merge_cluster_into_theme_pptx(
            cluster=cluster,
            bundles_dir=bundles_dir,
            temp_compile_dir=temp_compile_dir,
            dry_run=dry_run,
        )
        if deck_p:
            report.bundle_decks.append(deck_p)

    if temp_compile_dir.exists() and not dry_run:
        shutil.rmtree(temp_compile_dir, ignore_errors=True)

    if archive_pptx:
        archive_root = workspace / ".archive" / "strays"
        report.archived_pptx_files = archive_standalone_pptx_files(
            clusters=clusters,
            archive_root=archive_root,
            dry_run=dry_run,
        )

    write_stray_backlog_md(workspace, report, dry_run=dry_run)
    return report
