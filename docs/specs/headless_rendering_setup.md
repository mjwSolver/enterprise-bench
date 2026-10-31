# Headless Presentation Rasterization & Multi-Modal Vision Setup

> **Subsystem:** Diagram Engine V2 / Presentation Engine  
> **Status:** `CONFIRMED BASELINE` | **Version Stamp:** `v2.3`  
> **Directive Alignment:** Enforces the [Headless-First Verification Directive](file:///Users/marcelljw/VisualStudioCode/enterprise-bench/AGENTS.md) — 100% verification without desktop application popups (`open -a`).

---

## 1. Overview & Objective
This specification defines the zero-popup headless rasterization pipeline for PowerPoint (`.pptx`) and Word (`.docx`) deliverables. 

By rendering slides into high-DPI raster images headlessly, AI agents and automated CI runners can inspect rendered output using multi-modal vision to detect font clipping, text wrap drift, and visual congestion without launching Microsoft Office.

---

## 2. Cross-Platform Installation

These tools are external system utilities. They add **zero dependencies to Python / `pyproject.toml`** and run completely out-of-process.

### macOS (Homebrew)
```bash
brew install --cask libreoffice
brew install poppler
```

### Ubuntu / Debian Linux
```bash
sudo apt-get update
sudo apt-get install -y libreoffice-impress poppler-utils
```

### Windows (winget / Chocolatey / Scoop)
```powershell
# Using winget & chocolatey:
winget install TheDocumentFoundation.LibreOffice
choco install poppler

# Or using Scoop:
scoop install libreoffice poppler
```
*(Ensure `soffice` and `pdftoppm` are exported to the system `PATH`.)*

---

## 3. The Headless Execution Pipeline

When `soffice` and `pdftoppm` are present, the CLI executes:

```bash
# 1. Headless PPTX to PDF export (approx. 0.8s)
soffice --headless --convert-to pdf:impress_pdf_Export slide.pptx --outdir output/

# 2. Extract 150 DPI PNG raster plate from PDF (approx. 0.2s)
pdftoppm -png -r 150 output/slide.pdf output/slide_preview
```

The resulting `output/slide_preview-1.png` is passed directly to `PerceptualImageAnalyzer` or multimodal visual QA.

---

## 4. Graceful Fallback Architecture

If `soffice` or `pdftoppm` is not installed on a developer's machine:
1. **Zero Blocking Errors:** The engine logs an informational notice (`[dim]Headless rasterizer not found; operating under Tier 1 Geometric Linting.[/dim]`).
2. **Definitive Gate:** `Tier1GeometricLinter` executes its full suite of 19 spatial and typographic checks (`auditor.py`).
3. **No Build Failures:** Compilations and audits pass normally based on coordinate mathematics.

---

## 5. Reliability & Blind-Spot Comparison

| Verification Layer | What It Catches (100% Reliable) | Known Blind Spots / Limits |
| :--- | :--- | :--- |
| **Tier 1: Geometric Linter (`auditor.py`)**<br>*~85–90% Coverage* | • Physical bounding box collisions<br>• Connector span violations ($< 140\text{px}$)<br>• Arrow swallowing & obstacle clipping<br>• Header drift ($y < 1.350''$)<br>• Excessive node density & mathematical overflow | • Platform font substitution differences<br>• Non-standard word wrapping on long technical strings<br>• Sub-pixel anti-aliasing clipping |
| **Tier 2: Multi-Modal Vision (`visual_verifier.py`)**<br>*~10–15% Remaining* | • Actual rendered font line wrapping<br>• Visual balance and optical density hotspots<br>• Subtle WCAG contrast washing on complex gradients | • Requires external system binaries (`soffice`, `poppler`) |
