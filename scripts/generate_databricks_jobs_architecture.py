#!/usr/bin/env python3
"""
Generate Databricks Jobs API Architecture Visualization & Presentation Assets.

Implements all user refinements:
1. Space optimization: tightened container bounds to 435pt height, eliminating dead whitespace.
2. Prominent App icons: significantly enlarged monitor/laptop icons on App 1 (48px), App 2 (42px), App 3 (42px).
3. DBx Jobs API icon: fixed black artifacts by setting fill="none" on all SVG paths, and mathematically centered in the card (x=70, w=60 in w=200 card).
4. Re-included all arrow flows and between-arrow captions:
   - DBx Jobs API -> Cluster: POST /run-now
   - Cluster -> DBx Jobs API: Execution Done (dashed return)
   - Code -> Cluster: Run Here
   - Cluster -> Database: checks
   - Database -> Cluster: Record Result (dashed return)
   - Client Apps <-> DBx Jobs API: run-now / returns
5. Retained COMPUTE ENGINE heading at the top of Cluster.
6. Retained titles:
   - Code: Code & Notebook, Python, Wheel Dependencies
   - Database: Database & Unity Catalog
   - Cluster: COMPUTE ENGINE & Cluster
   - DBx Jobs API: DATABRICKS API 2.1 & DBx Jobs API
7. Official vector brand icons (REST API, Compute Clusters, Notebooks, Delta Lake, Monitors).
8. Dual brand stripes (1 Red : 2 Blue) at top left with clean non-verbose title.
9. Full solid white background (zero transparency, flat plain colors, no gradients).
10. Exactly 1-slide PowerPoint presentation embedding native vector SVG via OpenXML asvg:svgBlip.
"""

import os
import sys
import shutil
import subprocess
import zlib
import base64
import urllib.parse
import re
import html
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Base directories
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
TEMP_DIR = PROJECT_ROOT / "TEMP"
OUTPUT_DIR = PROJECT_ROOT / "output"
ASSETS_DIR = PROJECT_ROOT / "assets"
ARTIFACT_DIR = Path("/Users/marcelljw/.gemini/antigravity/brain/e043544e-083a-4220-b321-aefe0c3d969e")

# Load SVG logos for base64 data URIs for Draw.io
def get_svg_uri(rel_path: str) -> str:
    p = ASSETS_DIR / rel_path
    if p.exists():
        return f"data:image/svg+xml;base64,{base64.b64encode(p.read_bytes()).decode('ascii')}"
    return ""

dbx_logo_uri = get_svg_uri("logos/databricks/databricks.svg")
cluster_logo_uri = get_svg_uri("logos/databricks/compute_clusters.svg")
rest_api_logo_uri = get_svg_uri("logos/databricks/rest-api.svg")
delta_lake_logo_uri = get_svg_uri("logos/databricks/delta_lake.svg")
notebooks_logo_uri = get_svg_uri("logos/databricks/notebooks.svg")

monitor_svg_data = """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="3" rx="2" fill="#EFF6FF"/><path d="M8 21h8m-4-4v4"/></svg>"""
monitor_logo_uri = f"data:image/svg+xml;base64,{base64.b64encode(monitor_svg_data.encode('utf-8')).decode('ascii')}"


def create_drawio_xml() -> str:
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="Electron" agent="Enterprise Bench Diagram Engine" version="21.0.0" type="device">
  <diagram id="databricks_jobs_api" name="Databricks Jobs API Architecture">
    <mxGraphModel dx="1280" dy="720" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1280" pageHeight="720" background="#FFFFFF" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- ================= BRAND ACCENT STRIPES & CLEAN HEADER ================= -->
        <mxCell id="stripe_red" value="" style="rounded=1;arcSize=50;whiteSpace=wrap;html=1;fillColor=#E11D48;strokeColor=none;" vertex="1" parent="1">
          <mxGeometry x="50" y="32" width="5" height="34" as="geometry"/>
        </mxCell>
        <mxCell id="stripe_blue" value="" style="rounded=1;arcSize=50;whiteSpace=wrap;html=1;fillColor=#0284C7;strokeColor=none;" vertex="1" parent="1">
          <mxGeometry x="58" y="32" width="9" height="34" as="geometry"/>
        </mxCell>
        <mxCell id="header_title" value="&lt;b style=&quot;font-size:22px; color:#0F172A; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;&quot;&gt;Databricks Jobs API&lt;/b&gt;" style="text;html=1;align=left;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="74" y="28" width="300" height="42" as="geometry"/>
        </mxCell>

        <!-- ================= ZONE 1: CLIENT APPLICATIONS ================= -->
        <mxCell id="group_apps" value="CLIENT APPLICATIONS" style="rounded=1;arcSize=14;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#94A3B8;strokeWidth=2;fillColor=#F8FAFC;fontFamily=Helvetica, Arial, sans-serif;fontColor=#64748B;fontSize=12;fontStyle=1;align=center;verticalAlign=top;spacingTop=14;" vertex="1" parent="1">
          <mxGeometry x="50" y="105" width="280" height="435" as="geometry"/>
        </mxCell>

        <!-- APP 1 (TOP) -->
        <mxCell id="node_app1" value="&lt;div style=&quot;margin-bottom:8px;&quot;&gt;&lt;img src=&quot;{monitor_logo_uri}&quot; width=&quot;44&quot; height=&quot;44&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-weight:800; font-size:18px; color:#1E3A8A;&quot;&gt;App 1&lt;/div&gt;" style="rounded=1;arcSize=14;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="80" y="150" width="220" height="145" as="geometry"/>
        </mxCell>

        <!-- APP 2 (BOTTOM LEFT) -->
        <mxCell id="node_app2" value="&lt;div style=&quot;margin-bottom:8px;&quot;&gt;&lt;img src=&quot;{monitor_logo_uri}&quot; width=&quot;40&quot; height=&quot;40&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-weight:800; font-size:16px; color:#1E3A8A;&quot;&gt;App 2&lt;/div&gt;" style="rounded=1;arcSize=14;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="70" y="325" width="115" height="165" as="geometry"/>
        </mxCell>

        <!-- APP 3 (BOTTOM RIGHT) -->
        <mxCell id="node_app3" value="&lt;div style=&quot;margin-bottom:8px;&quot;&gt;&lt;img src=&quot;{monitor_logo_uri}&quot; width=&quot;40&quot; height=&quot;40&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-weight:800; font-size:16px; color:#1E3A8A;&quot;&gt;App 3&lt;/div&gt;" style="rounded=1;arcSize=14;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="195" y="325" width="115" height="165" as="geometry"/>
        </mxCell>

        <!-- ================= ZONE 2: DBX JOBS API ================= -->
        <mxCell id="node_dbx_api" value="&lt;div style=&quot;font-size:10px; font-weight:800; color:#C2410C; letter-spacing:0.5px; margin-bottom:8px;&quot;&gt;&lt;span style=&quot;background:#FFEDD5; padding:3px 8px; border-radius:4px;&quot;&gt;DATABRICKS API 2.1&lt;/span&gt;&lt;/div&gt;&lt;div style=&quot;margin-bottom:8px;&quot;&gt;&lt;img src=&quot;{rest_api_logo_uri}&quot; width=&quot;44&quot; height=&quot;44&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-size:19px; font-weight:800; color:#7C2D12;&quot;&gt;DBx Jobs API&lt;/div&gt;" style="rounded=1;arcSize=14;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#EA580C;strokeWidth=2.2;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="375" y="225" width="200" height="190" as="geometry"/>
        </mxCell>

        <!-- ================= ZONE 3: DATABRICKS ENVIRONMENT ================= -->
        <mxCell id="group_databricks" value="DATABRICKS" style="rounded=1;arcSize=14;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#EA580C;strokeWidth=2;fillColor=#FFFBF8;fontFamily=Helvetica, Arial, sans-serif;fontColor=#C2410C;fontSize=12;fontStyle=1;align=left;verticalAlign=top;spacingLeft=18;spacingTop=14;" vertex="1" parent="1">
          <mxGeometry x="640" y="105" width="595" height="435" as="geometry"/>
        </mxCell>

        <!-- CLUSTER (COMPUTE ENGINE HEADING AT TOP - BALANCED SPACING) -->
        <mxCell id="node_cluster" value="&lt;div style=&quot;font-size:10.5px; font-weight:800; color:#DC2626; letter-spacing:0.5px; margin-top:4px; margin-bottom:12px;&quot;&gt;&lt;span style=&quot;background:#FEE2E2; padding:4px 12px; border-radius:5px;&quot;&gt;COMPUTE ENGINE&lt;/span&gt;&lt;/div&gt;&lt;div style=&quot;margin-bottom:12px;&quot;&gt;&lt;img src=&quot;{cluster_logo_uri}&quot; width=&quot;50&quot; height=&quot;50&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-size:22px; font-weight:800; color:#0F172A;&quot;&gt;Cluster&lt;/div&gt;" style="rounded=1;arcSize=40;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#FF3621;strokeWidth=2.5;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="680" y="225" width="220" height="190" as="geometry"/>
        </mxCell>

        <!-- CODE COMPONENT (TOP RIGHT) -->
        <mxCell id="node_code" value="&lt;div style=&quot;font-size:10px; font-weight:800; color:#065F46; letter-spacing:0.5px; margin-bottom:6px;&quot;&gt;&lt;span style=&quot;background:#D1FAE5; padding:3px 8px; border-radius:4px;&quot;&gt;TASK ARTIFACT&lt;/span&gt;&lt;/div&gt;&lt;div style=&quot;margin-bottom:6px;&quot;&gt;&lt;img src=&quot;{notebooks_logo_uri}&quot; width=&quot;34&quot; height=&quot;34&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-size:19px; font-weight:800; color:#065F46; margin-bottom:4px;&quot;&gt;Code&lt;/div&gt;&lt;div style=&quot;font-size:11px; font-weight:700; color:#047857;&quot;&gt;Notebook, Python, Wheel Dependencies&lt;/div&gt;" style="rounded=1;arcSize=14;whiteSpace=wrap;html=1;fillColor=#ECFDF5;strokeColor=#10B981;strokeWidth=2;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="965" y="145" width="245" height="140" as="geometry"/>
        </mxCell>

        <!-- DATABASE COMPONENT (BOTTOM RIGHT CYLINDER) -->
        <mxCell id="node_database" value="&lt;div style=&quot;padding-top:14px; font-size:10px; font-weight:800; color:#0369A1; letter-spacing:0.5px; margin-bottom:6px;&quot;&gt;&lt;span style=&quot;background:#BAE6FD; padding:3px 8px; border-radius:4px;&quot;&gt;UNITY CATALOG&lt;/span&gt;&lt;/div&gt;&lt;div style=&quot;margin-bottom:6px;&quot;&gt;&lt;img src=&quot;{delta_lake_logo_uri}&quot; width=&quot;34&quot; height=&quot;34&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-size:19px; font-weight:800; color:#0369A1; margin-bottom:4px;&quot;&gt;Database&lt;/div&gt;&lt;div style=&quot;font-size:11px; font-weight:700; color:#0284C7;&quot;&gt;Unity Catalog&lt;/div&gt;" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=16;fillColor=#F0F9FF;strokeColor=#0284C7;strokeWidth=2;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="970" y="355" width="235" height="155" as="geometry"/>
        </mxCell>

        <!-- ================= CONNECTORS / FLOW ARROWS ================= -->

        <!-- 1. CLIENT CONTAINER -> DBX JOBS API (RUN-NOW) -->
        <mxCell id="edge_client_to_api" value="run-now" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#2563EB;strokeWidth=2.6;fontColor=#1D4ED8;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;labelBackgroundColor=#EFF6FF;labelBorderColor=#BFDBFE;exitX=1;exitY=0.40;entryX=0;entryY=0.29;" edge="1" parent="1" source="group_apps" target="node_dbx_api">
          <mxGeometry relative="1" as="geometry">
            <mxPoint y="-12" as="offset"/>
          </mxGeometry>
        </mxCell>

        <!-- 2. DBX JOBS API -> CLIENT CONTAINER (RETURNS) -->
        <mxCell id="edge_api_to_client" value="returns" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#2563EB;strokeWidth=2.6;fontColor=#1D4ED8;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;labelBackgroundColor=#EFF6FF;labelBorderColor=#BFDBFE;exitX=0;exitY=0.71;entryX=1;entryY=0.59;" edge="1" parent="1" source="node_dbx_api" target="group_apps">
          <mxGeometry relative="1" as="geometry">
            <mxPoint y="12" as="offset"/>
          </mxGeometry>
        </mxCell>

        <!-- 3. DBX JOBS API -> CLUSTER (POST /run-now) -->
        <mxCell id="edge_api_to_cluster" value="POST /run-now" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#EA580C;strokeWidth=2.6;fontColor=#C2410C;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;labelBackgroundColor=#FFF7ED;labelBorderColor=#FFEDD5;exitX=1;exitY=0.29;entryX=0;entryY=0.29;" edge="1" parent="1" source="node_dbx_api" target="node_cluster">
          <mxGeometry relative="1" as="geometry">
            <mxPoint y="-12" as="offset"/>
          </mxGeometry>
        </mxCell>

        <!-- 4. CLUSTER -> DBX JOBS API (Execution Done - DASHED RETURN) -->
        <mxCell id="edge_cluster_to_api" value="Execution Done" style="edgeStyle=straight;dashed=1;dashPattern=5 4;html=1;endArrow=block;endFill=1;strokeColor=#EA580C;strokeWidth=2.4;fontColor=#C2410C;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;labelBackgroundColor=#FFF7ED;labelBorderColor=#FFEDD5;exitX=0;exitY=0.71;entryX=1;entryY=0.71;" edge="1" parent="1" source="node_cluster" target="node_dbx_api">
          <mxGeometry relative="1" as="geometry">
            <mxPoint y="12" as="offset"/>
          </mxGeometry>
        </mxCell>

        <!-- 5. CODE -> CLUSTER (RUN HERE) -->
        <mxCell id="edge_code_to_cluster" value="Run Here" style="edgeStyle=curvedEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#10B981;strokeWidth=2.6;fontColor=#047857;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;labelBackgroundColor=#ECFDF5;labelBorderColor=#A7F3D0;exitX=0;exitY=0.55;entryX=0.92;entryY=0.22;" edge="1" parent="1" source="node_code" target="node_cluster">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="920" y="225"/>
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- 6. CLUSTER -> DATABASE (CHECKS) -->
        <mxCell id="edge_cluster_to_db" value="checks" style="edgeStyle=curvedEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#0284C7;strokeWidth=2.6;fontColor=#0369A1;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;labelBackgroundColor=#F0F9FF;labelBorderColor=#BAE6FD;exitX=0.92;exitY=0.68;entryX=0;entryY=0.28;" edge="1" parent="1" source="node_cluster" target="node_database">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="930" y="365"/>
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- 7. DATABASE -> CLUSTER (RECORD RESULT - DASHED RETURN) -->
        <mxCell id="edge_db_to_cluster" value="Record Result" style="edgeStyle=curvedEdgeStyle;rounded=1;dashed=1;dashPattern=5 4;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#0284C7;strokeWidth=2.4;fontColor=#0369A1;fontFamily=Helvetica, Arial, sans-serif;fontSize=10.5;fontStyle=1;labelBackgroundColor=#F0F9FF;labelBorderColor=#BAE6FD;exitX=0;exitY=0.68;entryX=0.92;entryY=0.88;" edge="1" parent="1" source="node_database" target="node_cluster">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="930" y="440"/>
            </Array>
          </mxGeometry>
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""
    return xml


def create_high_fidelity_svg() -> str:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720" style="background:#FFFFFF; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>

    <!-- Arrow Markers -->
    <marker id="arrow-blue" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#2563EB"/>
    </marker>
    <marker id="arrow-orange" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#EA580C"/>
    </marker>
    <marker id="arrow-green" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#10B981"/>
    </marker>
    <marker id="arrow-sky" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#0284C7"/>
    </marker>
  </defs>

  <!-- Clean Canvas Background (Full Solid White, Non-Transparent) -->
  <rect width="100%" height="100%" fill="#FFFFFF"/>

  <!-- ================= HEADER SECTION ================= -->
  <!-- Brand Stripes (1 Red : 2 Blue Ratio) -->
  <rect x="50" y="34" width="5" height="34" fill="#E11D48" rx="1.5"/>
  <rect x="58" y="34" width="9" height="34" fill="#0284C7" rx="1.5"/>
  <text x="78" y="59" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="24" font-weight="800" fill="#0F172A">Databricks Jobs API</text>

  <!-- ================= ZONE 1: CLIENT APPLICATIONS (SPACE OPTIMIZED) ================= -->
  <g id="zone-client-apps">
    <!-- Outer Container (Plain Color Fill, Height Tightened to 435px to Eliminate Dead Space) -->
    <rect x="50" y="105" width="280" height="435" rx="16" fill="#F8FAFC" stroke="#94A3B8" stroke-width="2" stroke-dasharray="8 6"/>
    <text x="190" y="134" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="700" fill="#64748B" text-anchor="middle" letter-spacing="0.5">CLIENT APPLICATIONS</text>

    <!-- App 1 (Top Center, Large Prominent Monitor Icon) -->
    <g id="app1" transform="translate(80, 150)">
      <rect x="0" y="0" width="220" height="145" rx="14" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
      <!-- Large Monitor Icon (Centered, 50x50) -->
      <svg x="85" y="20" width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect width="20" height="14" x="2" y="3" rx="2" fill="#EFF6FF"/>
        <path d="M8 21h8m-4-4v4"/>
      </svg>
      <text x="110" y="108" text-anchor="middle" font-size="18" font-weight="800" fill="#1E3A8A">App 1</text>
    </g>

    <!-- App 2 (Bottom Left, Large Prominent Monitor Icon) -->
    <g id="app2" transform="translate(70, 325)">
      <rect x="0" y="0" width="115" height="165" rx="14" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
      <!-- Large Monitor Icon (Centered, 44x44) -->
      <svg x="35.5" y="24" width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect width="20" height="14" x="2" y="3" rx="2" fill="#EFF6FF"/>
        <path d="M8 21h8m-4-4v4"/>
      </svg>
      <text x="57.5" y="112" text-anchor="middle" font-size="16" font-weight="800" fill="#1E3A8A">App 2</text>
    </g>

    <!-- App 3 (Bottom Right, Large Prominent Monitor Icon) -->
    <g id="app3" transform="translate(195, 325)">
      <rect x="0" y="0" width="115" height="165" rx="14" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
      <!-- Large Monitor Icon (Centered, 44x44) -->
      <svg x="35.5" y="24" width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect width="20" height="14" x="2" y="3" rx="2" fill="#EFF6FF"/>
        <path d="M8 21h8m-4-4v4"/>
      </svg>
      <text x="57.5" y="112" text-anchor="middle" font-size="16" font-weight="800" fill="#1E3A8A">App 3</text>
    </g>
  </g>

  <!-- ================= ZONE 2: INTEGRATION / DBX JOBS API (CENTERED & ZERO BLACK ARTIFACTS) ================= -->
  <g id="zone-dbx-api" transform="translate(375, 225)">
    <rect x="0" y="0" width="200" height="190" rx="14" fill="#FFFFFF" stroke="#EA580C" stroke-width="2.2"/>
    
    <!-- Header Badge (Centered at x=100) -->
    <rect x="25" y="16" width="150" height="22" rx="5" fill="#FFEDD5"/>
    <text x="100" y="31" text-anchor="middle" font-size="10.5" font-weight="800" fill="#C2410C" letter-spacing="0.5">DATABRICKS API 2.1</text>

    <!-- Official REST API Vector Glyph (EXACTLY CENTERED: x=70, w=60 in card w=200 -> center=100) -->
    <!-- All paths explicitly have fill="none" to eliminate black artifacts -->
    <svg x="70" y="48" width="60" height="60" viewBox="0 0 48 48" fill="none">
      <g transform="translate(2 2) scale(0.4583)" fill="none">
        <path d="M47.6417 36.9986C51.4202 36.9986 54.4833 33.9355 54.4833 30.157C54.4833 26.3785 51.4202 23.3154 47.6417 23.3154C43.8632 23.3154 40.8001 26.3785 40.8001 30.157C40.8001 33.9355 43.8632 36.9986 47.6417 36.9986Z" stroke="#EA580C" stroke-width="2.2" stroke-miterlimit="3" stroke-linecap="square" fill="none"/>
        <path d="M68.9153 73.8431C72.6938 73.8431 75.7569 70.78 75.7569 67.0015C75.7569 63.223 72.6938 60.1599 68.9153 60.1599C65.1368 60.1599 62.0737 63.223 62.0737 67.0015C62.0737 70.78 65.1368 73.8431 68.9153 73.8431Z" stroke="#EA580C" stroke-width="2.2" stroke-miterlimit="3" stroke-linecap="square" fill="none"/>
        <path d="M26.3681 73.8431C30.1466 73.8431 33.2097 70.78 33.2097 67.0015C33.2097 63.223 30.1466 60.1599 26.3681 60.1599C22.5896 60.1599 19.5265 63.223 19.5265 67.0015C19.5265 70.78 22.5896 73.8431 26.3681 73.8431Z" stroke="#EA580C" stroke-width="2.2" stroke-miterlimit="3" stroke-linecap="square" fill="none"/>
        <path d="M60.5953 67.0016L44.1409 67.0016C44.1409 76.8192 36.1793 84.7808 26.3617 84.7808C16.5441 84.7808 8.58249 76.8192 8.58249 67.0016C8.58249 57.184 16.5441 49.2224 26.3617 49.2224" stroke="#EA580C" stroke-width="2.2" stroke-miterlimit="3" stroke-linecap="square" fill="none"/>
        <path d="M51.9105 37.5488L60.0321 51.6096C68.5313 46.7008 79.4049 49.6128 84.3137 58.1184C89.2225 66.6176 86.3105 77.4912 77.8049 82.4C69.3057 87.3088 58.4321 84.3968 53.5233 75.8912" stroke="#EA580C" stroke-width="2.2" stroke-miterlimit="3" stroke-linecap="square" fill="none"/>
        <path d="M30.5217 59.8081L38.7521 45.5553C30.2529 40.6465 27.3345 29.7729 32.2433 21.2737C37.1521 12.7745 48.0257 9.8561 56.5249 14.7649C65.0241 19.6737 67.9425 30.5473 63.0337 39.0465" stroke="#EA580C" stroke-width="2.2" stroke-miterlimit="3" stroke-linecap="square" fill="none"/>
      </g>
    </svg>

    <text x="100" y="152" text-anchor="middle" font-size="19" font-weight="800" fill="#7C2D12">DBx Jobs API</text>
  </g>

  <!-- ================= ZONE 3: DATABRICKS ENVIRONMENT (SPACE OPTIMIZED) ================= -->
  <g id="zone-databricks">
    <!-- Outer Container (Plain Color Fill, Height 435px aligned with Client Apps) -->
    <rect x="640" y="105" width="595" height="435" rx="16" fill="#FFFBF8" stroke="#EA580C" stroke-width="2" stroke-dasharray="8 6"/>
    
    <!-- Databricks Label with Brand Icon -->
    <rect x="660" y="118" width="135" height="26" rx="6" fill="#EA580C"/>
    <g transform="translate(669, 123) scale(0.95)">
      <path d="M13.7194 6.60746L7.25506 10.338L0.332928 6.35214L0 6.53654L0 9.43016L7.25506 13.6004L13.7194 9.88406V11.416L7.25506 15.1465L0.332928 11.1607L0 11.3451L0 11.8415L7.25506 16.0117L14.4962 11.8415V8.94789L14.1633 8.76349L7.25506 12.7351L0.776832 9.01881L0.776832 7.4869L7.25506 11.2032L14.4962 7.033V4.18193L14.1356 3.96917L7.25506 7.92661L1.10976 4.40888L7.25506 0.876967L12.3045 3.78477L12.7484 3.52945V3.17484L7.25506 0.0117187L0 4.18193L0 4.63583L7.25506 8.80605L13.7194 5.07555V6.60746Z" fill="#FFFFFF"/>
    </g>
    <text x="737" y="135" text-anchor="middle" font-size="11.5" font-weight="800" fill="#FFFFFF" letter-spacing="0.5">DATABRICKS</text>

    <!-- Cluster Node (COMPUTE ENGINE HEADING AT THE TOP - BALANCED SPACING) -->
    <g id="cluster-node" transform="translate(680, 225)">
      <!-- Oval / Pill shape -->
      <rect x="0" y="0" width="220" height="190" rx="40" fill="#FFFFFF" stroke="#FF3621" stroke-width="2.5"/>
      
      <!-- Retained COMPUTE ENGINE Heading Badge at Top -->
      <rect x="40" y="20" width="140" height="22" rx="6" fill="#FEE2E2"/>
      <text x="110" y="35" text-anchor="middle" font-size="10.5" font-weight="800" fill="#DC2626" letter-spacing="0.5">COMPUTE ENGINE</text>

      <!-- Official Compute Clusters Icon (Prominent 56x56, Centered) -->
      <svg x="82" y="58" width="56" height="56" viewBox="0 0 48 48" fill="none">
        <g transform="translate(2 2) scale(1.375)">
          <path fill-rule="evenodd" clip-rule="evenodd" d="M5.5 22C4.11929 22 3 23.1193 3 24.5C3 25.8807 4.11929 27 5.5 27C6.88071 27 8 25.8807 8 24.5C8 23.1193 6.88071 22 5.5 22ZM4.00779 19.2048C1.6953 19.8552 0 21.9796 0 24.5C0 27.5376 2.46243 30 5.5 30C7.96481 30 10.0509 28.3786 10.75 26.1443C11.4491 28.3786 13.5352 30 16 30C18.4648 30 20.5509 28.3786 21.25 26.1443C21.9491 28.3786 24.0352 30 26.5 30C29.5376 30 32 27.5376 32 24.5C32 21.9796 30.3047 19.8552 27.9922 19.2048C27.8388 16.3045 25.4385 14 22.5 14H17.5V12.793C19.8085 12.14 21.5 10.0176 21.5 7.5C21.5 4.46243 19.0376 2 16 2C12.9624 2 10.5 4.46243 10.5 7.5C10.5 10.0176 12.1915 12.14 14.5 12.793V14H9.5C6.56145 14 4.16116 16.3045 4.00779 19.2048ZM14.5 17H9.5C8.21679 17 7.15939 17.9668 7.01645 19.2117C8.79201 19.7199 10.2001 21.0982 10.75 22.8557C11.3016 21.0928 12.7167 19.7114 14.5 19.207V17ZM17.5 17V19.207C19.2833 19.7114 20.6984 21.0928 21.25 22.8557C21.7999 21.0982 23.208 19.7199 24.9836 19.2117C24.8406 17.9668 23.7832 17 22.5 17H17.5ZM24 24.5C24 23.1193 25.1193 22 26.5 22C27.8807 22 29 23.1193 29 24.5C29 25.8807 27.8807 27 26.5 27C25.1193 27 24 25.8807 24 24.5ZM13.5 24.5C13.5 25.8807 14.6193 27 16 27C17.3807 27 18.5 25.8807 18.5 24.5C18.5 23.1193 17.3807 22 16 22C14.6193 22 13.5 23.1193 13.5 24.5ZM16 10C14.6193 10 13.5 8.88071 13.5 7.5C13.5 6.11929 14.6193 5 16 5C17.3807 5 18.5 6.11929 18.5 7.5C18.5 8.88071 17.3807 10 16 10Z" fill="#FF3621"/>
        </g>
      </svg>
      
      <text x="110" y="146" text-anchor="middle" font-size="22" font-weight="800" fill="#0F172A">Cluster</text>
    </g>

    <!-- Code Component (Upper Right) -->
    <g id="code-node" transform="translate(965, 145)">
      <rect x="0" y="0" width="245" height="140" rx="14" fill="#ECFDF5" stroke="#10B981" stroke-width="2"/>
      
      <!-- Header Badge -->
      <rect x="62" y="14" width="120" height="20" rx="5" fill="#D1FAE5"/>
      <text x="122.5" y="28" text-anchor="middle" font-size="10" font-weight="800" fill="#065F46" letter-spacing="0.5">TASK ARTIFACT</text>

      <!-- Official Databricks Notebooks Icon -->
      <g transform="translate(105, 38) scale(2.2)">
        <path fill-rule="evenodd" clip-rule="evenodd" d="M3 1.75C3 1.33579 3.33579 1 3.75 1L14.25 1C14.6642 1 15 1.33579 15 1.75L15 14.25C15 14.6642 14.6642 15 14.25 15L3.75 15C3.33579 15 3 14.6642 3 14.25L3 12.5H1V11H3L3 8.75H1L1 7.25H3L3 5H1L1 3.5L3 3.5L3 1.75ZM4.5 2.5L4.5 13.5H6L6 2.5L4.5 2.5ZM7.5 2.5L7.5 13.5L13.5 13.5L13.5 2.5L7.5 2.5Z" fill="#10B981"/>
      </g>
      
      <text x="122.5" y="96" text-anchor="middle" font-size="20" font-weight="800" fill="#065F46">Code</text>
      <!-- Re-included subtitle -->
      <text x="122.5" y="118" text-anchor="middle" font-size="11" font-weight="700" fill="#047857">Notebook, Python, Wheel Dependencies</text>
    </g>

    <!-- Database Component (Lower Right Cylinder, Solid Flat Color) -->
    <g id="database-node" transform="translate(970, 355)">
      <!-- Cylinder Path (Plain Solid Color Fill) -->
      <path d="M 0 20 L 0 135 A 117.5 20 0 0 0 235 135 L 235 20 Z" fill="#F0F9FF" stroke="#0284C7" stroke-width="2"/>
      <!-- Top ellipse -->
      <ellipse cx="117.5" cy="20" rx="117.5" ry="20" fill="#E0F2FE" stroke="#0284C7" stroke-width="2"/>
      <!-- Bottom ellipse outline -->
      <path d="M 0 135 A 117.5 20 0 0 0 235 135" fill="none" stroke="#0284C7" stroke-width="2"/>
      
      <!-- Header Badge -->
      <rect x="57" y="30" width="120" height="20" rx="5" fill="#BAE6FD"/>
      <text x="117.5" y="44" text-anchor="middle" font-size="10" font-weight="800" fill="#0369A1" letter-spacing="0.5">UNITY CATALOG</text>

      <!-- Official Delta Lake Icon -->
      <g transform="translate(100, 54) scale(0.42)">
        <path fill="#0284C7" d="M 51.328125 15.679688 C 50.625 14.464844 49.28125 13.695312 47.871094 13.695312 C 46.464844 13.695312 45.121094 14.464844 44.414062 15.679688 L 18.304688 60.929688 C 18.046875 61.441406 18.113281 62.078125 18.496094 62.464844 C 18.878906 62.847656 19.457031 62.976562 19.96875 62.785156 C 25.214844 60.480469 30.847656 59.199219 36.609375 59.070312 C 40.382812 59.007812 44.160156 59.96875 47.488281 61.761719 L 48.449219 60.097656 C 45.3125 58.238281 40.769531 57.089844 36.542969 57.089844 C 31.167969 57.214844 25.855469 58.304688 20.800781 60.289062 L 46.015625 16.640625 C 46.398438 16 47.105469 15.617188 47.808594 15.617188 C 48.574219 15.617188 49.214844 16 49.601562 16.640625 L 81.726562 70.527344 C 82.558594 71.871094 82.304688 73.664062 81.089844 74.753906 C 78.207031 77.3125 72.894531 80.382812 63.9375 80.382812 C 55.871094 80.382812 51.519531 77.824219 47.296875 75.390625 C 43.777344 73.34375 40.191406 71.230469 34.6875 70.785156 C 26.558594 70.144531 18.175781 73.792969 14.207031 75.648438 C 19.070312 69.054688 26.625 65.023438 34.753906 64.449219 C 41.792969 64 45.246094 66.046875 48.894531 68.222656 C 52.351562 70.273438 55.871094 72.382812 62.398438 72.382812 C 64.894531 72.382812 67.328125 71.9375 69.632812 71.105469 C 70.59375 70.785156 71.167969 69.695312 70.785156 68.734375 C 70.71875 68.609375 70.65625 68.480469 70.59375 68.351562 L 49.664062 32.769531 C 49.34375 32.191406 48.703125 31.808594 48 31.808594 C 47.296875 31.808594 46.65625 32.191406 46.273438 32.769531 L 36.160156 50.496094 C 35.648438 51.457031 35.96875 52.609375 36.863281 53.183594 C 37.054688 53.3125 37.246094 53.375 37.441406 53.375 C 41.664062 54.144531 45.695312 55.808594 49.28125 58.238281 L 50.367188 56.640625 C 46.65625 54.015625 42.367188 52.289062 37.886719 51.457031 L 37.886719 51.390625 L 48 33.664062 L 48.0625 33.664062 L 69.121094 69.3125 C 67.007812 70.078125 64.769531 70.464844 62.464844 70.464844 C 56.449219 70.464844 53.3125 68.542969 49.921875 66.558594 C 46.144531 64.320312 42.304688 62.015625 34.6875 62.464844 C 23.167969 63.167969 14.847656 70.65625 12.03125 75.457031 C 11.585938 76.222656 11.839844 77.183594 12.609375 77.632812 C 13.054688 77.886719 13.632812 77.953125 14.144531 77.695312 C 17.472656 76.097656 26.304688 71.871094 34.625 72.574219 C 39.679688 72.960938 42.945312 74.878906 46.464844 76.929688 C 50.878906 79.488281 55.488281 82.175781 64.0625 82.175781 C 73.601562 82.175781 79.359375 78.847656 82.496094 76.097656 C 84.351562 74.433594 84.800781 71.617188 83.519531 69.503906 Z M 51.328125 15.679688 "/>
      </g>
      
      <text x="117.5" y="122" text-anchor="middle" font-size="20" font-weight="800" fill="#0369A1">Database</text>
      <!-- Re-included subtitle -->
      <text x="117.5" y="142" text-anchor="middle" font-size="11" font-weight="700" fill="#0284C7">Unity Catalog</text>
    </g>
  </g>

  <!-- ================= CONNECTORS / FLOW ARROWS (PRECISELY ALIGNED) ================= -->

  <!-- 1. run-now: Client App Container -> DBx Jobs API -->
  <g id="flow-run-now">
    <path d="M 330 280 L 375 280" fill="none" stroke="#2563EB" stroke-width="2.6" marker-end="url(#arrow-blue)"/>
    <rect x="322" y="258" width="62" height="19" rx="4" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
    <text x="353" y="271" text-anchor="middle" font-size="10.5" font-weight="800" fill="#1D4ED8">run-now</text>
  </g>

  <!-- 2. returns: DBx Jobs API -> Client App Container -->
  <g id="flow-returns">
    <path d="M 375 360 L 330 360" fill="none" stroke="#2563EB" stroke-width="2.6" marker-end="url(#arrow-blue)"/>
    <rect x="329" y="366" width="48" height="19" rx="4" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
    <text x="353" y="379" text-anchor="middle" font-size="10.5" font-weight="800" fill="#1D4ED8">returns</text>
  </g>

  <!-- 3. POST /run-now: DBx Jobs API -> Cluster (Direct Trigger into Compute Engine) -->
  <g id="flow-api-to-cluster">
    <path d="M 575 280 L 680 280" fill="none" stroke="#EA580C" stroke-width="2.6" marker-end="url(#arrow-orange)"/>
    <rect x="586" y="256" width="84" height="20" rx="5" fill="#FFF7ED" stroke="#FFEDD5" stroke-width="1"/>
    <text x="628" y="270" text-anchor="middle" font-size="11" font-weight="800" fill="#C2410C">POST /run-now</text>
  </g>

  <!-- 4. Execution Done: Cluster -> DBx Jobs API (Dashed Return Flow) -->
  <g id="flow-execution-done">
    <path d="M 680 360 L 575 360" fill="none" stroke="#EA580C" stroke-width="2.4" stroke-dasharray="5 4" marker-end="url(#arrow-orange)"/>
    <rect x="583" y="336" width="88" height="20" rx="5" fill="#FFF7ED" stroke="#FFEDD5" stroke-width="1"/>
    <text x="627" y="350" text-anchor="middle" font-size="11" font-weight="800" fill="#C2410C">Execution Done</text>
  </g>

  <!-- 5. Code -> Cluster (Run Here) -->
  <g id="flow-run-here">
    <path d="M 965 215 C 930 220, 915 245, 900 275" fill="none" stroke="#10B981" stroke-width="2.6" marker-end="url(#arrow-green)"/>
    <rect x="898" y="202" width="66" height="20" rx="5" fill="#ECFDF5" stroke="#A7F3D0" stroke-width="1"/>
    <text x="931" y="216" text-anchor="middle" font-size="11" font-weight="800" fill="#047857">Run Here</text>
  </g>

  <!-- 6. Cluster -> Database (checks) -->
  <g id="flow-checks">
    <path d="M 900 345 C 922 360, 938 380, 970 395" fill="none" stroke="#0284C7" stroke-width="2.6" marker-end="url(#arrow-sky)"/>
    <rect x="908" y="350" width="54" height="20" rx="5" fill="#F0F9FF" stroke="#BAE6FD" stroke-width="1"/>
    <text x="935" y="364" text-anchor="middle" font-size="11" font-weight="800" fill="#0369A1">checks</text>
  </g>

  <!-- 7. Database -> Cluster (Record Result - Dashed Return Flow) -->
  <g id="flow-record-result">
    <path d="M 970 455 C 940 440, 922 420, 900 395" fill="none" stroke="#0284C7" stroke-width="2.4" stroke-dasharray="5 4" marker-end="url(#arrow-sky)"/>
    <rect x="898" y="435" width="84" height="20" rx="5" fill="#F0F9FF" stroke="#BAE6FD" stroke-width="1"/>
    <text x="940" y="449" text-anchor="middle" font-size="10.5" font-weight="800" fill="#0369A1">Record Result</text>
  </g>

</svg>
"""
    return svg


def build_presentation(svg_path: Path, png_path: Path, output_pptx: Path):
    """
    Build exactly 1-slide PowerPoint presentation with 100% native, fully editable DrawingML shapes, text boxes, and connectors.
    """
    from scripts.compile_native_databricks_jobs_pptx import build_native_deck
    build_native_deck(output_pptx)
    print(f"✓ Saved 100% Native, Fully Editable Single-Slide Presentation to: {output_pptx}")



def main():
    print("Starting Databricks Jobs API visualization compiler...")
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "diagrams").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "presentations").mkdir(parents=True, exist_ok=True)

    # 1. Generate Draw.io XML
    xml_content = create_drawio_xml()
    drawio_path = TEMP_DIR / "databricks_jobs_api_architecture.drawio"
    drawio_path.write_text(xml_content, encoding="utf-8")
    print(f"✓ Saved Draw.io XML: {drawio_path}")

    # 2. Generate Standalone High-Fidelity SVG
    svg_content = create_high_fidelity_svg()
    svg_path = TEMP_DIR / "databricks_jobs_api_architecture.svg"
    svg_path.write_text(svg_content, encoding="utf-8")
    (OUTPUT_DIR / "diagrams" / "databricks_jobs_api_architecture.svg").write_text(svg_content, encoding="utf-8")
    print(f"✓ Saved SVG companion: {svg_path}")

    # 3. Export High-Resolution PNG via rsvg-convert (3x zoom / 300+ DPI)
    png_path = TEMP_DIR / "databricks_jobs_api_architecture.png"
    out_png_path = OUTPUT_DIR / "diagrams" / "databricks_jobs_api_architecture.png"
    res = subprocess.run(["/opt/homebrew/bin/rsvg-convert", "-z", "3", str(svg_path), "-o", str(png_path)], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"✓ Exported High-Resolution PNG: {png_path}")
        shutil.copy2(png_path, out_png_path)
    else:
        print(f"rsvg-convert failed: {res.stderr}")

    # 4. Copy PNG to artifact directory
    if ARTIFACT_DIR.exists() and png_path.exists():
        artifact_png = ARTIFACT_DIR / "databricks_jobs_api_architecture.png"
        shutil.copy2(png_path, artifact_png)
        print(f"✓ Copied PNG to artifact directory: {artifact_png}")

    # 5. Build hybrid .drawio.svg
    escaped_xml = html.escape(xml_content, quote=True)
    svg_with_content = re.sub(r"<svg(\s+)", rf'<svg content="{escaped_xml}"\1', svg_content, count=1)
    desc_tag = f'\n  <desc><![CDATA[{xml_content}]]></desc>\n'
    idx = svg_with_content.rfind("</svg>")
    hybrid_svg = svg_with_content[:idx] + desc_tag + svg_with_content[idx:]
    drawio_svg_path = TEMP_DIR / "databricks_jobs_api_architecture.drawio.svg"
    drawio_svg_path.write_text(hybrid_svg, encoding="utf-8")
    print(f"✓ Generated hybrid .drawio.svg: {drawio_svg_path}")

    # 6. Update master project TEMP/device_whitelist_system.drawio
    master_drawio = TEMP_DIR / "device_whitelist_system.drawio"
    if master_drawio.exists():
        try:
            master_tree = ET.parse(master_drawio)
            master_root = master_tree.getroot()
            for diag in list(master_root.findall("diagram")):
                if diag.attrib.get("id") == "databricks_jobs_api" or "Databricks Jobs API" in diag.attrib.get("name", ""):
                    master_root.remove(diag)
            new_tree = ET.parse(drawio_path)
            master_root.append(new_tree.getroot().find("diagram"))
            raw = ET.tostring(master_root, encoding="utf-8")
            master_drawio.write_text(minidom.parseString(raw).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8"))
            print(f"✓ Updated master project: {master_drawio}")
        except Exception as e:
            print(f"Warning: Could not update master project: {e}")

    # 7. Generate browser URL and launcher
    compressor = zlib.compressobj(level=9, method=zlib.DEFLATED, wbits=-15)
    deflated = compressor.compress(xml_content.encode('utf-8')) + compressor.flush()
    b64 = base64.b64encode(deflated).decode('ascii')
    url_encoded = urllib.parse.quote(b64)
    new_url = f"https://app.diagrams.net/#R{url_encoded}"

    html_file = TEMP_DIR / "open_databricks_jobs_in_browser.html"
    html_file.write_text(f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url='{new_url}'" />
    <title>Opening Databricks Jobs API in Draw.io...</title>
</head>
<body>
    <p>Opening updated diagram in Draw.io... If not redirected, <a href="{new_url}">click here</a>.</p>
</body>
</html>""", encoding="utf-8")
    print(f"✓ Updated browser launcher: {html_file}")

    # 8. Build Presentation Deck (EXACTLY 1-SLIDE WITH NATIVE VECTOR SVG)
    pptx_path = TEMP_DIR / "databricks_jobs_api_architecture.pptx"
    out_pptx_path = OUTPUT_DIR / "presentations" / "databricks_jobs_api_architecture.pptx"
    build_presentation(svg_path, png_path, pptx_path)
    shutil.copy2(pptx_path, out_pptx_path)

    # 9. Update TEMP/index.html & TEMP/README.md
    update_index_and_readme()
    print("All tasks completed successfully!")


def update_index_and_readme():
    index_file = TEMP_DIR / "index.html"
    readme_file = TEMP_DIR / "README.md"

    card_html = """
            <div class="card" style="border-top: 4px solid #EA580C;">
                <span class="badge" style="background:#FFEDD5; color:#C2410C;">NEW ARTIFACT</span>
                <h2>Databricks Jobs API Architecture</h2>
                <p>Client 'run-now' execution orchestrator triggering Databricks Spark clusters to execute task code and validate Delta Lake database records.</p>
                <div class="links">
                    <a class="btn-primary" href="open_databricks_jobs_in_browser.html" target="_blank" style="background:#EA580C;">Open in Draw.io</a>
                    <a class="btn-secondary" href="databricks_jobs_api_architecture.png" target="_blank">View PNG (300 DPI)</a>
                    <a class="btn-secondary" href="databricks_jobs_api_architecture.svg" target="_blank">Vector SVG</a>
                    <a class="btn-secondary" href="databricks_jobs_api_architecture.pptx" download>Download Deck (.pptx)</a>
                </div>
            </div>"""

    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        if "databricks_jobs_api_architecture" not in content:
            content = content.replace('<div class="grid">', f'<div class="grid">\n{card_html}')
            index_file.write_text(content, encoding="utf-8")
            print("✓ Updated TEMP/index.html")

    if readme_file.exists():
        content = readme_file.read_text(encoding="utf-8")
        row = "| [`TEMP/databricks_jobs_api_architecture.drawio`](databricks_jobs_api_architecture.drawio) / [SVG](databricks_jobs_api_architecture.svg) / [PNG](databricks_jobs_api_architecture.png) | Vector / Raster / XML | **Databricks Jobs API Architecture**: Client-initiated `run-now` workflow executing Code on Spark cluster with Delta Lake verification. |\n| [`TEMP/databricks_jobs_api_architecture.pptx`](databricks_jobs_api_architecture.pptx) | Native PowerPoint (.pptx) | Single-slide presentation embedding native vector SVG plate. |\n"
        if "databricks_jobs_api_architecture" not in content and "| Artifact |" in content:
            parts = content.split("| :--- | :--- | :--- |\n", 1)
            if len(parts) == 2:
                new_content = parts[0] + "| :--- | :--- | :--- |\n" + row + parts[1]
                readme_file.write_text(new_content, encoding="utf-8")
                print("✓ Updated TEMP/README.md")


if __name__ == "__main__":
    main()
