# Enterprise Resource Registry (`assets/`)

> **Policy:** All binary assets (images, high-res logos, photography) live inside gitignored paths (primarily `assets/images/`).
> **Reproducibility Guarantee:** If this repository is cloned fresh, all external dependencies can be re-acquired using the canonical or fallback URLs below, or extracted locally from clean production templates.

---

## 1. Corporate Brand & Partner Logos

| Resource Key | Target Path (Gitignored) | Format & Resolution | Canonical Source / Download URL | Fallback / Local Extraction |
| :--- | :--- | :--- | :--- | :--- |
| `logo_metrodata_square` | `assets/images/logos/metrodata_square.png` | PNG (592×517, RGBA) | `https://www.snowflake.com/content/dam/snowflake-site/general/logos/partner-logos/pt-metrodata-electronics-tbk@3x.png` | Extract `ppt/media/image97.png` from `clean_workspace/projects/TTI_Snowflake_Analytics/01_presales/Modernize_Data_Platform_Pitch_Deck_Template.pptx` |
| `logo_snowflake` | `assets/logos/snowflake.svg` | SVG (Vector, 24×24 viewBox) | Tracked in Git under `assets/logos/` | Official Snowflake Brand Portal |
| `logo_aws` | `assets/logos/aws.svg` | SVG (Vector, 24×24 viewBox) | Tracked in Git under `assets/logos/` | Official AWS Brand Portal |
| `logo_kafka` | `assets/logos/kafka.svg` | SVG (Vector, 24×24 viewBox) | Tracked in Git under `assets/logos/` | Official Apache Software Foundation |
| `logo_dbt` | `assets/logos/dbt.svg` | SVG (Vector, 24×24 viewBox) | Tracked in Git under `assets/logos/` | Official dbt Labs Brand Assets |
| `logo_vault` | `assets/logos/vault.svg` | SVG (Vector, 24×24 viewBox) | Tracked in Git under `assets/logos/` | HashiCorp Brand Portal |

> *Note on Partner Branding:* Metrodata's authentic corporate logo is `logo_metrodata_square` (`assets/images/logos/metrodata_square.png`). The previously extracted `image95.png` was client logo Toyota Tsusho Indonesia mislabeled as Metrodata and has been purged.

---

## 2. Fast Asset Re-acquisition Commands

For automated setup after a fresh clone:

```bash
# 1. Create target gitignored directory:
mkdir -p assets/images/logos

# 2. Download Metrodata square logo from Snowflake Partner CDN:
curl -sSL "https://www.snowflake.com/content/dam/snowflake-site/general/logos/partner-logos/pt-metrodata-electronics-tbk@3x.png" \
  -o assets/images/logos/metrodata_square.png

# OR extract directly from clean master template:
python3 -c "
import zipfile
pptx = 'clean_workspace/projects/TTI_Snowflake_Analytics/01_presales/Modernize_Data_Platform_Pitch_Deck_Template.pptx'
with zipfile.ZipFile(pptx, 'r') as z:
    with open('assets/images/logos/metrodata_square.png', 'wb') as f:
        f.write(z.read('ppt/media/image97.png'))
"
```

---

## 3. Subsystem Architecture: `missing_resources.md`

When `bench ppt generate` or any deliverable engine executes:

1. **Pre-flight Resource Resolution:**
   - The engine checks if target image files exist on disk.
   - If missing, it attempts automated download using `Canonical URL` with a 3-second timeout.

2. **Graceful Fallback Execution (Zero Crash Guarantee):**
   - If an asset remains missing (offline, DNS failure, 404), the presentation generator **never crashes** with a raw `FileNotFoundError`.
   - Instead, it renders a semantic, theme-compliant fallback:
     * **Logo Missing:** Renders an elegant typographic badge (`[ METRODATA ]`) formatted with `theme.get_rgb("primary")`.
     * **Stock Photo Missing:** Renders an atmospheric solid-to-accent gradient rectangle with subtle cross-hatch.

3. **Automated Diagnostic Ledger (`missing_resources.md`):**
   - The engine writes or updates `missing_resources.md` at workspace root detailing:
     * Missing Resource Key & Target Path
     * Affected Slide Archetypes (e.g. Cover Slide, Chapter Divider)
     * Direct `curl` recovery command
     * Impact summary
   - When all registered resources are verified and present on disk, `missing_resources.md` is automatically cleaned and removed.

---

## 4. Verification & On-Demand Acquisition CLI

Run the resource check tool across all registered deliverable assets:

```bash
# Check status and silently download missing assets:
uv run bench ppt check-resources

# Check-only without downloading:
uv run bench ppt check-resources --no-download

# Strict gate (fails with exit code 1 if any asset is missing):
uv run bench ppt check-resources --strict
```

---

## 5. Diagram Icon Style Weight & Palette Harmonization Taxonomy

In architecture diagrams (`src/ppt_engine/diagram_engine.py`), embedded vector iconography is classified into three geometric styles via the `DrawIONode.icon_weight` AST property:

| Weight Style | Target Icons | Stroke / Fill Mechanics | Palette Binding | 1080p Presentation Guarantee |
| :--- | :--- | :--- | :--- | :--- |
| `light` | Lucide, Feather, Heroicons (`assets/icons/`) | Outline stroke normalized to $\ge 1.75\text{px}$ (typically $1.8\text{px}$), transparent fill (`fill="none"`) | Binds to node stroke (`strokeColor`) or explicit `icon_color` | Normalized stroke width prevents 1px hairline disappearance on 1080p slide renders |
| `weighted` | Solid silhouettes | Solid fill silhouette, synchronized stroke | Harmonized to container accent palette (`accent_node_stroke` / `accent_node_font`) | Dense visual presence balanced against card container |
| `brand` | Partner & vendor technology marks (Snowflake, AWS, Kafka, Cloudera, dbt, Vault) | Multi-color vector or canonical vendor fills | Preserves authentic vendor brand colors (`preserve_brand_color=True`): Snowflake cyan (`#29B5E8`), AWS orange (`#FF9900`), Kafka white/black (`#FFFFFF`/`#231F20`), dbt orange (`#FF694B`), Vault (`#000000`/`#FFFFFF`), Cloudera coral/white | Protected by default against inadvertent container theme tinting |

### Automatic AST Inference Precedence:
1. Explicit node property: `DrawIONode(..., icon_weight="brand")` or `node.icon_weight = "weighted"`
2. Explicit style dictionary entry: `custom_style={"icon_weight": "..."}` or `{"weight": "..."}`
3. Provenance & Namespace Inference:
   - `assets/logos/*` or corporate vendor keys (`snowflake`, `aws`, `kafka`, `cloudera`, `dbt`, `vault`) $\rightarrow$ `"brand"`
   - `assets/icons/*`, `lucide:*`, `feather:*`, outline glyphs $\rightarrow$ `"light"`

