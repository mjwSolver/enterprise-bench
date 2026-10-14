#!/usr/bin/env python3
"""
Generate Combined Before & After Whitelisting System Architecture Visualization.

This script compiles:
1. High-fidelity vector SVG (whitelist_system_before_after_comparison.svg)
2. Interactive multi-shape Draw.io XML (whitelist_system_before_after_comparison.drawio)
3. High-resolution 300+ DPI PNG via rsvg-convert (whitelist_system_before_after_comparison.png)
4. Hybrid editable .drawio.svg (whitelist_system_before_after_comparison.drawio.svg)
5. Updates master Draw.io workbook (TEMP/device_whitelist_system.drawio)
6. Updates TEMP/index.html & TEMP/README.md
7. Copies PNG to current conversation artifact directory
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

# 1. Load SVG logos for base64 data URIs
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
  <diagram id="before_after_comparison" name="Before vs After : Whitelist Modernization">
    <mxGraphModel dx="1840" dy="1060" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1840" pageHeight="1060" background="#FFFFFF" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- ================= TOP HEADER ================= -->
        <mxCell id="header_title" value="&lt;b style=&quot;font-size:24px; color:#0F172A; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;&quot;&gt;Device Whitelisting System: Architecture Evolution (Before vs. After)&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:13px; color:#64748B;&quot;&gt;Monolithic Cloudera CDSW Batch Execution vs. Proposed Decoupled AWS Lambda Serverless Topology&lt;/span&gt;" style="text;html=1;align=left;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="40" y="22" width="850" height="50" as="geometry"/>
        </mxCell>

        <!-- HEADER STATUS BADGE -->
        <mxCell id="header_badge" value="&lt;div style=&quot;background:#EFF6FF; border:1px solid #BFDBFE; border-radius:6px; padding:6px 12px; color:#1D4ED8; font-weight:800; font-size:11px; letter-spacing:0.5px;&quot;&gt;🔄 MODERNIZATION SPEC &amp;amp; COMPARISON&lt;/div&gt;" style="text;html=1;align=right;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="1540" y="26" width="260" height="36" as="geometry"/>
        </mxCell>

        <!-- ================= TOP KPI DELTA RIBBON ================= -->
        <mxCell id="delta_ribbon_bg" value="" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#F8FAFC;strokeColor=#CBD5E1;strokeWidth=1.5;" vertex="1" parent="1">
          <mxGeometry x="40" y="80" width="1760" height="48" as="geometry"/>
        </mxCell>

        <mxCell id="kpi_1" value="&lt;b style=&quot;color:#64748B; font-size:10px;&quot;&gt;EXECUTION MODEL:&lt;/b&gt; &lt;span style=&quot;color:#DC2626; font-weight:700;&quot;&gt;Sequential Batch&lt;/span&gt; ➔ &lt;span style=&quot;color:#16A34A; font-weight:700;&quot;&gt;Event-Driven Serverless&lt;/span&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;fontFamily=Helvetica, Arial, sans-serif;fontSize=11.5;" vertex="1" parent="1">
          <mxGeometry x="50" y="86" width="410" height="36" as="geometry"/>
        </mxCell>

        <mxCell id="kpi_2" value="&lt;b style=&quot;color:#64748B; font-size:10px;&quot;&gt;INGRESS GATEWAY:&lt;/b&gt; &lt;span style=&quot;color:#DC2626; font-weight:700;&quot;&gt;Direct Binary EXE&lt;/span&gt; ➔ &lt;span style=&quot;color:#16A34A; font-weight:700;&quot;&gt;Managed HTTPS REST API&lt;/span&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;fontFamily=Helvetica, Arial, sans-serif;fontSize=11.5;" vertex="1" parent="1">
          <mxGeometry x="480" y="86" width="420" height="36" as="geometry"/>
        </mxCell>

        <mxCell id="kpi_3" value="&lt;b style=&quot;color:#64748B; font-size:10px;&quot;&gt;CREDENTIAL SECURITY:&lt;/b&gt; &lt;span style=&quot;color:#DC2626; font-weight:700;&quot;&gt;Script Environment&lt;/span&gt; ➔ &lt;span style=&quot;color:#16A34A; font-weight:700;&quot;&gt;AWS Secrets Mgr &amp;amp; KMS&lt;/span&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;fontFamily=Helvetica, Arial, sans-serif;fontSize=11.5;" vertex="1" parent="1">
          <mxGeometry x="920" y="86" width="420" height="36" as="geometry"/>
        </mxCell>

        <mxCell id="kpi_4" value="&lt;b style=&quot;color:#64748B; font-size:10px;&quot;&gt;DATA PERSISTENCE:&lt;/b&gt; &lt;span style=&quot;color:#DC2626; font-weight:700;&quot;&gt;Shared Cluster Store&lt;/span&gt; ➔ &lt;span style=&quot;color:#16A34A; font-weight:700;&quot;&gt;Databricks Lakehouse (DBX)&lt;/span&gt;" style="text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;fontFamily=Helvetica, Arial, sans-serif;fontSize=11.5;" vertex="1" parent="1">
          <mxGeometry x="1360" y="86" width="420" height="36" as="geometry"/>
        </mxCell>

        <!-- ================= LEFT PANEL: CURRENT STATE (BEFORE) ================= -->
        <mxCell id="panel_left_bg" value="" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFDFB;strokeColor=#FCA5A5;strokeWidth=2;" vertex="1" parent="1">
          <mxGeometry x="40" y="142" width="860" height="678" as="geometry"/>
        </mxCell>

        <!-- LEFT PANEL HEADER -->
        <mxCell id="panel_left_header" value="&lt;div style=&quot;font-size:16px; font-weight:800; color:#991B1B;&quot;&gt;BEFORE: Current Legacy CDSW Job Execution&lt;/div&gt;&lt;div style=&quot;font-size:11px; color:#B45309; font-weight:600;&quot;&gt;Monolithic Synchronous Batch Processing &amp;amp; Bottleneck Lifecycle&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#FECACA;strokeWidth=1;align=left;spacingLeft=18;" vertex="1" parent="1">
          <mxGeometry x="40" y="142" width="860" height="52" as="geometry"/>
        </mxCell>

        <!-- LEFT PANEL BADGES -->
        <mxCell id="badge_left_legacy" value="&lt;span style=&quot;background:#FEE2E2; color:#DC2626; font-size:10px; font-weight:800; padding:3px 8px; border-radius:4px; border:1px solid #FECACA;&quot;&gt;⚠️ HIGH DEBT&lt;/span&gt; &lt;span style=&quot;background:#FEF3C7; color:#B45309; font-size:10px; font-weight:800; padding:3px 8px; border-radius:4px; border:1px solid #FDE68A;&quot;&gt;SYNCHRONOUS&lt;/span&gt;" style="text;html=1;align=right;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="690" y="152" width="190" height="30" as="geometry"/>
        </mxCell>

        <!-- LEFT: CLIENT APPLICATIONS CONTAINER -->
        <mxCell id="left_group_apps" value="Client Applications" style="rounded=1;arcSize=16;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#94A3B8;strokeWidth=2;fillColor=#F8FAFC;fillOpacity=50;fontFamily=Helvetica, Arial, sans-serif;fontColor=#475569;fontSize=12;fontStyle=2;align=center;verticalAlign=top;spacingTop=12;" vertex="1" parent="1">
          <mxGeometry x="65" y="215" width="230" height="350" as="geometry"/>
        </mxCell>

        <!-- LEFT APP 1 -->
        <mxCell id="left_app1" value="&lt;div style=&quot;font-weight:700; font-size:14px; color:#1E3A8A; margin-bottom:2px;&quot;&gt;app1&lt;/div&gt;&lt;div style=&quot;font-size:20px;&quot;&gt;🖥️&lt;/div&gt;&lt;div style=&quot;font-size:10px; color:#64748B;&quot;&gt;Device 1&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="125" y="250" width="110" height="82" as="geometry"/>
        </mxCell>

        <!-- LEFT APP 2 -->
        <mxCell id="left_app2" value="&lt;div style=&quot;font-weight:700; font-size:13px; color:#1E3A8A;&quot;&gt;app2&lt;/div&gt;&lt;div style=&quot;font-size:18px;&quot;&gt;🖥️&lt;/div&gt;&lt;div style=&quot;font-size:9.5px; color:#64748B;&quot;&gt;Device 2&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="80" y="375" width="95" height="80" as="geometry"/>
        </mxCell>

        <!-- LEFT APP 3 -->
        <mxCell id="left_app3" value="&lt;div style=&quot;font-weight:700; font-size:13px; color:#1E3A8A;&quot;&gt;app3&lt;/div&gt;&lt;div style=&quot;font-size:18px;&quot;&gt;🖥️&lt;/div&gt;&lt;div style=&quot;font-size:9.5px; color:#64748B;&quot;&gt;Device 3&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="185" y="375" width="95" height="80" as="geometry"/>
        </mxCell>

        <!-- LEFT: BACKEND EXECUTION BOUNDARY -->
        <mxCell id="left_group_backend" value="Backend Execution Boundary" style="rounded=1;arcSize=14;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#F59E0B;strokeWidth=2;fillColor=#FFFBEB;fillOpacity=35;fontFamily=Helvetica, Arial, sans-serif;fontColor=#B45309;fontSize=12;fontStyle=1;align=left;verticalAlign=top;spacingLeft=16;spacingTop=12;" vertex="1" parent="1">
          <mxGeometry x="320" y="215" width="560" height="350" as="geometry"/>
        </mxCell>

        <!-- LEFT: CLOUDERA CDSW BADGE -->
        <mxCell id="left_badge_cloudera" value="&lt;span style=&quot;background:#FEF3C7; color:#B45309; font-size:10px; font-weight:800; padding:2px 8px; border-radius:4px; border:1px solid #FDE68A;&quot;&gt;CLOUDERA CDSW&lt;/span&gt;" style="text;html=1;align=right;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="725" y="224" width="140" height="24" as="geometry"/>
        </mxCell>

        <!-- LEFT: CDSW JOB CARD -->
        <mxCell id="left_node_cdsw" value="&lt;div style=&quot;margin-bottom:4px;&quot;&gt;&lt;img src=&quot;{cloudera_data_uri}&quot; width=&quot;26&quot; height=&quot;26&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-size:16px; font-weight:800; color:#0F172A;&quot;&gt;CDSW JOB&lt;/div&gt;&lt;div style=&quot;font-size:10.5px; color:#475569; margin-top:2px;&quot;&gt;Cloudera Data Science&lt;/div&gt;&lt;div style=&quot;font-size:9.5px; color:#64748B;&quot;&gt;Workbench Job Runner&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#0284C7;strokeWidth=2.2;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="345" y="295" width="155" height="120" as="geometry"/>
        </mxCell>

        <!-- LEFT: 1 TASK WARNINGS -->
        <mxCell id="left_warnings" value="&lt;div style=&quot;display:flex; gap:6px;&quot;&gt;&lt;span style=&quot;background:#FEE2E2; color:#DC2626; font-size:9px; font-weight:800; padding:2px 6px; border-radius:3px;&quot;&gt;⚠️ BOTTLENECK&lt;/span&gt; &lt;span style=&quot;background:#FEF3C7; color:#B45309; font-size:9px; font-weight:800; padding:2px 6px; border-radius:3px;&quot;&gt;⚠️ SYNCHRONOUS&lt;/span&gt;&lt;/div&gt;" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="540" y="260" width="200" height="24" as="geometry"/>
        </mxCell>

        <!-- LEFT: 1 TASK CARD -->
        <mxCell id="left_node_task" value="&lt;div style=&quot;font-size:20px; font-weight:800; color:#0F172A;&quot;&gt;&lt;u&gt;1&lt;/u&gt; Task&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#DC2626;strokeWidth=2.5;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="540" y="290" width="145" height="65" as="geometry"/>
        </mxCell>

        <!-- LEFT: TASK STEPS BULLET LIST -->
        <mxCell id="left_task_steps" value="&lt;div style=&quot;text-align:left; font-size:12.5px; font-family:Helvetica, Arial, sans-serif; color:#0F172A; line-height:1.8;&quot;&gt;&lt;b&gt;• Input metadata&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• SQL Query&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• Filter &amp;amp; Search Dev. ADD&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• Logging&lt;/b&gt;&lt;br/&gt;&lt;b&gt;• Return to sender&lt;/b&gt;&lt;/div&gt;" style="text;html=1;align=left;verticalAlign=top;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="540" y="370" width="220" height="120" as="geometry"/>
        </mxCell>

        <!-- LEFT CONNECTORS -->
        <mxCell id="edge_left_apps_to_cdsw" value="1. EXE Call" style="edgeStyle=curvedEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#2563EB;strokeWidth=2.2;fontColor=#1D4ED8;fontSize=10;fontStyle=1;exitX=1;exitY=0.25;entryX=0;entryY=0.5;" edge="1" parent="1" source="left_group_apps" target="left_node_cdsw">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="320" y="270"/>
            </Array>
          </mxGeometry>
        </mxCell>

        <mxCell id="edge_left_cdsw_to_task" value="2. Run" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#0284C7;strokeWidth=2.2;fontColor=#0369A1;fontSize=10;fontStyle=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;" edge="1" parent="1" source="left_node_cdsw" target="left_node_task">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <mxCell id="edge_left_task_to_return" value="3. Return / 4. Response" style="edgeStyle=curvedEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#D97706;strokeWidth=2.2;fontColor=#B45309;fontSize=10;fontStyle=1;exitX=1;exitY=0.5;entryX=0.9;entryY=0.95;" edge="1" parent="1" source="left_node_task" target="left_group_apps">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="840" y="322"/>
              <mxPoint x="840" y="535"/>
              <mxPoint x="320" y="535"/>
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- LEFT: ARCHITECTURAL DEBT CARD (BOTTOM OF LEFT PANEL) -->
        <mxCell id="left_debt_card" value="&lt;div style=&quot;text-align:left; font-family:Helvetica, Arial, sans-serif;&quot;&gt;&lt;div style=&quot;font-size:12.5px; font-weight:800; color:#B91C1C; margin-bottom:6px;&quot;&gt;CRITICAL ARCHITECTURAL BOTTLENECK &amp;amp; RISKS:&lt;/div&gt;&lt;div style=&quot;font-size:11px; color:#475569; line-height:1.6;&quot;&gt;• &lt;b style=&quot;color:#0F172A;&quot;&gt;Single-Task Lock:&lt;/b&gt; Entire batch is serialized; concurrent requests queue and cause high latency.&lt;br/&gt;• &lt;b style=&quot;color:#0F172A;&quot;&gt;Fragile Ingress:&lt;/b&gt; Direct executable invocation lacks TLS, rate limiting, and automated retries.&lt;br/&gt;• &lt;b style=&quot;color:#0F172A;&quot;&gt;Exposed Secrets:&lt;/b&gt; Plaintext database credentials hardcoded inside CDSW runner scripts.&lt;/div&gt;&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#FECACA;strokeWidth=1.5;align=left;spacingLeft=14;spacingRight=14;" vertex="1" parent="1">
          <mxGeometry x="65" y="582" width="815" height="188" as="geometry"/>
        </mxCell>


        <!-- ================= RIGHT PANEL: TARGET STATE (AFTER) ================= -->
        <mxCell id="panel_right_bg" value="" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#F0FDF4;strokeColor=#86EFAC;strokeWidth=2;" vertex="1" parent="1">
          <mxGeometry x="940" y="142" width="860" height="678" as="geometry"/>
        </mxCell>

        <!-- RIGHT PANEL HEADER -->
        <mxCell id="panel_right_header" value="&lt;div style=&quot;font-size:16px; font-weight:800; color:#065F46;&quot;&gt;AFTER: Proposed AWS Lambda Serverless Architecture&lt;/div&gt;&lt;div style=&quot;font-size:11px; color:#059669; font-weight:600;&quot;&gt;Event-Driven Decoupled Services &amp;amp; Sub-Second Lifecycle Dataflow&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#ECFDF5;strokeColor=#A7F3D0;strokeWidth=1;align=left;spacingLeft=18;" vertex="1" parent="1">
          <mxGeometry x="940" y="142" width="860" height="52" as="geometry"/>
        </mxCell>

        <!-- RIGHT PANEL BADGES -->
        <mxCell id="badge_right_target" value="&lt;span style=&quot;background:#DCFCE7; color:#15803D; font-size:10px; font-weight:800; padding:3px 8px; border-radius:4px; border:1px solid #BBF7D0;&quot;&gt;✓ SUB-SECOND SLA&lt;/span&gt; &lt;span style=&quot;background:#EDE9FE; color:#6D28D9; font-size:10px; font-weight:800; padding:3px 8px; border-radius:4px; border:1px solid #DDD6FE;&quot;&gt;AUTO-SCALING&lt;/span&gt;" style="text;html=1;align=right;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="1590" y="152" width="200" height="30" as="geometry"/>
        </mxCell>

        <!-- RIGHT: CLIENT APPLICATIONS CONTAINER -->
        <mxCell id="right_group_apps" value="Client Applications" style="rounded=1;arcSize=16;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#94A3B8;strokeWidth=2;fillColor=#F8FAFC;fillOpacity=50;fontFamily=Helvetica, Arial, sans-serif;fontColor=#475569;fontSize=12;fontStyle=2;align=center;verticalAlign=top;spacingTop=12;" vertex="1" parent="1">
          <mxGeometry x="965" y="215" width="230" height="350" as="geometry"/>
        </mxCell>

        <!-- RIGHT APP 1 -->
        <mxCell id="right_app1" value="&lt;div style=&quot;font-weight:700; font-size:14px; color:#1E3A8A; margin-bottom:2px;&quot;&gt;app1&lt;/div&gt;&lt;div style=&quot;font-size:20px;&quot;&gt;🖥️&lt;/div&gt;&lt;div style=&quot;font-size:10px; color:#64748B;&quot;&gt;Device 1&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="1025" y="250" width="110" height="82" as="geometry"/>
        </mxCell>

        <!-- RIGHT APP 2 -->
        <mxCell id="right_app2" value="&lt;div style=&quot;font-weight:700; font-size:13px; color:#1E3A8A;&quot;&gt;app2&lt;/div&gt;&lt;div style=&quot;font-size:18px;&quot;&gt;🖥️&lt;/div&gt;&lt;div style=&quot;font-size:9.5px; color:#64748B;&quot;&gt;Device 2&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="980" y="375" width="95" height="80" as="geometry"/>
        </mxCell>

        <!-- RIGHT APP 3 -->
        <mxCell id="right_app3" value="&lt;div style=&quot;font-weight:700; font-size:13px; color:#1E3A8A;&quot;&gt;app3&lt;/div&gt;&lt;div style=&quot;font-size:18px;&quot;&gt;🖥️&lt;/div&gt;&lt;div style=&quot;font-size:9.5px; color:#64748B;&quot;&gt;Device 3&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="1085" y="375" width="95" height="80" as="geometry"/>
        </mxCell>

        <!-- RIGHT: UNIFIED API GATEWAY CARD -->
        <mxCell id="right_node_api_gw" value="&lt;div style=&quot;margin-bottom:4px;&quot;&gt;&lt;img src=&quot;{api_gw_data_uri}&quot; width=&quot;26&quot; height=&quot;26&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-size:9.5px; font-weight:800; color:#7C3AED; background:#EDE9FE; display:inline-block; padding:2px 6px; border-radius:4px; margin-bottom:3px;&quot;&gt;API GATEWAY&lt;/div&gt;&lt;div style=&quot;font-size:15px; font-weight:800; color:#1E1B4B;&quot;&gt;API Gateway&lt;/div&gt;&lt;div style=&quot;font-size:10px; color:#6B7280; margin-top:2px;&quot;&gt;HTTP / REST Endpoints&lt;/div&gt;&lt;div style=&quot;font-size:9px; font-weight:600; color:#7C3AED;&quot;&gt;Request &amp;amp; Response Delivery&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#8B5CF6;strokeWidth=2.2;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="1225" y="285" width="150" height="140" as="geometry"/>
        </mxCell>

        <!-- RIGHT: AWS CLOUD BOUNDARY CONTAINER -->
        <mxCell id="right_group_aws" value="AWS Cloud" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#F59E0B;strokeWidth=2;fillColor=#FFFBEB;fillOpacity=35;fontFamily=Helvetica, Arial, sans-serif;fontColor=#B45309;fontSize=12;fontStyle=1;align=left;verticalAlign=top;spacingLeft=14;spacingTop=10;" vertex="1" parent="1">
          <mxGeometry x="1405" y="205" width="375" height="245" as="geometry"/>
        </mxCell>

        <!-- RIGHT: AWS CLOUD BADGE -->
        <mxCell id="right_badge_aws" value="&lt;span style=&quot;background:#FEF3C7; color:#B45309; font-size:9.5px; font-weight:800; padding:2px 6px; border-radius:4px; border:1px solid #FDE68A;&quot;&gt;AWS CLOUD&lt;/span&gt;" style="text;html=1;align=right;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="1685" y="415" width="85" height="22" as="geometry"/>
        </mxCell>

        <!-- RIGHT: CODE DEPLOYED -->
        <mxCell id="right_node_code" value="&lt;div style=&quot;font-weight:700; font-size:12px; color:#065F46;&quot;&gt;Code&lt;/div&gt;&lt;div style=&quot;font-size:8.5px; font-weight:600; color:#059669;&quot;&gt;DEPLOYED&lt;/div&gt;" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#ECFDF5;strokeColor=#10B981;strokeWidth=1.5;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="1485" y="230" width="75" height="36" as="geometry"/>
        </mxCell>

        <!-- RIGHT: SECRET MANAGEMENT -->
        <mxCell id="right_node_secrets" value="&lt;div style=&quot;font-size:8.5px; font-weight:700; color:#DC2626; text-transform:uppercase;&quot;&gt;Security&lt;/div&gt;&lt;div style=&quot;font-size:12.5px; font-weight:700; color:#991B1B;&quot;&gt;Secret Management&lt;/div&gt;&lt;div style=&quot;font-size:9px; color:#7F1D1D;&quot;&gt;KMS / Secrets Mgr&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#EF4444;strokeWidth=1.8;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="1585" y="225" width="145" height="55" as="geometry"/>
        </mxCell>

        <!-- RIGHT: AWS LAMBDA CARD -->
        <mxCell id="right_node_lambda" value="&lt;div style=&quot;margin-bottom:3px;&quot;&gt;&lt;img src=&quot;{lambda_data_uri}&quot; width=&quot;26&quot; height=&quot;26&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-size:15px; font-weight:800; color:#0F172A;&quot;&gt;AWS Lambda&lt;/div&gt;&lt;div style=&quot;font-size:10.5px; font-weight:600; color:#D97706;&quot;&gt;(Aws Lamda)&lt;/div&gt;&lt;div style=&quot;font-size:9.5px; color:#64748B;&quot;&gt;Serverless Compute&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#D97706;strokeWidth=2.2;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="1435" y="310" width="155" height="100" as="geometry"/>
        </mxCell>

        <!-- RIGHT: DBX DATABASE CYLINDER -->
        <mxCell id="right_node_dbx" value="&lt;table style=&quot;margin:auto;&quot;&gt;&lt;tr&gt;&lt;td style=&quot;vertical-align:middle; padding-right:8px;&quot;&gt;&lt;img src=&quot;{dbx_data_uri}&quot; width=&quot;18&quot; height=&quot;20&quot;/&gt;&lt;/td&gt;&lt;td style=&quot;text-align:left; vertical-align:middle;&quot;&gt;&lt;div style=&quot;font-size:14px; font-weight:800; color:#0369A1; line-height:1.2;&quot;&gt;DBX&lt;/div&gt;&lt;div style=&quot;font-size:10px; font-weight:600; color:#0284C7;&quot;&gt;Databricks / DB&lt;/div&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;fillColor=#F0F9FF;strokeColor=#0284C7;strokeWidth=2;shadow=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="1630" y="465" width="135" height="80" as="geometry"/>
        </mxCell>

        <!-- RIGHT CONNECTORS -->
        <mxCell id="edge_right_apps_to_gw" value="1. Request" style="edgeStyle=curvedEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#2563EB;strokeWidth=2.2;fontColor=#1D4ED8;fontSize=10;fontStyle=1;exitX=1;exitY=0.25;entryX=0;entryY=0.25;" edge="1" parent="1" source="right_group_apps" target="right_node_api_gw">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <mxCell id="edge_right_gw_to_lambda" value="2. Invoke" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#7C3AED;strokeWidth=2.2;fontColor=#6D28D9;fontSize=10;fontStyle=1;exitX=1;exitY=0.55;entryX=0;entryY=0.35;" edge="1" parent="1" source="right_node_api_gw" target="right_node_lambda">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <mxCell id="edge_right_code_to_lambda" value="" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#10B981;strokeWidth=2;exitX=0.5;exitY=1;entryX=0.65;entryY=0;" edge="1" parent="1" source="right_node_code" target="right_node_lambda">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <mxCell id="edge_right_secrets_to_lambda" value="Secrets" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#EF4444;strokeWidth=1.8;dashed=1;dashPattern=4 3;fontColor=#DC2626;fontSize=9.5;fontStyle=1;exitX=0;exitY=0.75;entryX=1;entryY=0.25;" edge="1" parent="1" source="right_node_secrets" target="right_node_lambda">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <mxCell id="edge_right_lambda_to_dbx" value="SQL Query" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#0284C7;strokeWidth=2;fontColor=#0369A1;fontSize=9.5;fontStyle=1;exitX=1;exitY=0.8;entryX=0;entryY=0.3;" edge="1" parent="1" source="right_node_lambda" target="right_node_dbx">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <mxCell id="edge_right_dbx_to_lambda" value="" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#0284C7;strokeWidth=2;exitX=0;exitY=0.65;entryX=0.85;entryY=1;" edge="1" parent="1" source="right_node_dbx" target="right_node_lambda">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <mxCell id="edge_right_lambda_to_gw" value="5. Deliver" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#7C3AED;strokeWidth=2.2;fontColor=#6D28D9;fontSize=10;fontStyle=1;exitX=0;exitY=0.75;entryX=1;entryY=0.85;" edge="1" parent="1" source="right_node_lambda" target="right_node_api_gw">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <mxCell id="edge_right_gw_to_apps" value="6. Response" style="edgeStyle=curvedEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#2563EB;strokeWidth=2.2;fontColor=#1D4ED8;fontSize=10;fontStyle=1;exitX=0;exitY=0.80;entryX=1;entryY=0.80;" edge="1" parent="1" source="right_node_api_gw" target="right_group_apps">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- RIGHT: TARGET STATE VALUE REALIZATION CARD (BOTTOM OF RIGHT PANEL) -->
        <mxCell id="right_value_card" value="&lt;div style=&quot;text-align:left; font-family:Helvetica, Arial, sans-serif;&quot;&gt;&lt;div style=&quot;font-size:12.5px; font-weight:800; color:#065F46; margin-bottom:6px;&quot;&gt;TARGET ARCHITECTURE ADVANTAGES &amp;amp; VALUE REALIZATION:&lt;/div&gt;&lt;div style=&quot;font-size:11px; color:#475569; line-height:1.6;&quot;&gt;• &lt;b style=&quot;color:#0F172A;&quot;&gt;Elastic Auto-Scaling:&lt;/b&gt; Micro-billing Lambda invocations scale 0 to 1,000+ without resource starvation.&lt;br/&gt;• &lt;b style=&quot;color:#0F172A;&quot;&gt;Hardened API Gateway:&lt;/b&gt; Managed HTTPS endpoints enforce TLS, token authentication, and throttling.&lt;br/&gt;• &lt;b style=&quot;color:#0F172A;&quot;&gt;Zero-Trust Security:&lt;/b&gt; IAM execution roles fetch KMS-encrypted credentials just-in-time from Secrets Manager.&lt;/div&gt;&lt;/div&gt;" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#A7F3D0;strokeWidth=1.5;align=left;spacingLeft=14;spacingRight=14;" vertex="1" parent="1">
          <mxGeometry x="965" y="582" width="815" height="188" as="geometry"/>
        </mxCell>


        <!-- ================= BOTTOM ZONE: ARCHITECTURAL DELTA MATRIX ================= -->
        <mxCell id="matrix_bg" value="" style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#CBD5E1;strokeWidth=1.5;" vertex="1" parent="1">
          <mxGeometry x="40" y="835" width="1760" height="195" as="geometry"/>
        </mxCell>

        <!-- TABLE HEADER -->
        <mxCell id="matrix_th" value="" style="rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#F1F5F9;strokeColor=#E2E8F0;strokeWidth=1;" vertex="1" parent="1">
          <mxGeometry x="40" y="835" width="1760" height="36" as="geometry"/>
        </mxCell>
        <mxCell id="th_col1" value="&lt;b style=&quot;font-size:11px; color:#475569;&quot;&gt;DIMENSION / CRITERIA&lt;/b&gt;" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;spacingLeft=16;" vertex="1" parent="1">
          <mxGeometry x="40" y="835" width="260" height="36" as="geometry"/>
        </mxCell>
        <mxCell id="th_col2" value="&lt;b style=&quot;font-size:11px; color:#DC2626;&quot;&gt;CURRENT STATE (LEGACY CDSW)&lt;/b&gt;" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="310" y="835" width="450" height="36" as="geometry"/>
        </mxCell>
        <mxCell id="th_col3" value="&lt;b style=&quot;font-size:11px; color:#16A34A;&quot;&gt;PROPOSED TARGET (AWS LAMBDA)&lt;/b&gt;" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="780" y="835" width="470" height="36" as="geometry"/>
        </mxCell>
        <mxCell id="th_col4" value="&lt;b style=&quot;font-size:11px; color:#2563EB;&quot;&gt;STRATEGIC BUSINESS IMPACT&lt;/b&gt;" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="1270" y="835" width="520" height="36" as="geometry"/>
        </mxCell>

        <!-- ROW 1: THROUGHPUT & LATENCY -->
        <mxCell id="r1_c1" value="&lt;b style=&quot;color:#0F172A;&quot;&gt;Throughput &amp;amp; Latency&lt;/b&gt;" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;spacingLeft=16;fontSize=11.5;" vertex="1" parent="1">
          <mxGeometry x="40" y="875" width="260" height="45" as="geometry"/>
        </mxCell>
        <mxCell id="r1_c2" value="&lt;span style=&quot;color:#DC2626; font-weight:700;&quot;&gt;Serialized 1-task queue;&lt;/span&gt; high job spin-up latency (&amp;gt;30-60s per batch); risk of thread starvation" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;fontSize=11.5;" vertex="1" parent="1">
          <mxGeometry x="310" y="875" width="450" height="45" as="geometry"/>
        </mxCell>
        <mxCell id="r1_c3" value="&lt;span style=&quot;color:#16A34A; font-weight:700;&quot;&gt;Parallel on-demand invocation;&lt;/span&gt; sub-150ms cold start, sub-25ms warm execution" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;fontSize=11.5;" vertex="1" parent="1">
          <mxGeometry x="780" y="875" width="470" height="45" as="geometry"/>
        </mxCell>
        <mxCell id="r1_c4" value="Eliminates client timeouts; empowers instantaneous device whitelist verification in production apps" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;fontSize=11.5;color:#334155;" vertex="1" parent="1">
          <mxGeometry x="1270" y="875" width="520" height="45" as="geometry"/>
        </mxCell>

        <!-- ROW 2: SECURITY & SECRETS -->
        <mxCell id="r2_c1" value="&lt;b style=&quot;color:#0F172A;&quot;&gt;Security &amp;amp; Secrets&lt;/b&gt;" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;spacingLeft=16;fontSize=11.5;" vertex="1" parent="1">
          <mxGeometry x="40" y="925" width="260" height="45" as="geometry"/>
        </mxCell>
        <mxCell id="r2_c2" value="&lt;span style=&quot;color:#DC2626; font-weight:700;&quot;&gt;Plaintext tokens &amp;amp; DB credentials&lt;/span&gt; embedded in CDSW project script repository" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;fontSize=11.5;" vertex="1" parent="1">
          <mxGeometry x="310" y="925" width="450" height="45" as="geometry"/>
        </mxCell>
        <mxCell id="r2_c3" value="&lt;span style=&quot;color:#16A34A; font-weight:700;&quot;&gt;AWS Secrets Manager &amp;amp; KMS&lt;/span&gt; with automated key rotation and IAM-based policy isolation" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;fontSize=11.5;" vertex="1" parent="1">
          <mxGeometry x="780" y="925" width="470" height="45" as="geometry"/>
        </mxCell>
        <mxCell id="r2_c4" value="Remediates major audit vulnerability; brings architecture into strict compliance with SOC2 &amp;amp; ISO 27001" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;fontSize=11.5;color:#334155;" vertex="1" parent="1">
          <mxGeometry x="1270" y="925" width="520" height="45" as="geometry"/>
        </mxCell>

        <!-- ROW 3: RESILIENCE & BLAST RADIUS -->
        <mxCell id="r3_c1" value="&lt;b style=&quot;color:#0F172A;&quot;&gt;Resilience &amp;amp; Blast Radius&lt;/b&gt;" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;spacingLeft=16;fontSize=11.5;" vertex="1" parent="1">
          <mxGeometry x="40" y="975" width="260" height="45" as="geometry"/>
        </mxCell>
        <mxCell id="r3_c2" value="&lt;span style=&quot;color:#DC2626; font-weight:700;&quot;&gt;Monolithic single point of failure;&lt;/span&gt; crashed task aborts entire batch and requires human intervention" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;fontSize=11.5;" vertex="1" parent="1">
          <mxGeometry x="310" y="975" width="450" height="45" as="geometry"/>
        </mxCell>
        <mxCell id="r3_c3" value="&lt;span style=&quot;color:#16A34A; font-weight:700;&quot;&gt;Per-request micro-isolation;&lt;/span&gt; API Gateway throttles bursts while Dead Letter Queues (DLQ) handle retries" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;fontSize=11.5;" vertex="1" parent="1">
          <mxGeometry x="780" y="975" width="470" height="45" as="geometry"/>
        </mxCell>
        <mxCell id="r3_c4" value="Guarantees 99.99% operational SLA; prevents cascading failures across client applications" style="text;html=1;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;fontSize=11.5;color:#334155;" vertex="1" parent="1">
          <mxGeometry x="1270" y="975" width="520" height="45" as="geometry"/>
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""
    return xml.strip()

def create_high_fidelity_svg():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1840 1060" width="1840" height="1060">
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
    <marker id="arrow-purple" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#7C3AED"/>
    </marker>
    <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#10B981"/>
    </marker>
    <marker id="arrow-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#EF4444"/>
    </marker>
  </defs>

  <!-- Clean Canvas Background -->
  <rect width="1840" height="1060" fill="#FFFFFF"/>
  <rect width="1840" height="1060" fill="#F8FAFC" opacity="0.45"/>

  <!-- Subtle Blueprint Grid Pattern -->
  <g stroke="#E2E8F0" stroke-width="0.75" opacity="0.6">
    <path d="M 0 60 L 1840 60 M 0 120 L 1840 120 M 0 180 L 1840 180 M 0 240 L 1840 240 M 0 300 L 1840 300 M 0 360 L 1840 360 M 0 420 L 1840 420 M 0 480 L 1840 480 M 0 540 L 1840 540 M 0 600 L 1840 600 M 0 660 L 1840 660 M 0 720 L 1840 720 M 0 780 L 1840 780 M 0 840 L 1840 840 M 0 900 L 1840 900 M 0 960 L 1840 960 M 0 1020 L 1840 1020" />
    <path d="M 60 0 L 60 1060 M 120 0 L 120 1060 M 180 0 L 180 1060 M 240 0 L 240 1060 M 300 0 L 300 1060 M 360 0 L 360 1060 M 420 0 L 420 1060 M 480 0 L 480 1060 M 540 0 L 540 1060 M 600 0 L 600 1060 M 660 0 L 660 1060 M 720 0 L 720 1060 M 780 0 L 780 1060 M 840 0 L 840 1060 M 900 0 L 900 1060 M 960 0 L 960 1060 M 1020 0 L 1020 1060 M 1080 0 L 1080 1060 M 1140 0 L 1140 1060 M 1200 0 L 1200 1060 M 1260 0 L 1260 1060 M 1320 0 L 1320 1060 M 1380 0 L 1380 1060 M 1440 0 L 1440 1060 M 1500 0 L 1500 1060 M 1560 0 L 1560 1060 M 1620 0 L 1620 1060 M 1680 0 L 1680 1060 M 1740 0 L 1740 1060 M 1800 0 L 1800 1060" />
  </g>

  <!-- ================= TOP HEADER ================= -->
  <rect x="40" y="28" width="4.5" height="34" fill="#E11D48" rx="1"/>
  <rect x="46" y="28" width="9" height="34" fill="#0284C7" rx="1"/>
  <text x="66" y="44" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="22" font-weight="800" fill="#0F172A">Device Whitelisting System: Architecture Evolution (Before vs. After)</text>
  <text x="66" y="63" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="12" font-weight="500" fill="#64748B">Monolithic Cloudera CDSW Batch Execution vs. Proposed Decoupled AWS Lambda Serverless Topology</text>

  <!-- Header Status Pill -->
  <g transform="translate(1550, 26)">
    <rect width="250" height="34" rx="6" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
    <text x="125" y="22" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="800" fill="#1D4ED8" text-anchor="middle" letter-spacing="0.5">🔄 MODERNIZATION SPEC &amp; COMPARISON</text>
  </g>

  <!-- ================= TOP KPI DELTA RIBBON ================= -->
  <g transform="translate(40, 80)">
    <rect width="1760" height="48" rx="8" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="1.5"/>
    
    <!-- Chip 1 -->
    <text x="30" y="30" font-family="Helvetica, Arial, sans-serif" font-size="11.5">
      <tspan font-weight="800" fill="#64748B" font-size="10">EXECUTION MODEL: </tspan>
      <tspan font-weight="800" fill="#DC2626">Sequential Batch </tspan>
      <tspan fill="#64748B">➔ </tspan>
      <tspan font-weight="800" fill="#16A34A">Event-Driven Serverless</tspan>
    </text>

    <!-- Chip 2 -->
    <text x="470" y="30" font-family="Helvetica, Arial, sans-serif" font-size="11.5">
      <tspan font-weight="800" fill="#64748B" font-size="10">INGRESS GATEWAY: </tspan>
      <tspan font-weight="800" fill="#DC2626">Direct Binary EXE </tspan>
      <tspan fill="#64748B">➔ </tspan>
      <tspan font-weight="800" fill="#16A34A">Managed HTTPS REST API</tspan>
    </text>

    <!-- Chip 3 -->
    <text x="910" y="30" font-family="Helvetica, Arial, sans-serif" font-size="11.5">
      <tspan font-weight="800" fill="#64748B" font-size="10">CREDENTIAL SECURITY: </tspan>
      <tspan font-weight="800" fill="#DC2626">Script Environment </tspan>
      <tspan fill="#64748B">➔ </tspan>
      <tspan font-weight="800" fill="#16A34A">AWS Secrets Mgr &amp; KMS</tspan>
    </text>

    <!-- Chip 4 -->
    <text x="1350" y="30" font-family="Helvetica, Arial, sans-serif" font-size="11.5">
      <tspan font-weight="800" fill="#64748B" font-size="10">DATA PERSISTENCE: </tspan>
      <tspan font-weight="800" fill="#DC2626">Shared Cluster Store </tspan>
      <tspan fill="#64748B">➔ </tspan>
      <tspan font-weight="800" fill="#16A34A">Databricks Lakehouse (DBX)</tspan>
    </text>
  </g>


  <!-- ================= LEFT PANEL: CURRENT STATE (BEFORE) ================= -->
  <g transform="translate(40, 142)">
    <!-- Container -->
    <rect width="860" height="678" rx="16" fill="#FFFDFB" stroke="#FCA5A5" stroke-width="2"/>
    
    <!-- Header Bar -->
    <path d="M 0 16 A 16 16 0 0 1 16 0 L 844 0 A 16 16 0 0 1 860 16 L 860 52 L 0 52 Z" fill="#FEF2F2" stroke="#FECACA" stroke-width="1"/>
    <rect x="18" y="14" width="4" height="24" rx="1" fill="#DC2626"/>
    <text x="32" y="31" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="16" font-weight="800" fill="#991B1B">BEFORE: Current Legacy CDSW Job Execution</text>
    <text x="32" y="45" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600" fill="#B45309">Monolithic Synchronous Batch Processing &amp; Bottleneck Lifecycle</text>

    <!-- Badges -->
    <g transform="translate(640, 15)">
      <rect width="94" height="22" rx="4" fill="#FEE2E2" stroke="#FECACA" stroke-width="1"/>
      <text x="47" y="15" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#DC2626" text-anchor="middle">⚠️ HIGH DEBT</text>
      
      <rect x="102" width="102" height="22" rx="4" fill="#FEF3C7" stroke="#FDE68A" stroke-width="1"/>
      <text x="153" y="15" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#B45309" text-anchor="middle">SYNCHRONOUS</text>
    </g>

    <!-- ZONE 1: CLIENT APPS (LEFT SIDE) -->
    <g transform="translate(25, 73)">
      <rect width="230" height="350" rx="20" fill="#F8FAFC" stroke="#94A3B8" stroke-width="2" stroke-dasharray="8,6" opacity="0.95"/>
      <text x="115" y="24" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#64748B" text-anchor="middle" letter-spacing="0.5">CLIENT APPLICATIONS</text>

      <!-- App 1 / Device 1 -->
      <g transform="translate(60, 35)" filter="url(#card-shadow)">
        <rect width="110" height="82" rx="10" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
        <text x="55" y="22" font-family="Helvetica, Arial, sans-serif" font-size="14" font-weight="800" fill="#1E3A8A" text-anchor="middle">app1</text>
        <g transform="translate(43, 29) scale(1.0)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect width="20" height="14" x="2" y="3" rx="2"/>
          <path d="M8 21h8m-4-4v4"/>
        </g>
        <text x="55" y="70" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="600" fill="#64748B" text-anchor="middle">Device 1</text>
      </g>

      <!-- App 2 / Device 2 -->
      <g transform="translate(15, 160)" filter="url(#card-shadow)">
        <rect width="95" height="80" rx="10" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
        <text x="47.5" y="22" font-family="Helvetica, Arial, sans-serif" font-size="13" font-weight="800" fill="#1E3A8A" text-anchor="middle">app2</text>
        <g transform="translate(35.5, 28) scale(1.0)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect width="20" height="14" x="2" y="3" rx="2"/>
          <path d="M8 21h8m-4-4v4"/>
        </g>
        <text x="47.5" y="68" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="600" fill="#64748B" text-anchor="middle">Device 2</text>
      </g>

      <!-- App 3 / Device 3 -->
      <g transform="translate(120, 160)" filter="url(#card-shadow)">
        <rect width="95" height="80" rx="10" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
        <text x="47.5" y="22" font-family="Helvetica, Arial, sans-serif" font-size="13" font-weight="800" fill="#1E3A8A" text-anchor="middle">app3</text>
        <g transform="translate(35.5, 28) scale(1.0)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect width="20" height="14" x="2" y="3" rx="2"/>
          <path d="M8 21h8m-4-4v4"/>
        </g>
        <text x="47.5" y="68" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="600" fill="#64748B" text-anchor="middle">Device 3</text>
      </g>
    </g>

    <!-- ZONE 2: BACKEND BOUNDARY (RIGHT SIDE) -->
    <g transform="translate(280, 73)">
      <rect width="555" height="350" rx="16" fill="#FFFBEB" fill-opacity="0.3" stroke="#F59E0B" stroke-width="2" stroke-dasharray="8,6"/>
      <text x="18" y="25" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#B45309">Backend Execution Boundary</text>
      
      <!-- Cloudera CDSW Badge -->
      <g transform="translate(420, 12)">
        <rect width="120" height="22" rx="4" fill="#FEF3C7" stroke="#FDE68A" stroke-width="1"/>
        <text x="60" y="15" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#B45309" text-anchor="middle" letter-spacing="0.5">CLOUDERA CDSW</text>
      </g>

      <!-- CDSW JOB CARD -->
      <g transform="translate(25, 80)" filter="url(#shadow)">
        <rect width="155" height="120" rx="12" fill="#FFFFFF" stroke="#0284C7" stroke-width="2.2"/>
        <g transform="translate(63.5, 14) scale(0.1892)">
          <path d="{CML_PATH_D}" fill="#4CCF4C" fill-rule="evenodd"/>
        </g>
        <text x="77.5" y="68" font-family="Helvetica, Arial, sans-serif" font-size="16" font-weight="800" fill="#0F172A" text-anchor="middle">CDSW JOB</text>
        <text x="77.5" y="88" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="600" fill="#475569" text-anchor="middle">Cloudera Data Science</text>
        <text x="77.5" y="103" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="500" fill="#64748B" text-anchor="middle">Workbench Job Runner</text>
      </g>

      <!-- 1 TASK WARNINGS -->
      <g transform="translate(220, 45)">
        <rect width="96" height="20" rx="4" fill="#FEE2E2" stroke="#FECACA" stroke-width="1"/>
        <text x="48" y="14" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="800" fill="#DC2626" text-anchor="middle">⚠️ BOTTLENECK</text>
        <rect x="104" width="106" height="20" rx="4" fill="#FEF3C7" stroke="#FDE68A" stroke-width="1"/>
        <text x="157" y="14" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="800" fill="#B45309" text-anchor="middle">⚠️ SYNCHRONOUS</text>
      </g>

      <!-- 1 TASK STANDALONE RED BOX -->
      <g transform="translate(220, 75)" filter="url(#shadow)">
        <rect width="145" height="65" rx="10" fill="#FFFFFF" stroke="#DC2626" stroke-width="2.5"/>
        <text x="72.5" y="42" font-family="Helvetica, Arial, sans-serif" font-size="20" font-weight="800" fill="#0F172A" text-anchor="middle"><tspan text-decoration="underline">1</tspan> Task</text>
      </g>

      <!-- TASK STEPS BULLET LIST -->
      <g transform="translate(220, 160)" font-family="Helvetica, Arial, sans-serif">
        <circle cx="5" cy="8" r="3" fill="#0F172A"/>
        <text x="16" y="12" font-size="12.5" font-weight="700" fill="#0F172A">Input metadata</text>

        <circle cx="5" cy="30" r="3" fill="#0F172A"/>
        <text x="16" y="34" font-size="12.5" font-weight="700" fill="#0F172A">SQL Query</text>

        <circle cx="5" cy="52" r="3" fill="#0F172A"/>
        <text x="16" y="56" font-size="12.5" font-weight="700" fill="#0F172A">Filter &amp; Search Dev. ADD</text>

        <circle cx="5" cy="74" r="3" fill="#0F172A"/>
        <text x="16" y="78" font-size="12.5" font-weight="700" fill="#0F172A">Logging</text>

        <circle cx="5" cy="96" r="3" fill="#0F172A"/>
        <text x="16" y="100" font-size="12.5" font-weight="700" fill="#0F172A">Return to sender</text>
      </g>

      <!-- Connectors inside Left Diagram -->
      <!-- 1. EXE Call -->
      <path d="M -25 50 C 0 50, 10 90, 25 110" fill="none" stroke="#2563EB" stroke-width="2.2" marker-end="url(#arrow-blue)"/>
      <rect x="-18" y="58" width="68" height="18" rx="3" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
      <text x="16" y="71" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="700" fill="#1D4ED8" text-anchor="middle">1. EXE Call</text>

      <!-- 2. Run -->
      <path d="M 180 107 L 212 107" fill="none" stroke="#0284C7" stroke-width="2.2" marker-end="url(#arrow-cyan)"/>
      <rect x="182" y="94" width="44" height="16" rx="3" fill="#F0F9FF" stroke="#BAE6FD" stroke-width="1"/>
      <text x="204" y="106" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="700" fill="#0369A1" text-anchor="middle">2. Run</text>

      <!-- 3. Return (Looping around right and bottom) -->
      <path d="M 365 107 L 440 107 C 510 107, 510 320, 350 320 L -80 320 C -120 320, -135 290, -135 250" fill="none" stroke="#D97706" stroke-width="2.2" marker-end="url(#arrow-amber)"/>
      <rect x="420" y="311" width="70" height="18" rx="3" fill="#FFFBEB" stroke="#FDE68A" stroke-width="1"/>
      <text x="455" y="323" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="700" fill="#B45309" text-anchor="middle">3. Return</text>
      <rect x="40" y="311" width="80" height="18" rx="3" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
      <text x="80" y="323" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="700" fill="#1D4ED8" text-anchor="middle">4. Response</text>
    </g>

    <!-- CRITICAL ARCHITECTURAL BOTTLENECK & RISKS CARD -->
    <g transform="translate(25, 440)">
      <rect width="810" height="188" rx="10" fill="#FFFFFF" stroke="#FECACA" stroke-width="1.5"/>
      <text x="20" y="28" font-family="Helvetica, Arial, sans-serif" font-size="12.5" font-weight="800" fill="#B91C1C">CRITICAL ARCHITECTURAL BOTTLENECK &amp; RISKS</text>
      
      <!-- Bullet 1 -->
      <circle cx="28" cy="52" r="4" fill="#DC2626"/>
      <text x="42" y="56" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#0F172A">Single-Task Serialized Execution:</text>
      <text x="250" y="56" font-family="Helvetica, Arial, sans-serif" font-size="11.5" fill="#475569">Concurrent device requests queue sequentially behind long-running batch SQL jobs.</text>

      <!-- Bullet 2 -->
      <circle cx="28" cy="80" r="4" fill="#DC2626"/>
      <text x="42" y="84" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#0F172A">Fragile Ingress Mechanism:</text>
      <text x="208" y="84" font-family="Helvetica, Arial, sans-serif" font-size="11.5" fill="#475569">Direct executable calls lack TLS authentication, request throttling, and retry policies.</text>

      <!-- Bullet 3 -->
      <circle cx="28" cy="108" r="4" fill="#DC2626"/>
      <text x="42" y="112" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#0F172A">Plaintext Secret Exposure:</text>
      <text x="200" y="112" font-family="Helvetica, Arial, sans-serif" font-size="11.5" fill="#475569">Database credentials and tokens are embedded directly within CDSW script filesystem.</text>

      <!-- Bullet 4 -->
      <circle cx="28" cy="136" r="4" fill="#DC2626"/>
      <text x="42" y="140" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#0F172A">High Failure Blast Radius:</text>
      <text x="200" y="140" font-family="Helvetica, Arial, sans-serif" font-size="11.5" fill="#475569">A single query error crashes the entire runner process, requiring manual admin intervention.</text>
    </g>
  </g>


  <!-- ================= RIGHT PANEL: TARGET STATE (AFTER) ================= -->
  <g transform="translate(940, 142)">
    <!-- Container -->
    <rect width="860" height="678" rx="16" fill="#F0FDF4" stroke="#86EFAC" stroke-width="2"/>
    
    <!-- Header Bar -->
    <path d="M 0 16 A 16 16 0 0 1 16 0 L 844 0 A 16 16 0 0 1 860 16 L 860 52 L 0 52 Z" fill="#ECFDF5" stroke="#A7F3D0" stroke-width="1"/>
    <rect x="18" y="14" width="4" height="24" rx="1" fill="#16A34A"/>
    <text x="32" y="31" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="16" font-weight="800" fill="#065F46">AFTER: Proposed AWS Lambda Serverless Architecture</text>
    <text x="32" y="45" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600" fill="#059669">Event-Driven Decoupled Services &amp; Sub-Second Lifecycle Dataflow</text>

    <!-- Badges -->
    <g transform="translate(635, 15)">
      <rect width="105" height="22" rx="4" fill="#DCFCE7" stroke="#BBF7D0" stroke-width="1"/>
      <text x="52.5" y="15" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#15803D" text-anchor="middle">✓ SUB-SECOND SLA</text>
      
      <rect x="113" width="98" height="22" rx="4" fill="#EDE9FE" stroke="#DDD6FE" stroke-width="1"/>
      <text x="162" y="15" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#6D28D9" text-anchor="middle">AUTO-SCALING</text>
    </g>

    <!-- ZONE 1: CLIENT APPS (LEFT SIDE) -->
    <g transform="translate(25, 73)">
      <rect width="230" height="350" rx="20" fill="#F8FAFC" stroke="#94A3B8" stroke-width="2" stroke-dasharray="8,6" opacity="0.95"/>
      <text x="115" y="24" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#64748B" text-anchor="middle" letter-spacing="0.5">CLIENT APPLICATIONS</text>

      <!-- App 1 / Device 1 -->
      <g transform="translate(60, 35)" filter="url(#card-shadow)">
        <rect width="110" height="82" rx="10" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
        <text x="55" y="22" font-family="Helvetica, Arial, sans-serif" font-size="14" font-weight="800" fill="#1E3A8A" text-anchor="middle">app1</text>
        <g transform="translate(43, 29) scale(1.0)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect width="20" height="14" x="2" y="3" rx="2"/>
          <path d="M8 21h8m-4-4v4"/>
        </g>
        <text x="55" y="70" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="600" fill="#64748B" text-anchor="middle">Device 1</text>
      </g>

      <!-- App 2 / Device 2 -->
      <g transform="translate(15, 160)" filter="url(#card-shadow)">
        <rect width="95" height="80" rx="10" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
        <text x="47.5" y="22" font-family="Helvetica, Arial, sans-serif" font-size="13" font-weight="800" fill="#1E3A8A" text-anchor="middle">app2</text>
        <g transform="translate(35.5, 28) scale(1.0)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect width="20" height="14" x="2" y="3" rx="2"/>
          <path d="M8 21h8m-4-4v4"/>
        </g>
        <text x="47.5" y="68" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="600" fill="#64748B" text-anchor="middle">Device 2</text>
      </g>

      <!-- App 3 / Device 3 -->
      <g transform="translate(120, 160)" filter="url(#card-shadow)">
        <rect width="95" height="80" rx="10" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
        <text x="47.5" y="22" font-family="Helvetica, Arial, sans-serif" font-size="13" font-weight="800" fill="#1E3A8A" text-anchor="middle">app3</text>
        <g transform="translate(35.5, 28) scale(1.0)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect width="20" height="14" x="2" y="3" rx="2"/>
          <path d="M8 21h8m-4-4v4"/>
        </g>
        <text x="47.5" y="68" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="600" fill="#64748B" text-anchor="middle">Device 3</text>
      </g>
    </g>

    <!-- ZONE 2: UNIFIED API GATEWAY -->
    <g transform="translate(285, 140)" filter="url(#shadow)">
      <rect width="150" height="140" rx="12" fill="#FFFFFF" stroke="#8B5CF6" stroke-width="2.2"/>
      <g transform="translate(35, 12)">
        <rect width="80" height="16" rx="3" fill="#EDE9FE"/>
        <text x="40" y="12" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="800" fill="#6D28D9" text-anchor="middle" letter-spacing="0.5">API GATEWAY</text>
      </g>
      <!-- API Gateway Glyph -->
      <g transform="translate(57, 34) scale(0.55)">
        <rect width="48" height="48" rx="8" fill="#8B5CF6"/>
        <circle cx="24" cy="14" r="4" fill="#FFFFFF"/>
        <circle cx="14" cy="32" r="4" fill="#FFFFFF"/>
        <circle cx="34" cy="32" r="4" fill="#FFFFFF"/>
        <path d="M24 18V26M24 26L16 30M24 26L32 30" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"/>
      </g>
      <text x="75" y="86" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="800" fill="#1E1B4B" text-anchor="middle">API Gateway</text>
      <text x="75" y="103" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="500" fill="#6B7280" text-anchor="middle">HTTP / REST Endpoints</text>
      <text x="75" y="119" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="600" fill="#7C3AED" text-anchor="middle">Request &amp; Response Delivery</text>
    </g>

    <!-- ZONE 3: AWS CLOUD BOUNDARY CONTAINER -->
    <g transform="translate(465, 73)">
      <rect width="370" height="245" rx="14" fill="#FFFBEB" fill-opacity="0.3" stroke="#F59E0B" stroke-width="2" stroke-dasharray="8,6"/>
      <text x="16" y="24" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#B45309">AWS Cloud Boundary</text>
      <g transform="translate(270, 215)">
        <rect width="85" height="20" rx="4" fill="#FEF3C7" stroke="#FDE68A" stroke-width="1"/>
        <text x="42.5" y="14" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#B45309" text-anchor="middle" letter-spacing="0.5">AWS CLOUD</text>
      </g>

      <!-- Code Deployed -->
      <g transform="translate(80, 25)" filter="url(#card-shadow)">
        <rect width="75" height="36" rx="6" fill="#FFFFFF" stroke="#10B981" stroke-width="1.6"/>
        <text x="37.5" y="18" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="800" fill="#065F46" text-anchor="middle">Code</text>
        <text x="37.5" y="30" font-family="Helvetica, Arial, sans-serif" font-size="7.5" font-weight="600" fill="#059669" text-anchor="middle">DEPLOYED</text>
      </g>

      <!-- Secret Management -->
      <g transform="translate(180, 20)" filter="url(#card-shadow)">
        <rect width="145" height="55" rx="8" fill="#FFFFFF" stroke="#EF4444" stroke-width="1.8"/>
        <rect x="10" y="9" width="48" height="13" rx="2" fill="#FEE2E2"/>
        <text x="34" y="19" font-family="Helvetica, Arial, sans-serif" font-size="7.5" font-weight="800" fill="#B91C1C" text-anchor="middle">SECURITY</text>
        <text x="80" y="34" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="800" fill="#991B1B" text-anchor="middle">Secret Management</text>
        <text x="80" y="47" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="500" fill="#7F1D1D" text-anchor="middle">KMS / Secrets Mgr</text>
      </g>

      <!-- AWS Lambda Card -->
      <g transform="translate(30, 95)" filter="url(#shadow)">
        <rect width="155" height="100" rx="12" fill="#FFFFFF" stroke="#D97706" stroke-width="2.2"/>
        <g transform="translate(63.5, 12) scale(0.58)">
          <rect width="48" height="48" rx="8" fill="#FF9900"/>
          <path d="M14 36L22.5 18H27L35.5 36H30.5L25 24L18.5 36H14Z" fill="#FFFFFF"/>
          <path d="M21 21.5L16.5 12H12L17.5 23.5L21 21.5Z" fill="#FFFFFF"/>
        </g>
        <text x="77.5" y="66" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="800" fill="#0F172A" text-anchor="middle">AWS Lambda</text>
        <text x="77.5" y="81" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="600" fill="#D97706" text-anchor="middle">(Aws Lamda)</text>
        <text x="77.5" y="94" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="500" fill="#64748B" text-anchor="middle">Serverless Compute</text>
      </g>
    </g>

    <!-- ZONE 4: DBX DATABASE CYLINDER -->
    <g transform="translate(690, 335)" filter="url(#shadow)">
      <path d="M 0 12 L 0 76 A 67 12 0 0 0 135 76 L 135 12 Z" fill="#F0F9FF" stroke="#0284C7" stroke-width="1.8"/>
      <ellipse cx="67.5" cy="12" rx="67.5" ry="12" fill="#E0F2FE" stroke="#0284C7" stroke-width="1.8"/>
      <path d="M 0 76 A 67 12 0 0 0 135 76" fill="none" stroke="#0284C7" stroke-width="1.8"/>
      <!-- Databricks Logo -->
      <g transform="translate(18, 38) scale(1.15)">
        <path d="M13.7194 6.60746L7.25506 10.338L0.332928 6.35214L0 6.53654L0 9.43016L7.25506 13.6004L13.7194 9.88406V11.416L7.25506 15.1465L0.332928 11.1607L0 11.3451L0 11.8415L7.25506 16.0117L14.4962 11.8415V8.94789L14.1633 8.76349L7.25506 12.7351L0.776832 9.01881L0.776832 7.4869L7.25506 11.2032L14.4962 7.033V4.18193L14.1356 3.96917L7.25506 7.92661L1.10976 4.40888L7.25506 0.876967L12.3045 3.78477L12.7484 3.52945V3.17484L7.25506 0.0117187L0 4.18193L0 4.63583L7.25506 8.80605L13.7194 5.07555V6.60746Z" fill="#FF3621"/>
      </g>
      <text x="44" y="45" font-family="Helvetica, Arial, sans-serif" font-size="14" font-weight="800" fill="#0369A1">DBX</text>
      <text x="44" y="59" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="600" fill="#0284C7">Databricks / DB</text>
    </g>

    <!-- Connectors inside Right Diagram -->
    <!-- 1. Request -->
    <path d="M 255 180 C 270 180, 275 190, 285 200" fill="none" stroke="#2563EB" stroke-width="2.2" marker-end="url(#arrow-blue)"/>
    <rect x="228" y="165" width="58" height="16" rx="3" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
    <text x="257" y="177" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="700" fill="#1D4ED8" text-anchor="middle">1. Request</text>

    <!-- 2. Invoke -->
    <path d="M 435 205 L 492 205" fill="none" stroke="#7C3AED" stroke-width="2.2" marker-end="url(#arrow-purple)"/>
    <rect x="444" y="190" width="48" height="16" rx="3" fill="#F5F3FF" stroke="#DDD6FE" stroke-width="1"/>
    <text x="468" y="202" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="700" fill="#6D28D9" text-anchor="middle">2. Invoke</text>

    <!-- Code -> Lambda -->
    <path d="M 582 135 L 582 165" fill="none" stroke="#10B981" stroke-width="2" marker-end="url(#arrow-green)"/>

    <!-- Secrets -> Lambda -->
    <path d="M 645 130 L 630 165" fill="none" stroke="#EF4444" stroke-width="1.8" stroke-dasharray="4,3" marker-end="url(#arrow-red)"/>
    <rect x="625" y="130" width="46" height="14" rx="2" fill="#FEF2F2" stroke="#FECACA" stroke-width="1"/>
    <text x="648" y="141" font-family="Helvetica, Arial, sans-serif" font-size="7.5" font-weight="700" fill="#DC2626" text-anchor="middle">Secrets</text>

    <!-- Lambda -> DBX (SQL Query) -->
    <path d="M 650 250 L 695 340" fill="none" stroke="#0284C7" stroke-width="2" marker-end="url(#arrow-cyan)"/>
    <!-- DBX -> Lambda (Read Results) -->
    <path d="M 690 360 L 640 260" fill="none" stroke="#0284C7" stroke-width="2" marker-end="url(#arrow-cyan)"/>
    <rect x="640" y="285" width="62" height="16" rx="3" fill="#F0F9FF" stroke="#BAE6FD" stroke-width="1"/>
    <text x="671" y="297" font-family="Helvetica, Arial, sans-serif" font-size="8" font-weight="700" fill="#0369A1" text-anchor="middle">SQL Query</text>

    <!-- 5. Deliver -->
    <path d="M 495 245 L 438 245" fill="none" stroke="#7C3AED" stroke-width="2.2" marker-end="url(#arrow-purple)"/>
    <rect x="444" y="250" width="48" height="16" rx="3" fill="#F5F3FF" stroke="#DDD6FE" stroke-width="1"/>
    <text x="468" y="262" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="700" fill="#6D28D9" text-anchor="middle">5. Deliver</text>

    <!-- 6. Response -->
    <path d="M 285 240 C 275 250, 270 260, 255 260" fill="none" stroke="#2563EB" stroke-width="2.2" marker-end="url(#arrow-blue)"/>
    <rect x="228" y="265" width="64" height="16" rx="3" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
    <text x="260" y="277" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="700" fill="#1D4ED8" text-anchor="middle">6. Response</text>

    <!-- TARGET ARCHITECTURE ADVANTAGES & PRODUCTION BENEFITS CARD -->
    <g transform="translate(25, 440)">
      <rect width="810" height="188" rx="10" fill="#FFFFFF" stroke="#A7F3D0" stroke-width="1.5"/>
      <text x="20" y="28" font-family="Helvetica, Arial, sans-serif" font-size="12.5" font-weight="800" fill="#065F46">TARGET ARCHITECTURE ADVANTAGES &amp; VALUE REALIZATION</text>
      
      <!-- Bullet 1 -->
      <circle cx="28" cy="52" r="4" fill="#16A34A"/>
      <text x="42" y="56" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#0F172A">Elastic Sub-Second Concurrency:</text>
      <text x="245" y="56" font-family="Helvetica, Arial, sans-serif" font-size="11.5" fill="#475569">On-demand Lambda instances scale from 0 to 1,000+ automatically with zero idle cluster cost.</text>

      <!-- Bullet 2 -->
      <circle cx="28" cy="80" r="4" fill="#16A34A"/>
      <text x="42" y="84" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#0F172A">Standardized Ingress &amp; Auth:</text>
      <text x="228" y="84" font-family="Helvetica, Arial, sans-serif" font-size="11.5" fill="#475569">Unified API Gateway enforces TLS termination, API key rate limits, and IAM authentication.</text>

      <!-- Bullet 3 -->
      <circle cx="28" cy="108" r="4" fill="#16A34A"/>
      <text x="42" y="112" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#0F172A">Zero-Trust Credential Security:</text>
      <text x="238" y="112" font-family="Helvetica, Arial, sans-serif" font-size="11.5" fill="#475569">KMS-encrypted database credentials dynamically injected via IAM roles from Secrets Manager.</text>

      <!-- Bullet 4 -->
      <circle cx="28" cy="136" r="4" fill="#16A34A"/>
      <text x="42" y="140" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="700" fill="#0F172A">Decoupled ACID Lakehouse:</text>
      <text x="220" y="140" font-family="Helvetica, Arial, sans-serif" font-size="11.5" fill="#475569">Databricks (DBX) provides high-concurrency elastic SQL queries without table lockouts.</text>
    </g>
  </g>


  <!-- ================= BOTTOM ZONE: ARCHITECTURAL DELTA MATRIX ================= -->
  <g transform="translate(40, 835)">
    <!-- Matrix Container -->
    <rect width="1760" height="195" rx="14" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>

    <!-- Table Header Bar -->
    <path d="M 0 14 A 14 14 0 0 1 14 0 L 1746 0 A 14 14 0 0 1 1760 14 L 1760 36 L 0 36 Z" fill="#F1F5F9" stroke="#E2E8F0" stroke-width="1"/>
    <text x="20" y="23" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="800" fill="#475569" letter-spacing="0.5">DIMENSION / CRITERIA</text>
    <text x="280" y="23" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="800" fill="#DC2626" letter-spacing="0.5">CURRENT STATE (LEGACY CDSW)</text>
    <text x="750" y="23" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="800" fill="#16A34A" letter-spacing="0.5">PROPOSED TARGET (AWS LAMBDA)</text>
    <text x="1240" y="23" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="800" fill="#2563EB" letter-spacing="0.5">STRATEGIC BUSINESS IMPACT</text>

    <!-- Dividing Grid Lines -->
    <line x1="0" y1="88" x2="1760" y2="88" stroke="#F1F5F9" stroke-width="1.5"/>
    <line x1="0" y1="140" x2="1760" y2="140" stroke="#F1F5F9" stroke-width="1.5"/>
    
    <line x1="260" y1="0" x2="260" y2="195" stroke="#E2E8F0" stroke-width="1"/>
    <line x1="730" y1="0" x2="730" y2="195" stroke="#E2E8F0" stroke-width="1"/>
    <line x1="1220" y1="0" x2="1220" y2="195" stroke="#E2E8F0" stroke-width="1"/>

    <!-- ROW 1: Throughput & Latency -->
    <text x="20" y="65" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="800" fill="#0F172A">Throughput &amp; Latency</text>
    <text x="280" y="65" font-family="Helvetica, Arial, sans-serif" font-size="11.5">
      <tspan fill="#DC2626" font-weight="700">Serialized 1-task queue;</tspan>
      <tspan fill="#475569"> high job spin-up latency (&gt;30-60s per batch); risk of thread starvation</tspan>
    </text>
    <text x="750" y="65" font-family="Helvetica, Arial, sans-serif" font-size="11.5">
      <tspan fill="#16A34A" font-weight="700">Parallel on-demand invocation;</tspan>
      <tspan fill="#475569"> sub-150ms cold start, sub-25ms warm execution</tspan>
    </text>
    <text x="1240" y="65" font-family="Helvetica, Arial, sans-serif" font-size="11.5" fill="#334155">
      Eliminates client timeouts; empowers instantaneous device whitelist verification in production apps
    </text>

    <!-- ROW 2: Security & Secrets -->
    <text x="20" y="117" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="800" fill="#0F172A">Security &amp; Secrets</text>
    <text x="280" y="117" font-family="Helvetica, Arial, sans-serif" font-size="11.5">
      <tspan fill="#DC2626" font-weight="700">Plaintext tokens &amp; DB credentials</tspan>
      <tspan fill="#475569"> embedded in CDSW project script repository</tspan>
    </text>
    <text x="750" y="117" font-family="Helvetica, Arial, sans-serif" font-size="11.5">
      <tspan fill="#16A34A" font-weight="700">AWS Secrets Manager &amp; KMS</tspan>
      <tspan fill="#475569"> with automated key rotation and IAM-based policy isolation</tspan>
    </text>
    <text x="1240" y="117" font-family="Helvetica, Arial, sans-serif" font-size="11.5" fill="#334155">
      Remediates major audit vulnerability; brings architecture into strict compliance with SOC2 &amp; ISO 27001
    </text>

    <!-- ROW 3: Resilience & Blast Radius -->
    <text x="20" y="170" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="800" fill="#0F172A">Resilience &amp; Blast Radius</text>
    <text x="280" y="170" font-family="Helvetica, Arial, sans-serif" font-size="11.5">
      <tspan fill="#DC2626" font-weight="700">Monolithic single point of failure;</tspan>
      <tspan fill="#475569"> crashed task aborts entire batch and requires human intervention</tspan>
    </text>
    <text x="750" y="170" font-family="Helvetica, Arial, sans-serif" font-size="11.5">
      <tspan fill="#16A34A" font-weight="700">Per-request micro-isolation;</tspan>
      <tspan fill="#475569"> API Gateway throttles bursts while Dead Letter Queues handle retries</tspan>
    </text>
    <text x="1240" y="170" font-family="Helvetica, Arial, sans-serif" font-size="11.5" fill="#334155">
      Guarantees 99.99% operational SLA; prevents cascading failures across client applications
    </text>
  </g>

</svg>
"""
    return svg.replace("{CML_PATH_D}", cml_path_d)

def main():
    # Target file paths
    drawio_path = Path("output/diagrams/whitelist_system_before_after_comparison.drawio")
    svg_path = Path("output/diagrams/whitelist_system_before_after_comparison.svg")
    png_path = Path("output/diagrams/whitelist_system_before_after_comparison.png")
    drawio_svg_path = Path("output/diagrams/whitelist_system_before_after_comparison.drawio.svg")

    temp_drawio = Path("TEMP/whitelist_system_before_after_comparison.drawio")
    temp_svg = Path("TEMP/whitelist_system_before_after_comparison.svg")
    temp_png = Path("TEMP/whitelist_system_before_after_comparison.png")
    temp_drawio_svg = Path("TEMP/whitelist_system_before_after_comparison.drawio.svg")

    artifact_dir = Path("/Users/marcelljw/.gemini/antigravity/brain/d95a63dd-7a66-4b47-b53e-86ce3990d3c0")
    artifact_png_path = artifact_dir / "whitelist_system_before_after_comparison.png"

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
    res = subprocess.run(["rsvg-convert", "-z", "2.5", str(svg_path), "-o", str(png_path)], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"✓ Exported High-Resolution PNG to: {png_path} using rsvg-convert")
        shutil.copy2(png_path, temp_png)
    else:
        print(f"rsvg-convert failed: {res.stderr}")
        try:
            from src.ppt_engine.diagram_engine import _setup_cairo_library
            _setup_cairo_library()
            import cairosvg
            cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), write_to=str(png_path), scale=2.5)
            shutil.copy2(png_path, temp_png)
            print(f"✓ Exported High-Resolution PNG via cairosvg")
        except Exception as e:
            print(f"cairosvg fallback failed: {e}")

    # 4. Copy PNG to artifact directory for markdown embedding
    shutil.copy2(png_path, artifact_png_path)
    print(f"✓ Copied PNG to artifact directory: {artifact_png_path}")

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

    # 6. Update master project TEMP/device_whitelist_system.drawio with new page
    master_drawio = Path("TEMP/device_whitelist_system.drawio")
    if master_drawio.exists():
        master_tree = ET.parse(master_drawio)
        master_root = master_tree.getroot()
        for diag in list(master_root.findall("diagram")):
            if diag.attrib.get("id") == "before_after_comparison" or "Comparison" in diag.attrib.get("name", ""):
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

    html_file = Path("TEMP/open_before_after_in_browser.html")
    html_file.write_text(f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url='{new_url}'" />
    <title>Opening Before vs After Comparison in Draw.io...</title>
</head>
<body>
    <p>Opening Before vs After Architecture Comparison in Diagrams.net / Draw.io... If not redirected, <a href="{new_url}">click here</a>.</p>
</body>
</html>""", encoding="utf-8")
    print(f"✓ Updated browser launcher: {html_file}")

if __name__ == "__main__":
    main()
