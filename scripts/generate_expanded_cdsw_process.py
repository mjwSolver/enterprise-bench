#!/usr/bin/env python3
"""
Generate Expanded Legacy CDSW Job Execution Architecture Diagram & PowerPoint Slide.

Incorporate detailed client-side hardware Safe-Checker topology based on stakeholder sketch:
1. User Origin on far left with functional roles (Security, Finance, Fraud Operations).
2. "Trigger" connector leading into Local Device host environment.
3. Expanded "EXE" element ("Can be more than 1 type with different programs") connected via "runs" to Safe Checker.
4. "Safe Checker" pre-execution hardware whitelist verifier:
   - Connect to CDSW
   - Get MAC Address
   - Send API request ke CDSW (forward ingress flow)
   - Receive Status from CDSW (backward egress flow)
   - If / Else decision branch:
     * Allowed -> Continue with the rest of exe
     * Not Allowed -> Stopped
5. Retains full high-fidelity Cloudera CDSW backend execution boundary (CDSW JOB + 1 Task bottleneck).
"""

import sys
import shutil
import subprocess
import zlib
import base64
import urllib.parse
import re
from pathlib import Path

# Paths
REPO_ROOT = Path("/Users/marcelljw/VisualStudioCode/enterprise-bench")
CLOUDERA_SVG_PATH = REPO_ROOT / "assets/logos/cloudera/cloudera_cdsw.svg"

cml_path_d = ""
cloudera_data_uri = ""
if CLOUDERA_SVG_PATH.exists():
    cml_svg_text = CLOUDERA_SVG_PATH.read_text(encoding="utf-8")
    cml_path_match = re.search(r'd="([^"]+)"', cml_svg_text)
    cml_path_d = cml_path_match.group(1) if cml_path_match else ""
    cloudera_b64 = base64.b64encode(CLOUDERA_SVG_PATH.read_bytes()).decode("ascii")
    cloudera_data_uri = f"data:image/svg+xml;base64,{cloudera_b64}"


def create_drawio_xml() -> str:
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="Electron" agent="Enterprise Bench Diagram Engine" version="21.0.0" type="device">
  <diagram id="expanded_cdsw_process" name="Current : Expanded Hardware Safe-Checker">
    <mxGraphModel dx="1400" dy="850" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1340" pageHeight="750" background="#FFFFFF" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- ================= TITLE / HEADER ================= -->
        <mxCell id="header_title" value="&lt;b style=&quot;font-size:22px; color:#0F172A; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;&quot;&gt;Current: Legacy CDSW Job Execution (Expanded Hardware Safe-Checker)&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:12.5px; color:#64748B;&quot;&gt;Client Hardware Whitelist Verification, Monolithic Batch Execution &amp;amp; Bottleneck Lifecycle Dataflow&lt;/span&gt;" style="text;html=1;align=left;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="50" y="28" width="800" height="48" as="geometry"/>
        </mxCell>

        <!-- TOP RIGHT STATUS BADGE -->
        <mxCell id="header_badge" value="&lt;div style=&quot;background:#EFF6FF; border:1px solid #BFDBFE; border-radius:6px; padding:5px 12px; color:#1D4ED8; font-weight:800; font-size:11px;&quot;&gt;CLIENT INGRESS EXPANSION&lt;/div&gt;" style="text;html=1;align=right;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="1080" y="32" width="200" height="36" as="geometry"/>
        </mxCell>

        <!-- ================= ZONE 1: USER ORIGIN ================= -->
        <mxCell id="group_user" value="User Origin" style="rounded=1;arcSize=14;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#94A3B8;strokeWidth=2;fillColor=#F8FAFC;fillOpacity=50;fontFamily=Helvetica, Arial, sans-serif;fontColor=#475569;fontSize=12;fontStyle=2;align=center;verticalAlign=top;spacingTop=12;" vertex="1" parent="1">
          <mxGeometry x="50" y="130" width="150" height="560" as="geometry"/>
        </mxCell>

        <!-- USER CARD -->
        <mxCell id="node_user" value="&lt;div style=&quot;font-size:32px; margin-bottom:4px;&quot;&gt;👤&lt;/div&gt;&lt;div style=&quot;font-weight:800; font-size:17px; color:#0F172A;&quot;&gt;User&lt;/div&gt;&lt;div style=&quot;font-size:11px; color:#64748B; margin-top:2px;&quot;&gt;Operator / Client&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=0;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="58" y="180" width="134" height="150" as="geometry"/>
        </mxCell>

        <!-- USER ROLE NOTES CONTAINER -->
        <mxCell id="node_user_notes" value="&lt;div style=&quot;text-align:left; font-family:Helvetica, Arial, sans-serif;&quot;&gt;&lt;div style=&quot;font-size:10px; font-weight:800; color:#64748B; letter-spacing:0.5px; margin-bottom:8px;&quot;&gt;DEPT / ROLES&lt;/div&gt;&lt;div style=&quot;font-size:11.5px; font-weight:700; color:#0F172A; line-height:1.7;&quot;&gt;• Security &lt;span style=&quot;font-size:10px; color:#64748B; font-weight:400;&quot;&gt;(SecOps)&lt;/span&gt;&lt;br/&gt;• Finance &lt;span style=&quot;font-size:10px; color:#64748B; font-weight:400;&quot;&gt;(Recon)&lt;/span&gt;&lt;br/&gt;• Fraud &lt;span style=&quot;font-size:10px; color:#64748B; font-weight:400;&quot;&gt;(Audit)&lt;/span&gt;&lt;/div&gt;&lt;div style=&quot;border-top:1px solid #E2E8F0; margin-top:10px; padding-top:8px; font-size:10px; color:#475569; line-height:1.4;&quot;&gt;Initiates local business executables requiring hardware authorization.&lt;/div&gt;&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#CBD5E1;strokeWidth=1.5;shadow=0;align=left;verticalAlign=top;spacing=10;" vertex="1" parent="1">
          <mxGeometry x="58" y="355" width="134" height="305" as="geometry"/>
        </mxCell>

        <!-- ================= ZONE 2: LOCAL DEVICE BOUNDARY ================= -->
        <mxCell id="group_device" value="Local Device" style="rounded=1;arcSize=14;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#64748B;strokeWidth=2;fillColor=#F8FAFC;fillOpacity=60;fontFamily=Helvetica, Arial, sans-serif;fontColor=#334155;fontSize=13;fontStyle=1;align=center;verticalAlign=top;spacingTop=12;" vertex="1" parent="1">
          <mxGeometry x="310" y="130" width="420" height="560" as="geometry"/>
        </mxCell>

        <!-- CLIENT HOST TAG -->
        <mxCell id="badge_device" value="&lt;span style=&quot;background:#E2E8F0; color:#475569; font-size:9.5px; font-weight:800; padding:2px 8px; border-radius:4px;&quot;&gt;CLIENT HOST&lt;/span&gt;" style="text;html=1;align=right;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="615" y="140" width="105" height="24" as="geometry"/>
        </mxCell>

        <!-- EXE CARD (Point 1 / Ingress Trigger) -->
        <mxCell id="node_exe" value="&lt;div style=&quot;font-size:28px; margin-bottom:2px;&quot;&gt;⚙️&lt;/div&gt;&lt;div style=&quot;font-weight:800; font-size:18px; color:#1E3A8A;&quot;&gt;EXE&lt;/div&gt;&lt;div style=&quot;font-size:11px; font-weight:600; color:#475569; margin-top:2px;&quot;&gt;Client Executable&lt;/div&gt;&lt;div style=&quot;font-size:9.5px; color:#64748B; margin-top:6px; line-height:1.3;&quot;&gt;Can be more than 1 type&lt;br/&gt;with different programs&lt;br/&gt;&lt;i&gt;(recon_tool, audit)&lt;/i&gt;&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=0;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="320" y="180" width="130" height="160" as="geometry"/>
        </mxCell>

        <!-- SAFE CHECKER CONTAINER -->
        <mxCell id="group_safe_checker" value="" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#0284C7;strokeWidth=2;shadow=0;" vertex="1" parent="1">
          <mxGeometry x="480" y="165" width="235" height="505" as="geometry"/>
        </mxCell>

        <!-- SAFE CHECKER HEADER -->
        <mxCell id="header_safe_checker" value="&lt;div style=&quot;font-size:13px; font-weight:800; color:#0369A1;&quot;&gt;🛡️ Safe Checker&lt;/div&gt;&lt;div style=&quot;font-size:10px; color:#64748B; margin-top:2px;&quot;&gt;Pre-Run Whitelist Verifier&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#E0F2FE;strokeColor=#BAE6FD;strokeWidth=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="490" y="180" width="215" height="42" as="geometry"/>
        </mxCell>

        <!-- STEP 1: Connect to CDSW -->
        <mxCell id="step_connect" value="&lt;b style=&quot;color:#0F172A;&quot;&gt;• Connect to CDSW&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#F8FAFC;strokeColor=#E2E8F0;strokeWidth=1;align=left;spacingLeft=10;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="490" y="234" width="215" height="32" as="geometry"/>
        </mxCell>

        <!-- STEP 2: Get MAC Addresses -->
        <mxCell id="step_mac" value="&lt;b style=&quot;color:#0F172A;&quot;&gt;• Get MAC Addresses&lt;/b&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#F8FAFC;strokeColor=#E2E8F0;strokeWidth=1;align=left;spacingLeft=10;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="490" y="274" width="215" height="32" as="geometry"/>
        </mxCell>

        <!-- STEP 3: Send Request API ke CDSW (Highlighted Ingress Box) -->
        <mxCell id="step_send_api" value="&lt;div style=&quot;font-weight:800; font-size:11px; color:#0369A1;&quot;&gt;📤 Send request API ke CDSW&lt;/div&gt;&lt;div style=&quot;font-size:9px; color:#0284C7;&quot;&gt;Payload: MAC + Client Identity&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#F0F9FF;strokeColor=#0284C7;strokeWidth=2;align=center;verticalAlign=middle;fontFamily=Helvetica, Arial, sans-serif;" vertex="1" parent="1">
          <mxGeometry x="490" y="318" width="215" height="50" as="geometry"/>
        </mxCell>

        <!-- STEP 4: Receive Status (Highlighted Return Box) -->
        <mxCell id="step_receive_status" value="&lt;div style=&quot;font-weight:800; font-size:11px; color:#B45309;&quot;&gt;📥 Receive Status&lt;/div&gt;&lt;div style=&quot;font-size:9px; color:#D97706;&quot;&gt;Status: Allowed / Not Allowed&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFBEB;strokeColor=#F59E0B;strokeWidth=2;align=center;verticalAlign=middle;fontFamily=Helvetica, Arial, sans-serif;" vertex="1" parent="1">
          <mxGeometry x="490" y="380" width="215" height="46" as="geometry"/>
        </mxCell>

        <!-- STEP 5: If / Else Branch Header -->
        <mxCell id="step_if_else" value="&lt;b style=&quot;color:#475569; font-size:10.5px;&quot;&gt;• If / Else Evaluation:&lt;/b&gt;" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="490" y="434" width="215" height="20" as="geometry"/>
        </mxCell>

        <!-- BRANCH 1: Allowed -->
        <mxCell id="card_allowed" value="&lt;div style=&quot;background:#DCFCE7; color:#15803D; font-size:9.5px; font-weight:800; padding:2px 6px; border-radius:4px; display:inline-block; border:1px solid #86EFAC; margin-bottom:6px;&quot;&gt;Allowed&lt;/div&gt;&lt;div style=&quot;font-size:15px; margin-bottom:4px;&quot;&gt;↓&lt;/div&gt;&lt;div style=&quot;font-weight:700; font-size:10px; color:#166534; line-height:1.3;&quot;&gt;Continue with&lt;br/&gt;the rest of exe&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#F0FDF4;strokeColor=#16A34A;strokeWidth=1.5;shadow=0;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;spacing=6;" vertex="1" parent="1">
          <mxGeometry x="490" y="460" width="102" height="195" as="geometry"/>
        </mxCell>

        <!-- BRANCH 2: Not Allowed -->
        <mxCell id="card_not_allowed" value="&lt;div style=&quot;background:#FEE2E2; color:#B91C1C; font-size:9.5px; font-weight:800; padding:2px 6px; border-radius:4px; display:inline-block; border:1px solid #FECACA; margin-bottom:6px;&quot;&gt;not Allowed&lt;/div&gt;&lt;div style=&quot;font-size:15px; margin-bottom:4px;&quot;&gt;↓&lt;/div&gt;&lt;div style=&quot;font-weight:700; font-size:10.5px; color:#991B1B; line-height:1.3;&quot;&gt;Stopped&lt;/div&gt;&lt;div style=&quot;font-size:9px; color:#DC2626; margin-top:6px;&quot;&gt;Execution&lt;br/&gt;Aborted&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#DC2626;strokeWidth=1.5;shadow=0;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;spacing=6;" vertex="1" parent="1">
          <mxGeometry x="603" y="460" width="102" height="195" as="geometry"/>
        </mxCell>

        <!-- ================= ZONE 3: BACKEND EXECUTION BOUNDARY ================= -->
        <mxCell id="group_backend" value="Backend Execution Boundary" style="rounded=1;arcSize=14;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#F59E0B;strokeWidth=2;fillColor=#FFFBEB;fillOpacity=35;fontFamily=Helvetica, Arial, sans-serif;fontColor=#B45309;fontSize=13;fontStyle=1;align=center;verticalAlign=top;spacingTop=12;" vertex="1" parent="1">
          <mxGeometry x="885" y="130" width="400" height="560" as="geometry"/>
        </mxCell>

        <!-- CDSW TAG -->
        <mxCell id="badge_cdsw" value="&lt;span style=&quot;background:#FEF3C7; color:#B45309; font-size:10px; font-weight:800; padding:3px 8px; border-radius:4px; border:1px solid #FDE68A;&quot;&gt;CLOUDERA CDSW&lt;/span&gt;" style="text;html=1;align=right;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="1140" y="140" width="130" height="24" as="geometry"/>
        </mxCell>

        <!-- CDSW JOB CARD -->
        <mxCell id="node_cdsw" value="&lt;div style=&quot;margin-bottom:6px;&quot;&gt;&lt;img src=&quot;{cloudera_data_uri}&quot; width=&quot;26&quot; height=&quot;26&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-size:16.5px; font-weight:800; color:#0F172A;&quot;&gt;CDSW JOB&lt;/div&gt;&lt;div style=&quot;font-size:10.5px; color:#475569; margin-top:3px;&quot;&gt;Cloudera Data Science&lt;/div&gt;&lt;div style=&quot;font-size:9.5px; color:#64748B;&quot;&gt;Workbench Job Runner&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#0284C7;strokeWidth=2.5;shadow=0;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="900" y="210" width="165" height="150" as="geometry"/>
        </mxCell>

        <!-- WARNING BADGES ABOVE 1 TASK -->
        <mxCell id="node_warnings" value="&lt;div style=&quot;display:flex; gap:6px;&quot;&gt;&lt;span style=&quot;background:#FEE2E2; color:#DC2626; font-size:9px; font-weight:800; padding:2px 6px; border-radius:4px; border:1px solid #FECACA;&quot;&gt;⚠️ BOTTLENECK&lt;/span&gt; &lt;span style=&quot;background:#FEF3C7; color:#B45309; font-size:9px; font-weight:800; padding:2px 6px; border-radius:4px; border:1px solid #FDE68A;&quot;&gt;⚠️ SYNCHRONOUS&lt;/span&gt;&lt;/div&gt;" style="text;html=1;align=left;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="1095" y="170" width="180" height="26" as="geometry"/>
        </mxCell>

        <!-- 1 TASK SQUARE (STANDALONE RED CARD) -->
        <mxCell id="node_task" value="&lt;div style=&quot;font-size:22px; font-weight:800; color:#0F172A;&quot;&gt;&lt;u&gt;1&lt;/u&gt; Task&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#DC2626;strokeWidth=2.5;shadow=0;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="1095" y="210" width="175" height="85" as="geometry"/>
        </mxCell>

        <!-- CDSW JOB EXECUTION STEPS (BULLET LIST) -->
        <mxCell id="node_task_steps" value="&lt;div style=&quot;text-align:left; font-size:12px; font-family:Helvetica, Arial, sans-serif; color:#0F172A; line-height:1.9;&quot;&gt;&lt;b&gt;• Input metadata&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• SQL Query (Filter &amp;amp; Search)&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• Filter &amp;amp; Search Dev. ADD&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• Logging&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• Return Result&lt;/b&gt;&lt;/div&gt;" style="text;html=1;align=left;verticalAlign=top;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="1095" y="315" width="180" height="135" as="geometry"/>
        </mxCell>

        <!-- ================= CONNECTORS / FLOW ARROWS ================= -->

        <!-- 1. USER -> EXE (Trigger) -->
        <mxCell id="edge_user_to_exe" value="Trigger" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#2563EB;strokeWidth=2.5;fontColor=#1D4ED8;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;" edge="1" parent="1" source="node_user" target="node_exe">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 2. EXE -> SAFE CHECKER (runs) -->
        <mxCell id="edge_exe_to_safe" value="runs" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#2563EB;strokeWidth=2.5;fontColor=#1D4ED8;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;exitX=1;exitY=0.5;entryX=0;entryY=0.25;" edge="1" parent="1" source="node_exe" target="group_safe_checker">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 3. SAFE CHECKER -> CDSW JOB (1. Send API Request ke CDSW) -->
        <mxCell id="edge_safe_to_cdsw" value="1. Send API Request" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#0284C7;strokeWidth=2.5;fontColor=#0369A1;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;" edge="1" parent="1" source="step_send_api" target="node_cdsw">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 4. CDSW JOB -> 1 TASK (2. Run) -->
        <mxCell id="edge_cdsw_to_task" value="2. Run" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#0284C7;strokeWidth=2.5;fontColor=#0369A1;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;exitX=1;exitY=0.35;entryX=0;entryY=0.5;" edge="1" parent="1" source="node_cdsw" target="node_task">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 5. CDSW JOB -> RECEIVE STATUS (3. Return Status) -->
        <mxCell id="edge_cdsw_to_receive" value="3. Return Status" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#D97706;strokeWidth=2.5;fontColor=#B45309;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;exitX=0;exitY=0.75;entryX=1;entryY=0.5;" edge="1" parent="1" source="node_cdsw" target="step_receive_status">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""
    return xml.strip()


def create_high_fidelity_svg() -> str:
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1340 730" width="1340" height="730">
  <defs>
    <!-- Card Shadow -->
    <filter id="shadow" x="-5%" y="-5%" width="112%" height="114%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#0F172A" flood-opacity="0.07"/>
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
    <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#16A34A"/>
    </marker>
    <marker id="arrow-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#DC2626"/>
    </marker>
  </defs>

  <!-- Canvas Background -->
  <rect width="1340" height="730" fill="#FFFFFF"/>
  <rect width="1340" height="730" fill="#F8FAFC" opacity="0.45"/>

  <!-- Subtle Blueprint Grid Pattern -->
  <g stroke="#E2E8F0" stroke-width="0.75" opacity="0.5">
    <path d="M 0 60 L 1340 60 M 0 120 L 1340 120 M 0 180 L 1340 180 M 0 240 L 1340 240 M 0 300 L 1340 300 M 0 360 L 1340 360 M 0 420 L 1340 420 M 0 480 L 1340 480 M 0 540 L 1340 540 M 0 600 L 1340 600 M 0 660 L 1340 660" />
    <path d="M 60 0 L 60 730 M 120 0 L 120 730 M 180 0 L 180 730 M 240 0 L 240 730 M 300 0 L 300 730 M 360 0 L 360 730 M 420 0 L 420 730 M 480 0 L 480 730 M 540 0 L 540 730 M 600 0 L 600 730 M 660 0 L 660 730 M 720 0 L 720 730 M 780 0 L 780 730 M 840 0 L 840 730 M 900 0 L 900 730 M 960 0 L 960 730 M 1020 0 L 1020 730 M 1080 0 L 1080 730 M 1140 0 L 1140 730 M 1200 0 L 1200 730 M 1260 0 L 1260 730" />
  </g>

  <!-- ================= HEADER SECTION ================= -->
  <rect x="50" y="32" width="4.5" height="34" fill="#E11D48" rx="1"/>
  <rect x="56" y="32" width="9" height="34" fill="#0284C7" rx="1"/>
  <text x="76" y="47" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="22" font-weight="800" fill="#0F172A">Current: Legacy CDSW Job Execution (Expanded Hardware Safe-Checker)</text>
  <text x="76" y="66" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="12" font-weight="500" fill="#64748B">Client Hardware Whitelist Verification, Monolithic Batch Execution &amp; Bottleneck Lifecycle Dataflow</text>

  <!-- Header Badge -->
  <g transform="translate(1110, 32)">
    <rect width="180" height="26" rx="5" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
    <text x="90" y="17" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="800" fill="#1D4ED8" text-anchor="middle" letter-spacing="0.5">CLIENT INGRESS EXPANSION</text>
  </g>

  <!-- ================= ZONE 1: USER ORIGIN ================= -->
  <g>
    <!-- Boundary Container -->
    <rect x="50" y="130" width="150" height="560" rx="14" fill="#F8FAFC" fill-opacity="0.8" stroke="#94A3B8" stroke-width="2" stroke-dasharray="8,6"/>
    <text x="125" y="155" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#64748B" text-anchor="middle" letter-spacing="0.5">USER ORIGIN</text>

    <!-- User Card -->
    <g filter="url(#shadow)">
      <rect x="58" y="180" width="134" height="150" rx="12" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
      <!-- User Icon SVG -->
      <g transform="translate(111, 198) scale(1.3)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </g>
      <text x="125" y="278" font-family="Helvetica, Arial, sans-serif" font-size="17" font-weight="800" fill="#0F172A" text-anchor="middle">User</text>
      <text x="125" y="298" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="500" fill="#64748B" text-anchor="middle">Operator / Client</text>
    </g>

    <!-- Role Notes Container -->
    <g filter="url(#shadow)">
      <rect x="58" y="355" width="134" height="305" rx="10" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>
      <text x="70" y="380" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="800" fill="#64748B" letter-spacing="0.5">DEPT / ROLES</text>
      
      <!-- Bullet 1 -->
      <circle cx="73" cy="406" r="3" fill="#2563EB"/>
      <text x="82" y="410" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#0F172A">Security</text>
      <text x="82" y="424" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="500" fill="#64748B">SecOps</text>

      <!-- Bullet 2 -->
      <circle cx="73" cy="452" r="3" fill="#2563EB"/>
      <text x="82" y="456" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#0F172A">Finance</text>
      <text x="82" y="470" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="500" fill="#64748B">Reconciliation</text>

      <!-- Bullet 3 -->
      <circle cx="73" cy="498" r="3" fill="#2563EB"/>
      <text x="82" y="502" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#0F172A">Fraud</text>
      <text x="82" y="516" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="500" fill="#64748B">Investigation</text>

      <line x1="70" y1="538" x2="180" y2="538" stroke="#E2E8F0" stroke-width="1"/>
      <text x="70" y="560" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="500" fill="#475569">
        <tspan x="70" dy="0">Initiates local tools</tspan>
        <tspan x="70" dy="15">(e.g. recon_tool)</tspan>
        <tspan x="70" dy="15">requiring hardware</tspan>
        <tspan x="70" dy="15">authorization.</tspan>
      </text>
    </g>
  </g>

  <!-- ================= ZONE 2: LOCAL DEVICE BOUNDARY ================= -->
  <g>
    <!-- Boundary Container -->
    <rect x="310" y="130" width="420" height="560" rx="14" fill="#F8FAFC" fill-opacity="0.8" stroke="#64748B" stroke-width="2" stroke-dasharray="8,6"/>
    <!-- Client Host Badge -->
    <g transform="translate(630, 142)">
      <rect width="85" height="22" rx="4" fill="#E2E8F0"/>
      <text x="42.5" y="15" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#475569" text-anchor="middle">CLIENT HOST</text>
    </g>
    <text x="330" y="156" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="700" fill="#334155">Local Device</text>

    <!-- EXE CARD (Point 1 / Ingress Trigger) -->
    <g filter="url(#shadow)">
      <rect x="320" y="180" width="130" height="160" rx="12" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
      <!-- Settings Cog Icon -->
      <g transform="translate(371, 198) scale(1.2)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
      </g>
      <text x="385" y="265" font-family="Helvetica, Arial, sans-serif" font-size="18" font-weight="800" fill="#1E3A8A" text-anchor="middle">EXE</text>
      <text x="385" y="284" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="600" fill="#475569" text-anchor="middle">Client Executable</text>
      <text x="385" y="306" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="500" fill="#64748B" text-anchor="middle">
        <tspan x="385" dy="0">Can be more than 1 type</tspan>
        <tspan x="385" dy="13">with different programs</tspan>
        <tspan x="385" dy="13" font-style="italic">(recon_tool, audit)</tspan>
      </text>
    </g>

    <!-- SAFE CHECKER CONTAINER CARD -->
    <g filter="url(#shadow)">
      <rect x="480" y="165" width="235" height="505" rx="12" fill="#FFFFFF" stroke="#0284C7" stroke-width="2"/>
      
      <!-- Safe Checker Header Bar -->
      <rect x="490" y="180" width="215" height="42" rx="8" fill="#E0F2FE" stroke="#BAE6FD" stroke-width="1"/>
      <text x="597.5" y="198" font-family="Helvetica, Arial, sans-serif" font-size="13" font-weight="800" fill="#0369A1" text-anchor="middle">🛡️ Safe Checker</text>
      <text x="597.5" y="213" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="500" fill="#64748B" text-anchor="middle">Pre-Run Whitelist Verifier</text>

      <!-- Step 1: Connect to CDSW -->
      <rect x="490" y="234" width="215" height="32" rx="6" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1"/>
      <circle cx="505" cy="250" r="3" fill="#0284C7"/>
      <text x="515" y="254" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="700" fill="#0F172A">Connect to CDSW</text>

      <!-- Step 2: Get MAC Addresses -->
      <rect x="490" y="274" width="215" height="32" rx="6" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1"/>
      <circle cx="505" cy="290" r="3" fill="#0284C7"/>
      <text x="515" y="294" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="700" fill="#0F172A">Get MAC Addresses</text>

      <!-- Step 3: Send request API ke CDSW (Highlighted Ingress Box) -->
      <rect x="490" y="318" width="215" height="50" rx="8" fill="#F0F9FF" stroke="#0284C7" stroke-width="2"/>
      <text x="597.5" y="338" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="800" fill="#0369A1" text-anchor="middle">📤 Send request API ke CDSW</text>
      <text x="597.5" y="354" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="500" fill="#0284C7" text-anchor="middle">Payload: MAC + Client Identity</text>

      <!-- Step 4: Receive Status (Highlighted Return Box) -->
      <rect x="490" y="380" width="215" height="46" rx="8" fill="#FFFBEB" stroke="#F59E0B" stroke-width="2"/>
      <text x="597.5" y="399" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="800" fill="#B45309" text-anchor="middle">📥 Receive Status</text>
      <text x="597.5" y="414" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="500" fill="#D97706" text-anchor="middle">Response: Allowed / Not Allowed</text>

      <!-- Step 5: If Else Evaluation -->
      <text x="492" y="446" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="800" fill="#475569">• If / Else Evaluation:</text>

      <!-- Branch Allowed -->
      <g transform="translate(490, 460)">
        <rect width="102" height="195" rx="8" fill="#F0FDF4" stroke="#16A34A" stroke-width="1.5"/>
        <rect x="15" y="12" width="72" height="20" rx="4" fill="#DCFCE7" stroke="#86EFAC" stroke-width="1"/>
        <text x="51" y="26" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="800" fill="#15803D" text-anchor="middle">Allowed</text>
        <text x="51" y="55" font-family="Helvetica, Arial, sans-serif" font-size="16" font-weight="800" fill="#16A34A" text-anchor="middle">↓</text>
        <text x="51" y="80" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="700" fill="#166534" text-anchor="middle">
          <tspan x="51" dy="0">Continue with</tspan>
          <tspan x="51" dy="14">the rest</tspan>
          <tspan x="51" dy="14">of exe</tspan>
        </text>
        <!-- Success Icon -->
        <g transform="translate(39, 135) scale(1.0)" stroke="#16A34A" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <path d="m9 12 2 2 4-4"/>
        </g>
      </g>

      <!-- Branch Not Allowed -->
      <g transform="translate(603, 460)">
        <rect width="102" height="195" rx="8" fill="#FEF2F2" stroke="#DC2626" stroke-width="1.5"/>
        <rect x="11" y="12" width="80" height="20" rx="4" fill="#FEE2E2" stroke="#FECACA" stroke-width="1"/>
        <text x="51" y="26" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="800" fill="#B91C1C" text-anchor="middle">not Allowed</text>
        <text x="51" y="55" font-family="Helvetica, Arial, sans-serif" font-size="16" font-weight="800" fill="#DC2626" text-anchor="middle">↓</text>
        <text x="51" y="82" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="800" fill="#991B1B" text-anchor="middle">Stopped</text>
        <text x="51" y="100" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="500" fill="#DC2626" text-anchor="middle">
          <tspan x="51" dy="0">Execution</tspan>
          <tspan x="51" dy="13">Aborted</tspan>
        </text>
        <!-- Stop Icon -->
        <g transform="translate(39, 135) scale(1.0)" stroke="#DC2626" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="9" x2="15" y2="15"/>
        </g>
      </g>
    </g>
  </g>

  <!-- ================= ZONE 3: BACKEND EXECUTION BOUNDARY ================= -->
  <g>
    <!-- Boundary Container -->
    <rect x="885" y="130" width="400" height="560" rx="14" fill="#FFFBEB" fill-opacity="0.3" stroke="#F59E0B" stroke-width="2" stroke-dasharray="8,6"/>
    <!-- Tag Badge -->
    <g transform="translate(1160, 142)">
      <rect width="115" height="22" rx="4" fill="#FEF3C7" stroke="#FDE68A" stroke-width="1"/>
      <text x="57.5" y="15" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#B45309" text-anchor="middle">CLOUDERA CDSW</text>
    </g>
    <text x="905" y="156" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="700" fill="#B45309">Backend Execution Boundary</text>

    <!-- CDSW JOB CARD -->
    <g filter="url(#shadow)">
      <rect x="900" y="210" width="165" height="150" rx="12" fill="#FFFFFF" stroke="#0284C7" stroke-width="2.5"/>
      <!-- Cloudera Emblem -->
      <g transform="translate(969.5, 226) scale(0.1892)">
        <path d="{CML_PATH_D}" fill="#4CCF4C" fill-rule="evenodd"/>
      </g>
      <text x="982.5" y="280" font-family="Helvetica, Arial, sans-serif" font-size="16.5" font-weight="800" fill="#0F172A" text-anchor="middle">CDSW JOB</text>
      <text x="982.5" y="302" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="600" fill="#475569" text-anchor="middle">Cloudera Data Science</text>
      <text x="982.5" y="318" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="500" fill="#64748B" text-anchor="middle">Workbench Job Runner</text>
    </g>

    <!-- WARNING BADGES (ABOVE 1 TASK) -->
    <g transform="translate(1095, 172)">
      <rect width="82" height="20" rx="4" fill="#FEE2E2" stroke="#FECACA" stroke-width="1"/>
      <text x="41" y="14" font-family="Helvetica, Arial, sans-serif" font-size="8" font-weight="800" fill="#DC2626" text-anchor="middle">⚠️ BOTTLENECK</text>
      
      <rect x="88" width="88" height="20" rx="4" fill="#FEF3C7" stroke="#FDE68A" stroke-width="1"/>
      <text x="132" y="14" font-family="Helvetica, Arial, sans-serif" font-size="8" font-weight="800" fill="#B45309" text-anchor="middle">⚠️ SYNCHRONOUS</text>
    </g>

    <!-- 1 TASK SQUARE (STANDALONE RED CARD) -->
    <g filter="url(#shadow)">
      <rect x="1095" y="205" width="175" height="85" rx="10" fill="#FFFFFF" stroke="#DC2626" stroke-width="2.5"/>
      <text x="1182.5" y="256" font-family="Helvetica, Arial, sans-serif" font-size="22" font-weight="800" fill="#0F172A" text-anchor="middle"><tspan text-decoration="underline">1</tspan> Task</text>
    </g>

    <!-- STEP BULLET LIST -->
    <g transform="translate(1095, 315)" font-family="Helvetica, Arial, sans-serif">
      <circle cx="6" cy="10" r="3" fill="#0F172A"/>
      <text x="18" y="14" font-size="11.5" font-weight="700" fill="#0F172A">Input metadata</text>

      <circle cx="6" cy="34" r="3" fill="#0F172A"/>
      <text x="18" y="38" font-size="11.5" font-weight="700" fill="#0F172A">SQL Query (Filter &amp; Search)</text>

      <circle cx="6" cy="58" r="3" fill="#0F172A"/>
      <text x="18" y="62" font-size="11.5" font-weight="700" fill="#0F172A">Filter &amp; Search Dev. ADD</text>

      <circle cx="6" cy="82" r="3" fill="#0F172A"/>
      <text x="18" y="86" font-size="11.5" font-weight="700" fill="#0F172A">Logging</text>

      <circle cx="6" cy="106" r="3" fill="#0F172A"/>
      <text x="18" y="110" font-size="11.5" font-weight="700" fill="#0F172A">Return Result</text>
    </g>
  </g>

  <!-- ================= FLOW CONNECTORS / CYCLE ARROWS ================= -->

  <!-- 1. USER -> EXE (Trigger in Gutter 1: x=200..310, Center x=255) -->
  <path d="M 192 255 L 312 255" fill="none" stroke="#2563EB" stroke-width="2.5" marker-end="url(#arrow-blue)"/>
  <rect x="230" y="244" width="50" height="20" rx="4" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
  <text x="255" y="258" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#1D4ED8" text-anchor="middle">Trigger</text>

  <!-- 2. EXE -> SAFE CHECKER (runs) -->
  <path d="M 450 255 L 472 255" fill="none" stroke="#2563EB" stroke-width="2.5" marker-end="url(#arrow-blue)"/>
  <rect x="449" y="244" width="30" height="20" rx="4" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
  <text x="464" y="258" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#1D4ED8" text-anchor="middle">runs</text>

  <!-- 3. SAFE CHECKER -> CDSW JOB (1. Send API Request in Gutter 2: x=730..885, Center x=807.5) -->
  <path d="M 705 343 L 807.5 343 L 807.5 285 L 892 285" fill="none" stroke="#0284C7" stroke-width="2.5" marker-end="url(#arrow-cyan)"/>
  <rect x="765" y="274" width="85" height="20" rx="4" fill="#F0F9FF" stroke="#BAE6FD" stroke-width="1"/>
  <text x="807.5" y="288" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="800" fill="#0369A1" text-anchor="middle">1. API Request</text>

  <!-- 4. CDSW JOB -> 1 TASK (2. Run) -->
  <path d="M 1065 250 L 1087 250" fill="none" stroke="#0284C7" stroke-width="2.5" marker-end="url(#arrow-cyan)"/>
  <rect x="1057" y="239" width="34" height="20" rx="4" fill="#F0F9FF" stroke="#BAE6FD" stroke-width="1"/>
  <text x="1074" y="253" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#0369A1" text-anchor="middle">2. Run</text>

  <!-- 5. CDSW JOB -> RECEIVE STATUS (3. Return Status in Gutter 2: x=730..885, Center x=807.5) -->
  <path d="M 900 330 L 807.5 330 L 807.5 403 L 713 403" fill="none" stroke="#D97706" stroke-width="2.5" marker-end="url(#arrow-amber)"/>
  <rect x="765" y="358" width="85" height="20" rx="4" fill="#FFFBEB" stroke="#FDE68A" stroke-width="1"/>
  <text x="807.5" y="372" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="800" fill="#B45309" text-anchor="middle">3. Return Status</text>

</svg>
"""
    return svg.replace("{CML_PATH_D}", cml_path_d)


def build_powerpoint_slides():
    """Generates PPTX slides with both standalone export and full suite compilation."""
    from src.ppt_engine.pptx_diagram_compiler import PowerPointDiagramCompiler

    compiler = PowerPointDiagramCompiler()

    # 1. Generate standalone 1-slide presentation for rapid preview
    standalone_prs = compiler.create_deck()
    compiler.build_slide_1_expanded_cdsw_process(standalone_prs)
    standalone_path = REPO_ROOT / "output/presentations/cdsw_job_execution_expanded.pptx"
    standalone_path.parent.mkdir(parents=True, exist_ok=True)
    standalone_prs.save(str(standalone_path))
    print(f"✓ Saved Standalone PPTX to: {standalone_path}")

    # Copy to BSIM_Migration doc_outpput
    bsim_out = Path("/Users/marcelljw/Documents/antigravity/adventurous-darwin/BSIM_Migration/doc_outpput/cdsw_job_execution_expanded.pptx")
    bsim_out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(standalone_path, bsim_out)
    print(f"✓ Copied Standalone PPTX to BSIM workspace: {bsim_out}")

    # 2. Compile into master presentation suite
    master_path = REPO_ROOT / "output/presentations/architecture_evolution_cdsw_to_lambda.pptx"
    compiler.compile_presentation(master_path)
    print(f"✓ Recompiled Master Presentation Suite: {master_path}")
    shutil.copy2(master_path, REPO_ROOT / "TEMP/architecture_evolution_cdsw_to_lambda.pptx")


def main():
    drawio_path = REPO_ROOT / "output/diagrams/current_process_cdsw_expanded.drawio"
    svg_path = REPO_ROOT / "output/diagrams/current_process_cdsw_expanded.svg"
    png_path = REPO_ROOT / "output/diagrams/current_process_cdsw_expanded.png"

    temp_drawio = REPO_ROOT / "TEMP/current_process_cdsw_expanded.drawio"
    temp_svg = REPO_ROOT / "TEMP/current_process_cdsw_expanded.svg"
    temp_png = REPO_ROOT / "TEMP/current_process_cdsw_expanded.png"

    drawio_path.parent.mkdir(parents=True, exist_ok=True)
    temp_drawio.parent.mkdir(parents=True, exist_ok=True)

    # 1. Write Draw.io XML
    xml_content = create_drawio_xml()
    drawio_path.write_text(xml_content, encoding="utf-8")
    temp_drawio.write_text(xml_content, encoding="utf-8")
    print(f"✓ Saved Draw.io XML to: {drawio_path} and {temp_drawio}")

    # 2. Write SVG companion
    svg_content = create_high_fidelity_svg()
    svg_path.write_text(svg_content, encoding="utf-8")
    temp_svg.write_text(svg_content, encoding="utf-8")
    print(f"✓ Saved SVG companion to: {svg_path} and {temp_svg}")

    # 3. Export to High-Resolution PNG (300+ DPI via rsvg-convert)
    res = subprocess.run(["rsvg-convert", "-z", "2.5", str(svg_path), "-o", str(png_path)], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"✓ Exported High-Resolution PNG to: {png_path} using rsvg-convert")
        shutil.copy2(png_path, temp_png)
    else:
        print(f"rsvg-convert failed: {res.stderr}")
        from src.ppt_engine.diagram_engine import _setup_cairo_library
        _setup_cairo_library()
        import cairosvg
        cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), write_to=str(png_path), scale=2.5)
        shutil.copy2(png_path, temp_png)
        print(f"✓ Exported High-Resolution PNG via cairosvg")

    # 4. Copy PNG to current conversation artifact directory
    artifact_dir = Path("/Users/marcelljw/.gemini/antigravity/brain/bd3a3576-f0df-459c-801a-f0ef8e8b29a6")
    artifact_png = artifact_dir / "cdsw_job_execution_expanded.png"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(png_path, artifact_png)
    print(f"✓ Copied PNG to artifact directory: {artifact_png}")

    # Also copy PNG to BSIM_Migration doc_outpput
    bsim_png = Path("/Users/marcelljw/Documents/antigravity/adventurous-darwin/BSIM_Migration/doc_outpput/cdsw_job_execution_expanded.png")
    shutil.copy2(png_path, bsim_png)
    print(f"✓ Copied PNG to BSIM doc_outpput: {bsim_png}")

    # 5. Update master project TEMP/device_whitelist_system.drawio
    master_drawio = REPO_ROOT / "TEMP/device_whitelist_system.drawio"
    if master_drawio.exists():
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        master_tree = ET.parse(master_drawio)
        master_root = master_tree.getroot()
        for diag in list(master_root.findall("diagram")):
            if diag.attrib.get("id") == "expanded_cdsw_process" or "Expanded" in diag.attrib.get("name", ""):
                master_root.remove(diag)
        new_tree = ET.parse(drawio_path)
        master_root.append(new_tree.getroot().find("diagram"))
        raw = ET.tostring(master_root, encoding="utf-8")
        master_drawio.write_text(minidom.parseString(raw).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8"))
        print(f"✓ Updated master project: {master_drawio}")

    # 6. Generate browser URL and launcher
    compressor = zlib.compressobj(level=9, method=zlib.DEFLATED, wbits=-15)
    deflated = compressor.compress(xml_content.encode('utf-8')) + compressor.flush()
    b64 = base64.b64encode(deflated).decode('ascii')
    url_encoded = urllib.parse.quote(b64)
    new_url = f"https://app.diagrams.net/#R{url_encoded}"

    html_file = REPO_ROOT / "TEMP/open_expanded_cdsw_in_browser.html"
    html_file.write_text(f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url='{new_url}'" />
    <title>Opening Expanded CDSW Process in Draw.io...</title>
</head>
<body>
    <p>Opening Expanded CDSW Process in Draw.io... If not redirected, <a href="{new_url}">click here</a>.</p>
</body>
</html>""", encoding="utf-8")
    print(f"✓ Updated browser launcher: {html_file}")

    # 7. Build PowerPoint Slides
    build_powerpoint_slides()


if __name__ == "__main__":
    main()
