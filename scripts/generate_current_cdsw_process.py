import sys
import shutil
import subprocess
import zlib
import base64
import urllib.parse
from pathlib import Path

import re

# Load Cloudera CML / CDSW Product Emblem SVG
cloudera_svg_path = Path("assets/logos/cloudera/cloudera_cdsw.svg")
cml_svg_text = cloudera_svg_path.read_text(encoding="utf-8")
cml_path_match = re.search(r'd="([^"]+)"', cml_svg_text)
cml_path_d = cml_path_match.group(1) if cml_path_match else ""

cloudera_b64 = base64.b64encode(cloudera_svg_path.read_bytes()).decode("ascii")
cloudera_data_uri = f"data:image/svg+xml;base64,{cloudera_b64}"

def create_drawio_xml():
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="Electron" agent="Enterprise Bench Diagram Engine" version="21.0.0" type="device">
  <diagram id="current_cdsw_process" name="Current : Legacy CDSW Job">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="720" background="#FFFFFF" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- TITLE / HEADER -->
        <mxCell id="header_title" value="&lt;b style=&quot;font-size:24px; color:#0F172A; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;&quot;&gt;Current: Legacy CDSW Job Execution&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:13px; color:#64748B;&quot;&gt;Monolithic Synchronous Batch Processing &amp;amp; Bottleneck Lifecycle Dataflow&lt;/span&gt;" style="text;html=1;align=left;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="50" y="30" width="460" height="50" as="geometry"/>
        </mxCell>

        <!-- ZONE 1: CLIENT APPS CLUSTER CONTAINER -->
        <mxCell id="group_apps" value="Client Applications" style="rounded=1;arcSize=18;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#94A3B8;strokeWidth=2;fillColor=#F8FAFC;fillOpacity=50;fontFamily=Helvetica, Arial, sans-serif;fontColor=#475569;fontSize=13;fontStyle=2;align=center;verticalAlign=top;spacingTop=14;" vertex="1" parent="1">
          <mxGeometry x="60" y="130" width="310" height="390" as="geometry"/>
        </mxCell>

        <!-- APP 1 / DEVICE 1 (TOP) -->
        <mxCell id="node_app1" value="&lt;div style=&quot;font-weight:700; font-size:15px; color:#1E3A8A; margin-bottom:4px;&quot;&gt;app1&lt;/div&gt;&lt;div style=&quot;font-size:22px;&quot;&gt;🖥️&lt;/div&gt;&lt;div style=&quot;font-size:11px; color:#64748B; margin-top:2px;&quot;&gt;Device 1&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="150" y="175" width="130" height="95" as="geometry"/>
        </mxCell>

        <!-- APP 2 / DEVICE 2 (BOTTOM LEFT) -->
        <mxCell id="node_app2" value="&lt;div style=&quot;font-weight:700; font-size:15px; color:#1E3A8A; margin-bottom:4px;&quot;&gt;app2&lt;/div&gt;&lt;div style=&quot;font-size:22px;&quot;&gt;🖥️&lt;/div&gt;&lt;div style=&quot;font-size:11px; color:#64748B; margin-top:2px;&quot;&gt;Device 2&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="85" y="350" width="120" height="95" as="geometry"/>
        </mxCell>

        <!-- APP 3 / DEVICE 3 (BOTTOM RIGHT) -->
        <mxCell id="node_app3" value="&lt;div style=&quot;font-weight:700; font-size:15px; color:#1E3A8A; margin-bottom:4px;&quot;&gt;app3&lt;/div&gt;&lt;div style=&quot;font-size:22px;&quot;&gt;🖥️&lt;/div&gt;&lt;div style=&quot;font-size:11px; color:#64748B; margin-top:2px;&quot;&gt;Device 3&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="230" y="350" width="120" height="95" as="geometry"/>
        </mxCell>

        <!-- ZONE 2: BACKEND EXECUTION BOUNDARY -->
        <mxCell id="group_backend" value="Backend Execution Boundary" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#F59E0B;strokeWidth=2;fillColor=#FFFBEB;fillOpacity=35;fontFamily=Helvetica, Arial, sans-serif;fontColor=#B45309;fontSize=13;fontStyle=1;align=right;verticalAlign=bottom;spacingRight=18;spacingBottom=12;" vertex="1" parent="1">
          <mxGeometry x="420" y="130" width="700" height="390" as="geometry"/>
        </mxCell>

        <!-- CDSW JOB (CLEAN BLUE CARD WITH CLOUDERA LOGO, NO ORCHESTRATOR) -->
        <mxCell id="node_cdsw" value="&lt;div style=&quot;margin-bottom:6px;&quot;&gt;&lt;img src=&quot;{cloudera_data_uri}&quot; width=&quot;28&quot; height=&quot;28&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-size:18px; font-weight:800; color:#0F172A;&quot;&gt;CDSW JOB&lt;/div&gt;&lt;div style=&quot;font-size:11px; color:#475569; margin-top:3px;&quot;&gt;Cloudera Data Science&lt;/div&gt;&lt;div style=&quot;font-size:10px; color:#64748B;&quot;&gt;Workbench Job Runner&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#0284C7;strokeWidth=2.5;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="450" y="235" width="180" height="120" as="geometry"/>
        </mxCell>

        <!-- WARNING BADGES (OUTSIDE THE RED SQUARE) -->
        <mxCell id="node_warnings" value="&lt;div style=&quot;display:flex; gap:8px;&quot;&gt;&lt;span style=&quot;background:#FEE2E2; color:#DC2626; font-size:10px; font-weight:800; padding:3px 8px; border-radius:4px; border:1px solid #FECACA;&quot;&gt;⚠️ BOTTLENECK&lt;/span&gt; &lt;span style=&quot;background:#FEF3C7; color:#B45309; font-size:10px; font-weight:800; padding:3px 8px; border-radius:4px; border:1px solid #FDE68A;&quot;&gt;⚠️ SYNCHRONOUS&lt;/span&gt;&lt;/div&gt;" style="text;html=1;align=left;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="720" y="180" width="220" height="30" as="geometry"/>
        </mxCell>

        <!-- 1 TASK (STANDALONE SQUARE/RECTANGULAR BOX) -->
        <mxCell id="node_task" value="&lt;div style=&quot;font-size:22px; font-weight:800; color:#0F172A;&quot;&gt;&lt;u&gt;1&lt;/u&gt; Task&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#DC2626;strokeWidth=2.5;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="720" y="225" width="160" height="75" as="geometry"/>
        </mxCell>

        <!-- BULLET LIST (OUTSIDE THE RED BOX, SOLID BLACK TEXT, NO DASHES) -->
        <mxCell id="node_task_steps" value="&lt;div style=&quot;text-align:left; font-size:14px; font-family:Helvetica, Arial, sans-serif; color:#0F172A; line-height:2.0;&quot;&gt;&lt;b&gt;• Input metadata&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• SQL Query&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• Filter &amp;amp; Search Dev. ADD&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• Logging&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• Return to sender&lt;/b&gt;&lt;/div&gt;" style="text;html=1;align=left;verticalAlign=top;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="720" y="320" width="240" height="135" as="geometry"/>
        </mxCell>

        <!-- CONNECTORS / FLOW ARROWS -->

        <!-- 1. APPS CLUSTER -> CDSW JOB (EXE TRIGGER) -->
        <mxCell id="edge_apps_to_cdsw" value="1. EXE Call" style="edgeStyle=curvedEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#2563EB;strokeWidth=2.5;fontColor=#1D4ED8;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;exitX=1;exitY=0.25;entryX=0;entryY=0.5;" edge="1" parent="1" source="group_apps" target="node_cdsw">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="400" y="190"/>
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- 2. CDSW JOB -> 1 TASK (2. RUN) -->
        <mxCell id="edge_cdsw_to_task" value="2. Run" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#0284C7;strokeWidth=2.5;fontColor=#0369A1;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;" edge="1" parent="1" source="node_cdsw" target="node_task">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 3. TASK AREA -> RETURN FLOW (3. Return, curved loop to clients) -->
        <mxCell id="edge_task_to_return" value="3. Return" style="edgeStyle=curvedEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#D97706;strokeWidth=2.5;fontColor=#B45309;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;exitX=1;exitY=0.5;entryX=0.9;entryY=0.95;" edge="1" parent="1" source="node_task" target="group_apps">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="1050" y="262"/>
              <mxPoint x="1050" y="555"/>
              <mxPoint x="420" y="555"/>
            </Array>
          </mxGeometry>
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""
    return xml.strip()

def create_high_fidelity_svg():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1180 660" width="1180" height="660">
  <defs>
    <!-- Drop Shadows -->
    <filter id="shadow" x="-8%" y="-8%" width="120%" height="125%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0F172A" flood-opacity="0.08"/>
    </filter>
    <filter id="card-shadow" x="-5%" y="-5%" width="114%" height="118%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#0F172A" flood-opacity="0.06"/>
    </filter>

    <!-- Arrow Markers -->
    <marker id="arrow-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#2563EB"/>
    </marker>
    <marker id="arrow-cyan" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#0284C7"/>
    </marker>
    <marker id="arrow-amber" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#D97706"/>
    </marker>
  </defs>

  <!-- Clean Canvas Background -->
  <rect width="1180" height="660" fill="#FFFFFF"/>
  <rect width="1180" height="660" fill="#F8FAFC" opacity="0.45"/>

  <!-- Subtle Blueprint Grid Pattern -->
  <g stroke="#E2E8F0" stroke-width="0.75" opacity="0.6">
    <path d="M 0 60 L 1180 60 M 0 120 L 1180 120 M 0 180 L 1180 180 M 0 240 L 1180 240 M 0 300 L 1180 300 M 0 360 L 1180 360 M 0 420 L 1180 420 M 0 480 L 1180 480 M 0 540 L 1180 540 M 0 600 L 1180 600" />
    <path d="M 60 0 L 60 660 M 120 0 L 120 660 M 180 0 L 180 660 M 240 0 L 240 660 M 300 0 L 300 660 M 360 0 L 360 660 M 420 0 L 420 660 M 480 0 L 480 660 M 540 0 L 540 660 M 600 0 L 600 660 M 660 0 L 660 660 M 720 0 L 720 660 M 780 0 L 780 660 M 840 0 L 840 660 M 900 0 L 900 660 M 960 0 L 960 660 M 1020 0 L 1020 660 M 1080 0 L 1080 660 M 1120 0 L 1120 660" />
  </g>

  <!-- ================= HEADER SECTION ================= -->
  <!-- Brand Stripes (1 Red : 2 Blue Ratio) -->
  <rect x="50" y="32" width="4.5" height="32" fill="#E11D48" rx="1"/>
  <rect x="56" y="32" width="9" height="32" fill="#0284C7" rx="1"/>
  <text x="76" y="47" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="22" font-weight="800" fill="#0F172A">Current: Legacy CDSW Job Execution</text>
  <text x="76" y="65" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="12" font-weight="500" fill="#64748B">Monolithic Synchronous Batch Processing &amp; Bottleneck Lifecycle Dataflow</text>

  <!-- ================= ZONE 1: CLIENT APPS CONTAINER ================= -->
  <g>
    <!-- Cluster Boundary -->
    <rect x="60" y="130" width="310" height="390" rx="36" fill="#F8FAFC" stroke="#94A3B8" stroke-width="2" stroke-dasharray="8,6" opacity="0.95"/>
    <text x="215" y="156" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="700" fill="#64748B" text-anchor="middle" letter-spacing="0.5">CLIENT APPLICATIONS</text>

    <!-- App 1 / Device 1 (Top Center) -->
    <g filter="url(#card-shadow)">
      <rect x="150" y="175" width="130" height="95" rx="12" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
      <text x="215" y="200" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="800" fill="#1E3A8A" text-anchor="middle">app1</text>
      <!-- Lucide Monitor Device Icon -->
      <g transform="translate(201, 208) scale(1.15)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect width="20" height="14" x="2" y="3" rx="2"/>
        <path d="M8 21h8m-4-4v4"/>
      </g>
      <text x="215" y="258" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="600" fill="#64748B" text-anchor="middle">Device 1</text>
    </g>

    <!-- App 2 / Device 2 (Bottom Left) -->
    <g filter="url(#card-shadow)">
      <rect x="85" y="350" width="120" height="95" rx="12" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
      <text x="145" y="375" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="800" fill="#1E3A8A" text-anchor="middle">app2</text>
      <!-- Lucide Monitor Device Icon -->
      <g transform="translate(131, 383) scale(1.15)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect width="20" height="14" x="2" y="3" rx="2"/>
        <path d="M8 21h8m-4-4v4"/>
      </g>
      <text x="145" y="433" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="600" fill="#64748B" text-anchor="middle">Device 2</text>
    </g>

    <!-- App 3 / Device 3 (Bottom Right) -->
    <g filter="url(#card-shadow)">
      <rect x="230" y="350" width="120" height="95" rx="12" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
      <text x="290" y="375" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="800" fill="#1E3A8A" text-anchor="middle">app3</text>
      <!-- Lucide Monitor Device Icon -->
      <g transform="translate(276, 383) scale(1.15)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect width="20" height="14" x="2" y="3" rx="2"/>
        <path d="M8 21h8m-4-4v4"/>
      </g>
      <text x="290" y="433" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="600" fill="#64748B" text-anchor="middle">Device 3</text>
    </g>
  </g>

  <!-- ================= ZONE 2: BACKEND EXECUTION BOUNDARY ================= -->
  <g>
    <!-- Boundary Container -->
    <rect x="420" y="130" width="700" height="390" rx="20" fill="#FFFBEB" fill-opacity="0.3" stroke="#F59E0B" stroke-width="2" stroke-dasharray="8,6"/>
    <!-- Boundary Label Badge -->
    <g transform="translate(970, 145)">
      <rect width="132" height="24" rx="5" fill="#FEF3C7" stroke="#FDE68A" stroke-width="1"/>
      <text x="66" y="16" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="800" fill="#B45309" text-anchor="middle" letter-spacing="0.5">CLOUDERA CDSW</text>
    </g>
    <text x="440" y="162" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="700" fill="#B45309">Backend Execution Boundary</text>

    <!-- CDSW JOB (Clean Blue Card with Official Cloudera Logo, No Orchestrator Badge) -->
    <g filter="url(#shadow)">
      <rect x="450" y="225" width="185" height="135" rx="14" fill="#FFFFFF" stroke="#0284C7" stroke-width="2.5"/>
      
      <!-- Authentic Cloudera CDSW / CML Product Emblem (28x28 px centered at x=528.5, y=245) -->
      <g transform="translate(528.5, 245) scale(0.1892)">
        <path d="{CML_PATH_D}" fill="#4CCF4C" fill-rule="evenodd"/>
      </g>

      <text x="542" y="298" font-family="Helvetica, Arial, sans-serif" font-size="18" font-weight="800" fill="#0F172A" text-anchor="middle">CDSW JOB</text>
      <text x="542" y="320" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="#475569" text-anchor="middle">Cloudera Data Science</text>
      <text x="542" y="336" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="500" fill="#64748B" text-anchor="middle">Workbench Job Runner</text>
    </g>

    <!-- ================= 1 TASK ARCHITECTURE ================= -->

    <!-- WARNING BADGES (OUTSIDE THE RED SQUARE) -->
    <g transform="translate(720, 182)">
      <!-- Bottleneck Pill -->
      <rect width="104" height="22" rx="4" fill="#FEE2E2" stroke="#FECACA" stroke-width="1"/>
      <text x="52" y="15" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#DC2626" text-anchor="middle">⚠️ BOTTLENECK</text>
      
      <!-- Synchronous Pill -->
      <rect x="114" width="116" height="22" rx="4" fill="#FEF3C7" stroke="#FDE68A" stroke-width="1"/>
      <text x="172" y="15" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#B45309" text-anchor="middle">⚠️ SYNCHRONOUS</text>
    </g>

    <!-- 1 TASK SQUARE (STANDALONE RED CARD) -->
    <g filter="url(#shadow)">
      <rect x="720" y="220" width="160" height="75" rx="10" fill="#FFFFFF" stroke="#DC2626" stroke-width="2.5"/>
      <text x="800" y="266" font-family="Helvetica, Arial, sans-serif" font-size="22" font-weight="800" fill="#0F172A" text-anchor="middle"><tspan text-decoration="underline">1</tspan> Task</text>
    </g>

    <!-- BULLET LIST (OUTSIDE THE RED BOX, SOLID BLACK TEXT, NO DASHES) -->
    <g transform="translate(720, 325)" font-family="Helvetica, Arial, sans-serif">
      <!-- Bullet 1 -->
      <circle cx="6" cy="10" r="3" fill="#0F172A"/>
      <text x="18" y="15" font-size="14" font-weight="700" fill="#0F172A">Input metadata</text>

      <!-- Bullet 2 -->
      <circle cx="6" cy="36" r="3" fill="#0F172A"/>
      <text x="18" y="41" font-size="14" font-weight="700" fill="#0F172A">SQL Query</text>

      <!-- Bullet 3 -->
      <circle cx="6" cy="62" r="3" fill="#0F172A"/>
      <text x="18" y="67" font-size="14" font-weight="700" fill="#0F172A">Filter &amp; Search Dev. ADD</text>

      <!-- Bullet 4 -->
      <circle cx="6" cy="88" r="3" fill="#0F172A"/>
      <text x="18" y="93" font-size="14" font-weight="700" fill="#0F172A">Logging</text>

      <!-- Bullet 5 -->
      <circle cx="6" cy="114" r="3" fill="#0F172A"/>
      <text x="18" y="119" font-size="14" font-weight="700" fill="#0F172A">Return to sender</text>
    </g>
  </g>

  <!-- ================= FLOW CONNECTORS / CYCLE ARROWS ================= -->

  <!-- 1. APPS CLUSTER -> CDSW JOB (Request Arc) -->
  <path d="M 315 180 C 375 145, 410 200, 448 250" fill="none" stroke="#2563EB" stroke-width="2.5" marker-end="url(#arrow-blue)"/>
  <rect x="345" y="150" width="76" height="20" rx="4" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
  <text x="383" y="164" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="700" fill="#1D4ED8" text-anchor="middle">1. EXE Call</text>

  <!-- 2. CDSW JOB -> 1 TASK (2. RUN) -->
  <path d="M 635 258 L 712 258" fill="none" stroke="#0284C7" stroke-width="2.5" marker-end="url(#arrow-cyan)"/>
  <rect x="646" y="248" width="52" height="18" rx="4" fill="#F0F9FF" stroke="#BAE6FD" stroke-width="1"/>
  <text x="672" y="261" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="700" fill="#0369A1" text-anchor="middle">2. Run</text>

  <!-- 3. TASK AREA -> RETURN FLOW (Looping gracefully around right and bottom) -->
  <path d="M 880 258 L 980 258 C 1060 258, 1060 545, 850 545 L 340 545 C 290 545, 270 515, 270 450" fill="none" stroke="#D97706" stroke-width="2.5" marker-end="url(#arrow-amber)"/>
  
  <!-- Step 3. Return Badge -->
  <rect x="940" y="535" width="82" height="20" rx="4" fill="#FFFBEB" stroke="#FDE68A" stroke-width="1"/>
  <text x="981" y="549" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="700" fill="#B45309" text-anchor="middle">3. Return</text>

  <!-- Step 4. Response Badge -->
  <rect x="420" y="535" width="90" height="20" rx="4" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
  <text x="465" y="549" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="700" fill="#1D4ED8" text-anchor="middle">4. Response</text>

</svg>
"""
    return svg.replace("{CML_PATH_D}", cml_path_d)

def main():
    drawio_path = Path("output/diagrams/current_process_cdsw.drawio")
    svg_path = Path("output/diagrams/current_process_cdsw.svg")
    png_path = Path("output/diagrams/current_process_cdsw.png")

    temp_drawio = Path("TEMP/current_process_to_update.drawio")
    temp_svg = Path("TEMP/current_process_to_update.svg")
    temp_png = Path("TEMP/current_process_to_update.png")

    drawio_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Write Draw.io mxGraph XML file
    xml_content = create_drawio_xml()
    drawio_path.write_text(xml_content, encoding="utf-8")
    temp_drawio.write_text(xml_content, encoding="utf-8")
    print(f"✓ Saved Draw.io XML to: {drawio_path} and {temp_drawio}")

    # 2. Write SVG companion file
    svg_content = create_high_fidelity_svg()
    svg_path.write_text(svg_content, encoding="utf-8")
    temp_svg.write_text(svg_content, encoding="utf-8")
    print(f"✓ Saved SVG companion to: {svg_path} and {temp_svg}")

    # 3. Export to High-Resolution PNG (3x zoom / 300+ DPI)
    res = subprocess.run(["rsvg-convert", "-z", "3", str(svg_path), "-o", str(png_path)], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"✓ Exported High-Resolution PNG to: {png_path} using rsvg-convert")
        shutil.copy2(png_path, temp_png)
    else:
        from src.ppt_engine.diagram_engine import _setup_cairo_library
        _setup_cairo_library()
        import cairosvg
        cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), write_to=str(png_path), scale=2.5)
        shutil.copy2(png_path, temp_png)
        print(f"✓ Exported High-Resolution PNG via cairosvg")

    # 4. Copy PNG to artifact directory
    artifact_dir = Path("/Users/marcelljw/.gemini/antigravity/brain/c95641a2-cc71-4bd6-b9c4-46d8624c2e12")
    artifact_png = artifact_dir / "current_process_cdsw.png"
    shutil.copy2(png_path, artifact_png)
    print(f"✓ Copied PNG to artifact directory: {artifact_png}")

    # 5. Generate browser URL
    compressor = zlib.compressobj(level=9, method=zlib.DEFLATED, wbits=-15)
    deflated = compressor.compress(xml_content.encode('utf-8')) + compressor.flush()
    b64 = base64.b64encode(deflated).decode('ascii')
    url_encoded = urllib.parse.quote(b64)
    new_url = f"https://app.diagrams.net/#R{url_encoded}"

    html_file = Path("TEMP/open_in_browser.html")
    html_file.write_text(f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url='{new_url}'" />
    <title>Opening Current Process in Draw.io...</title>
</head>
<body>
    <p>Opening updated diagram in Draw.io... If not redirected, <a href="{new_url}">click here</a>.</p>
</body>
</html>""", encoding="utf-8")
    print(f"✓ Updated browser launcher: {html_file}")

    # Update master project
    master_drawio = Path("TEMP/device_whitelist_system.drawio")
    if master_drawio.exists():
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        master_tree = ET.parse(master_drawio)
        master_root = master_tree.getroot()
        for diag in master_root.findall("diagram"):
            if diag.attrib.get("id") in ("current_cdsw_process", "current_process_to_update") or "Current" in diag.attrib.get("name", ""):
                master_root.remove(diag)
        new_tree = ET.parse(drawio_path)
        master_root.append(new_tree.getroot().find("diagram"))
        raw = ET.tostring(master_root, encoding="utf-8")
        master_drawio.write_text(minidom.parseString(raw).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8"))
        print(f"✓ Updated master project: {master_drawio}")

if __name__ == "__main__":
    main()
