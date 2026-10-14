#!/usr/bin/env python3
"""
Generate Optimized Interwoven Migration Architecture Visualization for Whitelisting System.

Remediations implemented:
1. Shrunk database cylinder shapes horizontally (width reduced from 260px to 170px) across both tracks.
2. Expanded all horizontal arrow spans (140px to 175px clearance), eliminating any badge overlap over arrow stems and arrowheads.
3. Moved '3a. Serialized Sync Return (>30-60s)' from top ceiling down to BELLOW THE CLUSTER (y=240), flowing cleanly from the base of Legacy Storage across to Client Ingress Origin.
4. Maintained clean, unclipped, solid vertical migration bridges (Col 2 & Col 3).
5. Updated Draw.io XML, companion SVG, High-Res PNG (v4), and master presentation.
"""

import sys
import shutil
import subprocess
import zlib
import base64
import urllib.parse
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Load logos for base64 data URIs
cloudera_svg_path = Path("assets/logos/cloudera/cloudera_cdsw.svg")
cml_svg_text = cloudera_svg_path.read_text(encoding="utf-8") if cloudera_svg_path.exists() else ""
cml_path_match = re.search(r'd="([^"]+)"', cml_svg_text)
cml_path_d = cml_path_match.group(1) if cml_path_match else ""
cloudera_data_uri = f"data:image/svg+xml;base64,{base64.b64encode(cloudera_svg_path.read_bytes()).decode('ascii')}" if cloudera_svg_path.exists() else ""

api_gw_svg_path = Path("assets/logos/aws/aws_api_gateway.svg")
api_gw_data_uri = f"data:image/svg+xml;base64,{base64.b64encode(api_gw_svg_path.read_bytes()).decode('ascii')}" if api_gw_svg_path.exists() else ""

lambda_svg_path = Path("assets/logos/aws/aws_lambda.svg")
lambda_data_uri = f"data:image/svg+xml;base64,{base64.b64encode(lambda_svg_path.read_bytes()).decode('ascii')}" if lambda_svg_path.exists() else ""

dbx_svg_path = Path("assets/logos/databricks/databricks.svg")
dbx_data_uri = f"data:image/svg+xml;base64,{base64.b64encode(dbx_svg_path.read_bytes()).decode('ascii')}" if dbx_svg_path.exists() else ""

def create_drawio_xml():
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="Electron" agent="Enterprise Bench Diagram Engine" version="21.0.0" type="device">
  <diagram id="interwoven_migration" name="Interwoven Migration Architecture">
    <mxGraphModel dx="1360" dy="660" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1360" pageHeight="660" background="#FFFFFF" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- ================= ZONE 1: SHARED CLIENT INGRESS ORIGIN ================= -->
        <mxCell id="group_client_apps" value="Shared Client Ingress Origin" style="rounded=1;arcSize=14;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#94A3B8;strokeWidth=2.2;fillColor=#F8FAFC;fillOpacity=60;fontFamily=Helvetica, Arial, sans-serif;fontColor=#475569;fontSize=13;fontStyle=2;align=center;verticalAlign=top;spacingTop=12;" vertex="1" parent="1">
          <mxGeometry x="25" y="35" width="205" height="585" as="geometry"/>
        </mxCell>

        <!-- APP 1 -->
        <mxCell id="node_app1" value="&lt;div style=&quot;font-weight:800; font-size:15px; color:#1E3A8A; margin-bottom:3px;&quot;&gt;app1&lt;/div&gt;&lt;div style=&quot;font-size:22px;&quot;&gt;🖥️&lt;/div&gt;&lt;div style=&quot;font-size:11.5px; color:#64748B; margin-top:2px;&quot;&gt;Device 1&lt;/div&gt;&lt;div style=&quot;font-size:9.5px; color:#94A3B8;&quot;&gt;recon_tool binary&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="40" y="80" width="175" height="100" as="geometry"/>
        </mxCell>

        <!-- APP 2 -->
        <mxCell id="node_app2" value="&lt;div style=&quot;font-weight:800; font-size:15px; color:#1E3A8A; margin-bottom:3px;&quot;&gt;app2&lt;/div&gt;&lt;div style=&quot;font-size:22px;&quot;&gt;🖥️&lt;/div&gt;&lt;div style=&quot;font-size:11.5px; color:#64748B; margin-top:2px;&quot;&gt;Device 2&lt;/div&gt;&lt;div style=&quot;font-size:9.5px; color:#94A3B8;&quot;&gt;recon_tool binary&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="40" y="275" width="175" height="100" as="geometry"/>
        </mxCell>

        <!-- APP 3 -->
        <mxCell id="node_app3" value="&lt;div style=&quot;font-weight:800; font-size:15px; color:#1E3A8A; margin-bottom:3px;&quot;&gt;app3&lt;/div&gt;&lt;div style=&quot;font-size:22px;&quot;&gt;🖥️&lt;/div&gt;&lt;div style=&quot;font-size:11.5px; color:#64748B; margin-top:2px;&quot;&gt;Device 3&lt;/div&gt;&lt;div style=&quot;font-size:9.5px; color:#94A3B8;&quot;&gt;recon_tool binary&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="40" y="470" width="175" height="100" as="geometry"/>
        </mxCell>


        <!-- ================= ZONE 2: UPPER TRACK (LEGACY CDSW BATCH) ================= -->
        <mxCell id="group_legacy_track" value="UPPER TRACK: LEGACY CDSW BATCH" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#FCA5A5;strokeWidth=2.2;fillColor=#FFFDFB;fillOpacity=50;fontFamily=Helvetica, Arial, sans-serif;fontColor=#B91C1C;fontSize=13;fontStyle=1;align=left;verticalAlign=top;spacingLeft=18;spacingTop=10;" vertex="1" parent="1">
          <mxGeometry x="380" y="35" width="940" height="225" as="geometry"/>
        </mxCell>

        <!-- CDSW JOB CARD (COL 1) -->
        <mxCell id="node_cdsw" value="&lt;div style=&quot;margin-bottom:4px;&quot;&gt;&lt;img src=&quot;{cloudera_data_uri}&quot; width=&quot;28&quot; height=&quot;28&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-size:17px; font-weight:800; color:#0F172A;&quot;&gt;CDSW JOB&lt;/div&gt;&lt;div style=&quot;font-size:11.5px; color:#475569; margin-top:2px;&quot;&gt;Cloudera Data Science&lt;/div&gt;&lt;div style=&quot;font-size:10.5px; color:#64748B;&quot;&gt;Workbench Job Runner&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#0284C7;strokeWidth=2.5;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="405" y="75" width="195" height="145" as="geometry"/>
        </mxCell>

        <!-- 1 TASK WARNINGS (COL 2) -->
        <mxCell id="node_task_warnings" value="&lt;div style=&quot;display:flex; gap:6px;&quot;&gt;&lt;span style=&quot;background:#FEE2E2; color:#DC2626; font-size:9px; font-weight:800; padding:2px 6px; border-radius:4px;&quot;&gt;⚠️ BOTTLENECK&lt;/span&gt; &lt;span style=&quot;background:#FEF3C7; color:#B45309; font-size:9px; font-weight:800; padding:2px 6px; border-radius:4px;&quot;&gt;⚠️ SYNCHRONOUS&lt;/span&gt;&lt;/div&gt;" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="745" y="65" width="195" height="22" as="geometry"/>
        </mxCell>

        <!-- 1 TASK CARD (COL 2) -->
        <mxCell id="node_task" value="&lt;div style=&quot;font-size:21px; font-weight:800; color:#0F172A;&quot;&gt;&lt;u&gt;1&lt;/u&gt; Task&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#DC2626;strokeWidth=2.5;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="745" y="90" width="195" height="46" as="geometry"/>
        </mxCell>

        <!-- TASK STEPS BULLETS (COL 2) -->
        <mxCell id="node_task_bullets" value="&lt;div style=&quot;text-align:left; font-size:11.5px; font-family:Helvetica, Arial, sans-serif; color:#0F172A; line-height:1.4;&quot;&gt;&lt;b&gt;• Input metadata&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• SQL Query&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• Filter &amp;amp; Search Dev. ADD&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• Logging&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• Return to sender&lt;/b&gt;&lt;/div&gt;" style="text;html=1;align=left;verticalAlign=top;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="745" y="140" width="195" height="75" as="geometry"/>
        </mxCell>

        <!-- LEGACY STORAGE CYLINDER (COL 3 - SHRUNK HORIZONTALLY TO 170px) -->
        <mxCell id="node_legacy_db" value="&lt;div style=&quot;padding-top:6px;&quot;&gt;&lt;div style=&quot;font-size:15px; font-weight:800; color:#991B1B;&quot;&gt;Legacy Storage&lt;/div&gt;&lt;div style=&quot;font-size:12px; font-weight:700; color:#B91C1C; margin-top:2px;&quot;&gt;wsaidsu_exp&lt;/div&gt;&lt;div style=&quot;font-size:10px; color:#7F1D1D;&quot;&gt;Monolithic Cluster DB&lt;/div&gt;&lt;/div&gt;" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=14;fillColor=#FEF2F2;strokeColor=#EF4444;strokeWidth=2.2;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="1090" y="75" width="170" height="120" as="geometry"/>
        </mxCell>


        <!-- ================= ZONE 3: LOWER TRACK (MODERN AWS SERVERLESS PIPELINE) ================= -->
        <mxCell id="group_modern_track" value="LOWER TRACK: TARGET AWS SERVERLESS" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;strokeColor=#86EFAC;strokeWidth=2.2;fillColor=#F0FDF4;fontFamily=Helvetica, Arial, sans-serif;fontColor=#065F46;fontSize=13;fontStyle=1;align=left;verticalAlign=top;spacingLeft=18;spacingTop=10;" vertex="1" parent="1">
          <mxGeometry x="380" y="390" width="940" height="230" as="geometry"/>
        </mxCell>

        <!-- UNIFIED API GATEWAY CARD (COL 1) -->
        <mxCell id="node_api_gw" value="&lt;div style=&quot;margin-bottom:3px;&quot;&gt;&lt;span style=&quot;font-size:9px; font-weight:800; color:#6D28D9; background:#EDE9FE; padding:1px 7px; border-radius:3px;&quot;&gt;API GATEWAY&lt;/span&gt;&lt;/div&gt;&lt;div style=&quot;margin-bottom:3px;&quot;&gt;&lt;img src=&quot;{api_gw_data_uri}&quot; width=&quot;28&quot; height=&quot;28&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-size:17px; font-weight:800; color:#1E1B4B;&quot;&gt;API Gateway&lt;/div&gt;&lt;div style=&quot;font-size:11.5px; color:#6B7280; margin-top:2px;&quot;&gt;Managed HTTPS Endpoints&lt;/div&gt;&lt;div style=&quot;font-size:10.5px; font-weight:600; color:#7C3AED;&quot;&gt;Managed Ingress &amp;amp; Egress&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#8B5CF6;strokeWidth=2.2;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="405" y="425" width="195" height="175" as="geometry"/>
        </mxCell>

        <!-- CODE COMPONENT (COL 2) -->
        <mxCell id="node_code" value="&lt;div style=&quot;font-weight:800; font-size:11.5px; color:#065F46;&quot;&gt;Code&lt;/div&gt;&lt;div style=&quot;font-size:8px; font-weight:700; color:#059669;&quot;&gt;DEPLOYED&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#10B981;strokeWidth=1.8;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="725" y="425" width="75" height="36" as="geometry"/>
        </mxCell>

        <!-- SECRET MANAGEMENT (COL 2) -->
        <mxCell id="node_secrets" value="&lt;div style=&quot;font-size:7.5px; font-weight:800; color:#B91C1C; background:#FEE2E2; display:inline-block; padding:1px 5px; border-radius:3px;&quot;&gt;SECURITY&lt;/div&gt;&lt;div style=&quot;font-size:11px; font-weight:800; color:#991B1B; margin-top:1px;&quot;&gt;Secret Management&lt;/div&gt;&lt;div style=&quot;font-size:9px; color:#7F1D1D;&quot;&gt;KMS / Secrets Mgr&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#EF4444;strokeWidth=1.8;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="870" y="422" width="135" height="42" as="geometry"/>
        </mxCell>

        <!-- AWS LAMBDA (COL 2) -->
        <mxCell id="node_lambda" value="&lt;div style=&quot;margin-bottom:3px;&quot;&gt;&lt;img src=&quot;{lambda_data_uri}&quot; width=&quot;26&quot; height=&quot;26&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-size:17px; font-weight:800; color:#0F172A;&quot;&gt;AWS Lambda&lt;/div&gt;&lt;div style=&quot;font-size:11px; font-weight:600; color:#D97706;&quot;&gt;(Aws Lamda)&lt;/div&gt;&lt;div style=&quot;font-size:10px; color:#64748B;&quot;&gt;Serverless Compute&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#D97706;strokeWidth=2.5;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="740" y="478" width="200" height="122" as="geometry"/>
        </mxCell>

        <!-- DATABRICKS DBX CYLINDER (COL 3 - SHRUNK HORIZONTALLY TO 170px) -->
        <mxCell id="node_dbx" value="&lt;table style=&quot;margin:auto;&quot;&gt;&lt;tr&gt;&lt;td style=&quot;vertical-align:middle; padding-right:8px;&quot;&gt;&lt;img src=&quot;{dbx_data_uri}&quot; width=&quot;22&quot; height=&quot;26&quot;/&gt;&lt;/td&gt;&lt;td style=&quot;text-align:left; vertical-align:middle;&quot;&gt;&lt;div style=&quot;font-size:16px; font-weight:800; color:#0369A1; line-height:1.2;&quot;&gt;DBX&lt;/div&gt;&lt;div style=&quot;font-size:11px; font-weight:600; color:#0284C7; line-height:1.2;&quot;&gt;Databricks / DB&lt;/div&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#F0F9FF;strokeColor=#0284C7;strokeWidth=2.2;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="1090" y="425" width="170" height="145" as="geometry"/>
        </mxCell>


        <!-- ================= CONNECTORS: EXPANDED SPANS, ZERO OVERLAY CONGESTION ================= -->

        <!-- 1a. CLIENT CONTAINER BORDER (x=230, y=145) -> CDSW JOB (x=405, y=145) [175px EXPANDED SPAN] -->
        <mxCell id="edge_apps_to_cdsw" value="1a. Legacy EXE Call (Deprecated)" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#DC2626;strokeWidth=2.5;fontColor=#B91C1C;fontFamily=Helvetica, Arial, sans-serif;fontSize=10.5;fontStyle=1;exitX=1;exitY=0.19;entryX=0;entryY=0.48;" edge="1" parent="1" source="group_client_apps" target="node_cdsw">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 2a. CDSW (x=600, y=112) -> 1 TASK (x=745, y=112) [145px EXPANDED SPAN] -->
        <mxCell id="edge_cdsw_to_task" value="2a. Run" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#0284C7;strokeWidth=2.5;fontColor=#0369A1;fontFamily=Helvetica, Arial, sans-serif;fontSize=10.5;fontStyle=1;exitX=1;exitY=0.25;entryX=0;entryY=0.48;" edge="1" parent="1" source="node_cdsw" target="node_task">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 2a_db. 1 TASK (x=940, y=112) -> LEGACY DB (x=1090, y=112) [150px EXPANDED SPAN] -->
        <mxCell id="edge_task_to_db" value="SQL Query" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#EF4444;strokeWidth=2.2;fontColor=#DC2626;fontFamily=Helvetica, Arial, sans-serif;fontSize=10.5;fontStyle=1;exitX=1;exitY=0.48;entryX=0;entryY=0.35;" edge="1" parent="1" source="node_task" target="node_legacy_db">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 3a. LEGACY RETURN LOOP: RUNS DIRECTLY BELLOW THE CLUSTER (y=230) BACK TO CLIENT ORIGIN -->
        <mxCell id="edge_legacy_return" value="3a. Serialized Sync Return (&amp;gt;30-60s)" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#D97706;strokeWidth=2.2;fontColor=#B45309;fontFamily=Helvetica, Arial, sans-serif;fontSize=10.5;fontStyle=1;exitX=0.25;exitY=1;entryX=1;entryY=0.33;" edge="1" parent="1" source="node_legacy_db" target="group_client_apps">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="1132" y="230"/>
              <mxPoint x="230" y="230"/>
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- 1b. CLIENT CONTAINER BORDER (x=230, y=485) -> API GATEWAY (x=405, y=485) [175px EXPANDED SPAN] -->
        <mxCell id="edge_apps_to_gw" value="1b. HTTPS REST (Managed Ingress)" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#2563EB;strokeWidth=2.5;fontColor=#1D4ED8;fontFamily=Helvetica, Arial, sans-serif;fontSize=10.5;fontStyle=1;exitX=1;exitY=0.77;entryX=0;entryY=0.35;" edge="1" parent="1" source="group_client_apps" target="node_api_gw">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 2b. API GATEWAY (x=600, y=485) -> AWS LAMBDA (x=740, y=485) [140px EXPANDED SPAN] -->
        <mxCell id="edge_gw_to_lambda" value="2b. Event Invoke" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#7C3AED;strokeWidth=2.5;fontColor=#6D28D9;fontFamily=Helvetica, Arial, sans-serif;fontSize=10.5;fontStyle=1;exitX=1;exitY=0.35;entryX=0;entryY=0.25;" edge="1" parent="1" source="node_api_gw" target="node_lambda">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- Code & Secrets Injections -->
        <mxCell id="edge_code_to_lambda" value="" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#10B981;strokeWidth=2;exitX=0.5;exitY=1;entryX=0.22;entryY=0;" edge="1" parent="1" source="node_code" target="node_lambda">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="edge_secrets_to_lambda" value="Secrets" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#EF4444;strokeWidth=1.8;dashed=1;dashPattern=4 3;fontColor=#DC2626;fontSize=9.5;fontStyle=1;exitX=0.5;exitY=1;entryX=0.72;entryY=0;" edge="1" parent="1" source="node_secrets" target="node_lambda">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 3b. AWS LAMBDA (x=940, y=485) -> DBX (x=1090, y=485) [150px EXPANDED SPAN] -->
        <mxCell id="edge_lambda_to_dbx" value="3b. ACID SQL" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#0284C7;strokeWidth=2.2;fontColor=#0369A1;fontFamily=Helvetica, Arial, sans-serif;fontSize=10.5;fontStyle=1;exitX=1;exitY=0.35;entryX=0;entryY=0.45;" edge="1" parent="1" source="node_lambda" target="node_dbx">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 4b. AWS LAMBDA (x=740, y=545) -> API GATEWAY (x=600, y=545) [140px EXPANDED SPAN] -->
        <mxCell id="edge_lambda_to_gw" value="4b. Deliver" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#7C3AED;strokeWidth=2.2;fontColor=#6D28D9;fontFamily=Helvetica, Arial, sans-serif;fontSize=10.5;fontStyle=1;exitX=0;exitY=0.65;entryX=1;entryY=0.69;" edge="1" parent="1" source="node_lambda" target="node_api_gw">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 5b. API GATEWAY (x=405, y=545) -> CLIENT CONTAINER BORDER (x=230, y=545) [175px EXPANDED SPAN] -->
        <mxCell id="edge_gw_to_apps" value="5b. Sub-100ms Fast Response" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#2563EB;strokeWidth=2.5;fontColor=#1D4ED8;fontFamily=Helvetica, Arial, sans-serif;fontSize=10.5;fontStyle=1;exitX=0;exitY=0.69;entryX=1;entryY=0.87;" edge="1" parent="1" source="node_api_gw" target="group_client_apps">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>


        <!-- ================= VERTICAL MIGRATION TRANSITIONS (SOLID, UNCLIPPED, DIRECT) ================= -->

        <!-- BRIDGE 1: SCRIPT TO SERVERLESS HANDLER (COL 2: 1 TASK -> AWS LAMBDA) -->
        <mxCell id="bridge_task_to_lambda" value="Modernize: 1-Task Script ➔ Serverless Lambda" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#D97706;strokeWidth=2.5;fontColor=#B45309;fontFamily=Helvetica, Arial, sans-serif;fontSize=10.5;fontStyle=1;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" edge="1" parent="1" source="group_legacy_track" target="node_lambda">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- BRIDGE 2: DATA MIGRATION (COL 3: LEGACY STORAGE -> DBX DATABRICKS) -->
        <mxCell id="bridge_db_to_dbx" value="Data Migration: Legacy HDFS ➔ Databricks Delta" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#0284C7;strokeWidth=2.5;fontColor=#0369A1;fontFamily=Helvetica, Arial, sans-serif;fontSize=10.5;fontStyle=1;exitX=0.5;exitY=1;entryX=0.5;entryY=0;" edge="1" parent="1" source="node_legacy_db" target="node_dbx">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""
    return xml.strip()

def create_high_fidelity_svg():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1360 660" width="1360" height="660">
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
    <marker id="arrow-purple" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#7C3AED"/>
    </marker>
    <marker id="arrow-amber" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#D97706"/>
    </marker>
    <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#10B981"/>
    </marker>
    <marker id="arrow-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#DC2626"/>
    </marker>
  </defs>

  <!-- Clean Canvas Background -->
  <rect width="1360" height="660" fill="#FFFFFF"/>
  <rect width="1360" height="660" fill="#F8FAFC" opacity="0.45"/>

  <!-- Subtle Blueprint Grid Pattern -->
  <g stroke="#E2E8F0" stroke-width="0.75" opacity="0.6">
    <path d="M 0 50 L 1360 50 M 0 100 L 1360 100 M 0 150 L 1360 150 M 0 200 L 1360 200 M 0 250 L 1360 250 M 0 300 L 1360 300 M 0 350 L 1360 350 M 0 400 L 1360 400 M 0 450 L 1360 450 M 0 500 L 1360 500 M 0 550 L 1360 550 M 0 600 L 1360 600" />
    <path d="M 50 0 L 50 660 M 100 0 L 100 660 M 150 0 L 150 660 M 200 0 L 200 660 M 250 0 L 250 660 M 300 0 L 300 660 M 350 0 L 350 660 M 400 0 L 400 660 M 450 0 L 450 660 M 500 0 L 500 660 M 550 0 L 550 660 M 600 0 L 600 660 M 650 0 L 650 660 M 700 0 L 700 660 M 750 0 L 750 660 M 800 0 L 800 660 M 850 0 L 850 660 M 900 0 L 900 660 M 950 0 L 950 660 M 1000 0 L 1000 660 M 1050 0 L 1050 660 M 1100 0 L 1100 660 M 1150 0 L 1150 660 M 1200 0 L 1200 660 M 1250 0 L 1250 660 M 1300 0 L 1300 660" />
  </g>


  <!-- ================= ZONE 1: SHARED CLIENT INGRESS ORIGIN (x=25 to x=230) ================= -->
  <g transform="translate(25, 35)">
    <!-- Boundary Container -->
    <rect width="205" height="585" rx="16" fill="#F8FAFC" stroke="#94A3B8" stroke-width="2.2" stroke-dasharray="8,6" opacity="0.95"/>
    <text x="102" y="26" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="800" fill="#475569" text-anchor="middle" letter-spacing="0.5">SHARED INGRESS ORIGIN</text>
    <text x="102" y="42" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="600" fill="#94A3B8" text-anchor="middle">Client Application Devices</text>

    <!-- App 1 (Device 1) -->
    <g transform="translate(15, 48)" filter="url(#card-shadow)">
      <rect width="175" height="100" rx="12" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
      <text x="87.5" y="24" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="800" fill="#1E3A8A" text-anchor="middle">app1</text>
      <g transform="translate(76, 31) scale(1.1)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect width="20" height="14" x="2" y="3" rx="2"/>
        <path d="M8 21h8m-4-4v4"/>
      </g>
      <text x="87.5" y="74" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#475569" text-anchor="middle">Device 1</text>
      <text x="87.5" y="90" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="500" fill="#94A3B8" text-anchor="middle">recon_tool binary</text>
    </g>

    <!-- App 2 (Device 2) -->
    <g transform="translate(15, 238)" filter="url(#card-shadow)">
      <rect width="175" height="100" rx="12" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
      <text x="87.5" y="24" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="800" fill="#1E3A8A" text-anchor="middle">app2</text>
      <g transform="translate(76, 31) scale(1.1)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect width="20" height="14" x="2" y="3" rx="2"/>
        <path d="M8 21h8m-4-4v4"/>
      </g>
      <text x="87.5" y="74" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#475569" text-anchor="middle">Device 2</text>
      <text x="87.5" y="90" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="500" fill="#94A3B8" text-anchor="middle">recon_tool binary</text>
    </g>

    <!-- App 3 (Device 3) -->
    <g transform="translate(15, 428)" filter="url(#card-shadow)">
      <rect width="175" height="100" rx="12" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
      <text x="87.5" y="24" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="800" fill="#1E3A8A" text-anchor="middle">app3</text>
      <g transform="translate(76, 31) scale(1.1)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect width="20" height="14" x="2" y="3" rx="2"/>
        <path d="M8 21h8m-4-4v4"/>
      </g>
      <text x="87.5" y="74" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#475569" text-anchor="middle">Device 3</text>
      <text x="87.5" y="90" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="500" fill="#94A3B8" text-anchor="middle">recon_tool binary</text>
    </g>
  </g>


  <!-- ================= ZONE 2: UPPER TRACK (LEGACY CDSW BATCH, x=380 to x=1320, y=35 to y=260) ================= -->
  <g transform="translate(380, 35)">
    <!-- Container -->
    <rect width="940" height="225" rx="16" fill="#FFFDFB" stroke="#FCA5A5" stroke-width="2.2" stroke-dasharray="8,6"/>
    <text x="24" y="24" font-family="Helvetica, Arial, sans-serif" font-size="13" font-weight="800" fill="#B91C1C">UPPER TRACK: LEGACY CDSW BATCH</text>

    <!-- CDSW Job Card (Col 1: x=25 to x=220) -->
    <g transform="translate(25, 40)" filter="url(#shadow)">
      <rect width="195" height="145" rx="14" fill="#FFFFFF" stroke="#0284C7" stroke-width="2.5"/>
      <g transform="translate(82, 16) scale(0.20)">
        <path d="{CML_PATH_D}" fill="#4CCF4C" fill-rule="evenodd"/>
      </g>
      <text x="97.5" y="82" font-family="Helvetica, Arial, sans-serif" font-size="17" font-weight="800" fill="#0F172A" text-anchor="middle">CDSW JOB</text>
      <text x="97.5" y="105" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="600" fill="#475569" text-anchor="middle">Cloudera Data Science</text>
      <text x="97.5" y="123" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="500" fill="#64748B" text-anchor="middle">Workbench Job Runner</text>
    </g>

    <!-- 1 Task Warnings (Col 2) -->
    <g transform="translate(365, 30)">
      <rect width="92" height="19" rx="4" fill="#FEE2E2" stroke="#FECACA" stroke-width="1"/>
      <text x="46" y="13" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="800" fill="#DC2626" text-anchor="middle">⚠️ BOTTLENECK</text>
      
      <rect x="98" width="97" height="19" rx="4" fill="#FEF3C7" stroke="#FDE68A" stroke-width="1"/>
      <text x="146.5" y="13" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="800" fill="#B45309" text-anchor="middle">⚠️ SYNCHRONOUS</text>
    </g>

    <!-- 1 Task Card (Col 2: x=365 to x=560) -->
    <g transform="translate(365, 55)" filter="url(#shadow)">
      <rect width="195" height="46" rx="10" fill="#FFFFFF" stroke="#DC2626" stroke-width="2.5"/>
      <text x="97.5" y="31" font-family="Helvetica, Arial, sans-serif" font-size="21" font-weight="800" fill="#0F172A" text-anchor="middle"><tspan text-decoration="underline">1</tspan> Task</text>
    </g>

    <!-- Task Steps Bullets (Col 2) -->
    <g transform="translate(365, 112)" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#0F172A">
      <circle cx="8" cy="8" r="2.5" fill="#0F172A"/>
      <text x="18" y="12">Input metadata</text>

      <circle cx="8" cy="24" r="2.5" fill="#0F172A"/>
      <text x="18" y="28">SQL Query</text>

      <circle cx="8" cy="40" r="2.5" fill="#0F172A"/>
      <text x="18" y="44">Filter &amp; Search Dev. ADD</text>

      <circle cx="8" cy="56" r="2.5" fill="#0F172A"/>
      <text x="18" y="60">Logging</text>

      <circle cx="8" cy="72" r="2.5" fill="#0F172A"/>
      <text x="18" y="76">Return to sender</text>
    </g>

    <!-- Legacy Storage 3D Cylinder (Col 3: x=710 to x=880 - SHRUNK HORIZONTALLY TO 170px) -->
    <g transform="translate(710, 40)" filter="url(#shadow)">
      <path d="M 0 14 L 0 95 A 85 14 0 0 0 170 95 L 170 14 Z" fill="#FEF2F2" stroke="#EF4444" stroke-width="2.2"/>
      <ellipse cx="85" cy="14" rx="85" ry="14" fill="#FEE2E2" stroke="#EF4444" stroke-width="2.2"/>
      <path d="M 0 95 A 85 14 0 0 0 170 95" fill="none" stroke="#EF4444" stroke-width="2.2"/>
      <text x="85" y="48" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="800" fill="#991B1B" text-anchor="middle">Legacy Storage</text>
      <text x="85" y="68" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="700" fill="#B91C1C" text-anchor="middle">wsaidsu_exp</text>
      <text x="85" y="86" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="500" fill="#7F1D1D" text-anchor="middle">Monolithic Cluster DB</text>
    </g>

    <!-- Flows inside Upper Track -->
    <!-- 2a. Run (EXPANDED TO 145px CLEARANCE) -->
    <path d="M 220 85 L 360 85" fill="none" stroke="#0284C7" stroke-width="2.5" marker-end="url(#arrow-cyan)"/>
    <rect x="262" y="74" width="56" height="20" rx="3" fill="#F0F9FF" stroke="#BAE6FD" stroke-width="1"/>
    <text x="290" y="88" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="700" fill="#0369A1" text-anchor="middle">2a. Run</text>

    <!-- 2a_db. Query to DB (EXPANDED TO 150px CLEARANCE) -->
    <path d="M 560 85 L 705 85" fill="none" stroke="#EF4444" stroke-width="2.2" marker-end="url(#arrow-red)"/>
    <rect x="600" y="74" width="70" height="20" rx="3" fill="#FEF2F2" stroke="#FECACA" stroke-width="1"/>
    <text x="635" y="88" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="700" fill="#DC2626" text-anchor="middle">SQL Query</text>

    <!-- 3a. SERIALIZED SYNC RETURN: RUNS BELLOW THE CLUSTER (y=205 inside track / y=240 canvas) -->
    <!-- Exits bottom ellipse of Legacy Storage at x=750, drops to y=205, runs horizontally left back to client origin border (x=-150) -->
    <path d="M 750 145 L 750 205 L -145 205" fill="none" stroke="#D97706" stroke-width="2.2" marker-end="url(#arrow-amber)"/>
    <rect x="180" y="194" width="220" height="22" rx="4" fill="#FFFBEB" stroke="#FDE68A" stroke-width="1"/>
    <text x="290" y="209" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="700" fill="#B45309" text-anchor="middle">3a. Serialized Sync Return (&gt;30-60s)</text>
  </g>


  <!-- ================= ZONE 3: LOWER TRACK (TARGET AWS SERVERLESS, x=380 to x=1320, y=390 to y=620) ================= -->
  <g transform="translate(380, 390)">
    <!-- Container -->
    <rect width="940" height="230" rx="16" fill="#F0FDF4" stroke="#86EFAC" stroke-width="2.2"/>
    <text x="24" y="24" font-family="Helvetica, Arial, sans-serif" font-size="13" font-weight="800" fill="#065F46">LOWER TRACK: TARGET AWS SERVERLESS</text>

    <!-- Unified API Gateway Card (Col 1: x=25 to x=220) -->
    <g transform="translate(25, 35)" filter="url(#shadow)">
      <rect width="195" height="175" rx="14" fill="#FFFFFF" stroke="#8B5CF6" stroke-width="2.2"/>
      <g transform="translate(52, 10)">
        <rect width="90" height="18" rx="4" fill="#EDE9FE"/>
        <text x="45" y="12" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="800" fill="#6D28D9" text-anchor="middle">API GATEWAY</text>
      </g>
      <g transform="translate(81, 32) scale(0.667)">
        <rect width="48" height="48" rx="8" fill="#8B5CF6"/>
        <circle cx="24" cy="14" r="4" fill="#FFFFFF"/>
        <circle cx="14" cy="32" r="4" fill="#FFFFFF"/>
        <circle cx="34" cy="32" r="4" fill="#FFFFFF"/>
        <path d="M24 18V26M24 26L16 30M24 26L32 30" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"/>
      </g>
      <text x="97.5" y="96" font-family="Helvetica, Arial, sans-serif" font-size="17" font-weight="800" fill="#1E1B4B" text-anchor="middle">API Gateway</text>
      <text x="97.5" y="118" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="500" fill="#6B7280" text-anchor="middle">Managed HTTPS Endpoints</text>
      <text x="97.5" y="136" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="600" fill="#7C3AED" text-anchor="middle">Managed Ingress &amp; Egress</text>
    </g>

    <!-- Code Component (Col 2) -->
    <g transform="translate(345, 38)" filter="url(#card-shadow)">
      <rect width="75" height="36" rx="8" fill="#FFFFFF" stroke="#10B981" stroke-width="1.8"/>
      <text x="37.5" y="17" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="800" fill="#065F46" text-anchor="middle">Code</text>
      <text x="37.5" y="29" font-family="Helvetica, Arial, sans-serif" font-size="8" font-weight="700" fill="#059669" text-anchor="middle">DEPLOYED</text>
    </g>

    <!-- Secret Management Component (Col 2) -->
    <g transform="translate(485, 35)" filter="url(#card-shadow)">
      <rect width="135" height="42" rx="10" fill="#FFFFFF" stroke="#EF4444" stroke-width="1.8"/>
      <rect x="8" y="5" width="44" height="11" rx="2" fill="#FEE2E2"/>
      <text x="30" y="13" font-family="Helvetica, Arial, sans-serif" font-size="7.5" font-weight="800" fill="#B91C1C" text-anchor="middle">SECURITY</text>
      <text x="68" y="24" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="800" fill="#991B1B" text-anchor="middle">Secret Management</text>
      <text x="68" y="36" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="500" fill="#7F1D1D" text-anchor="middle">KMS / Secrets Mgr</text>
    </g>

    <!-- AWS Lambda Card (Col 2: x=360 to x=560) -->
    <g transform="translate(360, 88)" filter="url(#shadow)">
      <rect width="200" height="120" rx="14" fill="#FFFFFF" stroke="#D97706" stroke-width="2.5"/>
      <g transform="translate(84, 10) scale(0.667)">
        <rect width="48" height="48" rx="8" fill="#FF9900"/>
        <path d="M14 36L22.5 18H27L35.5 36H30.5L25 24L18.5 36H14Z" fill="#FFFFFF"/>
        <path d="M21 21.5L16.5 12H12L17.5 23.5L21 21.5Z" fill="#FFFFFF"/>
      </g>
      <text x="100" y="70" font-family="Helvetica, Arial, sans-serif" font-size="17" font-weight="800" fill="#0F172A" text-anchor="middle">AWS Lambda</text>
      <text x="100" y="88" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="#D97706" text-anchor="middle">(Aws Lamda)</text>
      <text x="100" y="104" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="500" fill="#64748B" text-anchor="middle">Serverless Compute</text>
    </g>

    <!-- Databricks DBX 3D Cylinder (Col 3: x=710 to x=880 - SHRUNK HORIZONTALLY TO 170px) -->
    <g transform="translate(710, 35)" filter="url(#shadow)">
      <path d="M 0 15 L 0 115 A 85 15 0 0 0 170 115 L 170 15 Z" fill="#F0F9FF" stroke="#0284C7" stroke-width="2.2"/>
      <ellipse cx="85" cy="15" rx="85" ry="15" fill="#E0F2FE" stroke="#0284C7" stroke-width="2.2"/>
      <path d="M 0 115 A 85 15 0 0 0 170 115" fill="none" stroke="#0284C7" stroke-width="2.2"/>
      <g transform="translate(24, 55) scale(1.35)">
        <path d="M13.7194 6.60746L7.25506 10.338L0.332928 6.35214L0 6.53654L0 9.43016L7.25506 13.6004L13.7194 9.88406V11.416L7.25506 15.1465L0.332928 11.1607L0 11.3451L0 11.8415L7.25506 16.0117L14.4962 11.8415V8.94789L14.1633 8.76349L7.25506 12.7351L0.776832 9.01881L0.776832 7.4869L7.25506 11.2032L14.4962 7.033V4.18193L14.1356 3.96917L7.25506 7.92661L1.10976 4.40888L7.25506 0.876967L12.3045 3.78477L12.7484 3.52945V3.17484L7.25506 0.0117187L0 4.18193L0 4.63583L7.25506 8.80605L13.7194 5.07555V6.60746Z" fill="#FF3621"/>
      </g>
      <text x="65" y="70" font-family="Helvetica, Arial, sans-serif" font-size="16" font-weight="800" fill="#0369A1">DBX</text>
      <text x="65" y="88" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="#0284C7">Databricks / DB</text>
    </g>

    <!-- Flows inside Lower Track -->
    <!-- 2b. Invoke (EXPANDED TO 140px CLEARANCE) -->
    <path d="M 220 95 L 355 95" fill="none" stroke="#7C3AED" stroke-width="2.5" marker-end="url(#arrow-purple)"/>
    <rect x="248" y="84" width="84" height="20" rx="3" fill="#F5F3FF" stroke="#DDD6FE" stroke-width="1"/>
    <text x="290" y="97" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="700" fill="#6D28D9" text-anchor="middle">2b. Event Invoke</text>

    <!-- Code & Secrets Injections -->
    <path d="M 382 74 L 382 88" fill="none" stroke="#10B981" stroke-width="2" marker-end="url(#arrow-green)"/>
    <path d="M 535 77 L 515 88" fill="none" stroke="#EF4444" stroke-width="1.8" stroke-dasharray="4,3" marker-end="url(#arrow-red)"/>

    <!-- 3b. ACID SQL Query (EXPANDED TO 150px CLEARANCE) -->
    <path d="M 560 110 L 705 110" fill="none" stroke="#0284C7" stroke-width="2.2" marker-end="url(#arrow-cyan)"/>
    <rect x="600" y="99" width="72" height="20" rx="3" fill="#F0F9FF" stroke="#BAE6FD" stroke-width="1"/>
    <text x="636" y="112" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="700" fill="#0369A1" text-anchor="middle">3b. ACID SQL</text>

    <!-- 4b. Deliver (EXPANDED TO 140px CLEARANCE) -->
    <path d="M 360 155 L 225 155" fill="none" stroke="#7C3AED" stroke-width="2.2" marker-end="url(#arrow-purple)"/>
    <rect x="258" y="160" width="64" height="20" rx="3" fill="#F5F3FF" stroke="#DDD6FE" stroke-width="1"/>
    <text x="290" y="173" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="700" fill="#6D28D9" text-anchor="middle">4b. Deliver</text>
  </g>


  <!-- ================= INGRESS DIVERGENCE & RETURN (EXPANDED TO 175px CLEARANCE) ================= -->

  <!-- 1a. UPPER INGRESS FROM CLIENT CONTAINER BORDER (x=230, y=145) TO CDSW (x=405) -->
  <path d="M 230 145 L 398 145" fill="none" stroke="#DC2626" stroke-width="2.5" marker-end="url(#arrow-red)"/>
  <rect x="275" y="125" width="84" height="28" rx="4" fill="#FEE2E2" stroke="#FECACA" stroke-width="1"/>
  <text x="317" y="137" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#B91C1C" text-anchor="middle">1a. EXE Call</text>
  <text x="317" y="149" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="700" fill="#DC2626" text-anchor="middle">(Deprecated)</text>

  <!-- 1b. LOWER INGRESS FROM CLIENT CONTAINER BORDER (x=230, y=485) TO API GATEWAY (x=405) -->
  <path d="M 230 485 L 398 485" fill="none" stroke="#2563EB" stroke-width="2.5" marker-end="url(#arrow-blue)"/>
  <rect x="275" y="465" width="86" height="28" rx="4" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
  <text x="318" y="477" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#1D4ED8" text-anchor="middle">1b. HTTPS REST</text>
  <text x="318" y="489" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="600" fill="#2563EB" text-anchor="middle">(Managed Ingress)</text>

  <!-- 5b. SUB-100MS RESPONSE FROM API GATEWAY (x=405, y=545) TO CLIENT BORDER (x=230) -->
  <path d="M 405 545 L 236 545" fill="none" stroke="#2563EB" stroke-width="2.5" marker-end="url(#arrow-blue)"/>
  <rect x="275" y="552" width="86" height="28" rx="4" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
  <text x="318" y="564" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#1D4ED8" text-anchor="middle">5b. Sub-100ms</text>
  <text x="318" y="576" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="600" fill="#2563EB" text-anchor="middle">Fast Response</text>


  <!-- ================= VERTICAL MIGRATION TRANSITIONS (SOLID, DIRECT, UNCLIPPED) ================= -->
  <!-- Rendered on top of tracks so arrow heads and full paths are 100% visible and unclipped -->

  <!-- Bridge 1: Refactor Code (Col 2: Upper Track bottom at x=840 -> AWS Lambda top at x=840) -->
  <path d="M 840 260 L 840 475" fill="none" stroke="#D97706" stroke-width="2.5" marker-end="url(#arrow-amber)"/>
  <rect x="705" y="312" width="270" height="24" rx="4" fill="#FEF3C7" stroke="#FDE68A" stroke-width="1.2"/>
  <text x="840" y="328" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="800" fill="#B45309" text-anchor="middle">Modernize: 1-Task Script ➔ Serverless Lambda</text>

  <!-- Bridge 2: Data Migration (Col 3: Upper Track bottom at x=1175 -> Databricks DBX top at x=1175) -->
  <path d="M 1175 260 L 1175 422" fill="none" stroke="#0284C7" stroke-width="2.5" marker-end="url(#arrow-cyan)"/>
  <rect x="1030" y="312" width="290" height="24" rx="4" fill="#E0F2FE" stroke="#BAE6FD" stroke-width="1.2"/>
  <text x="1175" y="328" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="800" fill="#0369A1" text-anchor="middle">Data Migration: Legacy HDFS ➔ Databricks Delta</text>

</svg>
"""
    return svg.replace("{CML_PATH_D}", cml_path_d)

def main():
    drawio_path = Path("output/diagrams/whitelist_system_interwoven_migration.drawio")
    svg_path = Path("output/diagrams/whitelist_system_interwoven_migration.svg")
    png_path = Path("output/diagrams/whitelist_system_interwoven_migration.png")
    drawio_svg_path = Path("output/diagrams/whitelist_system_interwoven_migration.drawio.svg")

    # Cache-busted copies (v4)
    png_v4_path = Path("output/diagrams/whitelist_system_interwoven_migration_v4.png")
    temp_png_v4 = Path("TEMP/whitelist_system_interwoven_migration_v4.png")

    temp_drawio = Path("TEMP/whitelist_system_interwoven_migration.drawio")
    temp_svg = Path("TEMP/whitelist_system_interwoven_migration.svg")
    temp_png = Path("TEMP/whitelist_system_interwoven_migration.png")
    temp_drawio_svg = Path("TEMP/whitelist_system_interwoven_migration.drawio.svg")

    artifact_dir = Path("/Users/marcelljw/.gemini/antigravity/brain/d95a63dd-7a66-4b47-b53e-86ce3990d3c0")
    artifact_png_path = artifact_dir / "whitelist_system_interwoven_migration.png"
    artifact_png_v4 = artifact_dir / "whitelist_system_interwoven_migration_v4.png"

    drawio_path.parent.mkdir(parents=True, exist_ok=True)
    temp_drawio.parent.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)

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

    # 3. Export to High-Resolution PNG (300+ DPI via rsvg-convert)
    res = subprocess.run(["rsvg-convert", "-z", "3", str(svg_path), "-o", str(png_path)], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"✓ Exported High-Resolution PNG to: {png_path} using rsvg-convert")
        shutil.copy2(png_path, temp_png)
        shutil.copy2(png_path, png_v4_path)
        shutil.copy2(png_path, temp_png_v4)
    else:
        print(f"rsvg-convert failed: {res.stderr}")
        try:
            from src.ppt_engine.diagram_engine import _setup_cairo_library
            _setup_cairo_library()
            import cairosvg
            cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), write_to=str(png_path), scale=3)
            shutil.copy2(png_path, temp_png)
            shutil.copy2(png_path, png_v4_path)
            shutil.copy2(png_path, temp_png_v4)
            print(f"✓ Exported High-Resolution PNG via cairosvg")
        except Exception as e:
            print(f"cairosvg fallback failed: {e}")

    # 4. Copy PNG to artifact directory
    shutil.copy2(png_path, artifact_png_path)
    shutil.copy2(png_path, artifact_png_v4)
    print(f"✓ Copied PNG to artifact directory: {artifact_png_path} and {artifact_png_v4}")

    # 5. Build hybrid .drawio.svg
    import html
    escaped_xml = html.escape(xml_content, quote=True)
    svg_with_content = re.sub(r"<svg(\s+)", rf'<svg content="{escaped_xml}"\1', svg_content, count=1)
    desc_tag = f'\n  <desc><![CDATA[{xml_content}]]></desc>\n'
    idx = svg_with_content.rfind("</svg>")
    hybrid_svg = svg_with_content[:idx] + desc_tag + svg_with_content[idx:]
    drawio_svg_path.write_text(hybrid_svg, encoding="utf-8")
    temp_drawio_svg.write_text(hybrid_svg, encoding="utf-8")
    print(f"✓ Generated hybrid .drawio.svg: {drawio_svg_path} and {temp_drawio_svg}")

    # 6. Update master project TEMP/device_whitelist_system.drawio with page 7
    master_drawio = Path("TEMP/device_whitelist_system.drawio")
    if master_drawio.exists():
        master_tree = ET.parse(master_drawio)
        master_root = master_tree.getroot()
        for diag in list(master_root.findall("diagram")):
            if diag.attrib.get("id") == "interwoven_migration" or "Interwoven" in diag.attrib.get("name", ""):
                master_root.remove(diag)
        new_tree = ET.parse(drawio_path)
        master_root.append(new_tree.getroot().find("diagram"))
        raw = ET.tostring(master_root, encoding="utf-8")
        master_drawio.write_text(minidom.parseString(raw).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8"))
        print(f"✓ Updated master project: {master_drawio}")

    # 7. Generate browser URL and launcher
    compressor = zlib.compressobj(level=9, method=zlib.DEFLATED, wbits=-15)
    deflated = compressor.compress(xml_content.encode('utf-8')) + compressor.flush()
    b64 = base64.b64encode(deflated).decode('ascii')
    url_encoded = urllib.parse.quote(b64)
    new_url = f"https://app.diagrams.net/#R{url_encoded}"

    html_file = Path("TEMP/open_interwoven_in_browser.html")
    html_file.write_text(f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url='{new_url}'" />
    <title>Opening Interwoven Migration Architecture in Draw.io...</title>
</head>
<body>
    <p>Opening Interwoven Migration Architecture in Diagrams.net / Draw.io... If not redirected, <a href="{new_url}">click here</a>.</p>
</body>
</html>""", encoding="utf-8")
    print(f"✓ Updated browser launcher: {html_file}")

if __name__ == "__main__":
    main()
