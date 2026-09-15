# Enterprise Resource Registry (`assets/`)

> **Policy:** All binary assets (images, high-res logos, photography) live inside gitignored paths (primarily `assets/images/`).
> **Reproducibility Guarantee:** If this repository is cloned fresh, all external dependencies can be re-acquired using the canonical or fallback URLs below, or extracted locally from clean production templates.

---

## 1. Corporate Brand & Partner Logos

| Resource Key | Target Path (Gitignored) | Format & Resolution | Canonical Source / Download URL | Fallback / Local Extraction |
| :--- | :--- | :--- | :--- | :--- |
| `logo_metrodata_square` | `assets/images/logos/metrodata_square.png` | PNG (592×517, RGBA) | `https://www.snowflake.com/content/dam/snowflake-site/general/logos/partner-logos/pt-metrodata-electronics-tbk@3x.png` | Extract `ppt/media/image97.png` from `clean_workspace/projects/TTI_Snowflake_Analytics/01_presales/Modernize_Data_Platform_Pitch_Deck_Template.pptx` |
| `logo_snowflake` | `assets/logos/snowflake.svg` | SVG (Vector, 24×24 viewBox) | Tracked in Git under `assets/logos/` | Official Snowflake Brand Portal |
| `logo_metrodata_wide` | `assets/images/logos/metrodata_wide.png` | PNG (1594×182, RGBA) | Metrodata Corporate Portal (`metrodata.co.id`) | Extract `ppt/media/image95.png` from `Modernize_Data_Platform_Pitch_Deck_Template.pptx` |

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
