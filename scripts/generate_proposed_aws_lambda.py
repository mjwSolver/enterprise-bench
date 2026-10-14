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

# Load SVG logos for base64 data URIs
api_gw_svg_path = Path("assets/logos/aws/aws_api_gateway.svg")
api_gw_data_uri = f"data:image/svg+xml;base64,{base64.b64encode(api_gw_svg_path.read_bytes()).decode('ascii')}" if api_gw_svg_path.exists() else ""

lambda_svg_path = Path("assets/logos/aws/aws_lambda.svg")
lambda_data_uri = f"data:image/svg+xml;base64,{base64.b64encode(lambda_svg_path.read_bytes()).decode('ascii')}" if lambda_svg_path.exists() else ""

dbx_svg_path = Path("assets/logos/databricks/databricks.svg")
dbx_data_uri = f"data:image/svg+xml;base64,{base64.b64encode(dbx_svg_path.read_bytes()).decode('ascii')}" if dbx_svg_path.exists() else ""

def create_drawio_xml():
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="Electron" agent="Enterprise Bench Diagram Engine" version="21.0.0" type="device">
  <diagram id="proposed_aws_lambda" name="Proposed AWS Lambda">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="720" background="#FFFFFF" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- TITLE / HEADER -->
        <mxCell id="header_title" value="&lt;b style=&quot;font-size:24px; color:#0F172A; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;&quot;&gt;Proposed: AWS Lambda&lt;/b&gt;&lt;br/&gt;&lt;span style=&quot;font-size:13px; color:#64748B;&quot;&gt;Serverless Architecture &amp;amp; Execution Lifecycle Dataflow&lt;/span&gt;" style="text;html=1;align=left;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="50" y="30" width="340" height="50" as="geometry"/>
        </mxCell>

        <!-- ZONE 1: CLIENT APPS CLUSTER CONTAINER -->
        <mxCell id="group_apps" value="Client Applications" style="rounded=1;arcSize=18;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#94A3B8;strokeWidth=2;fillColor=#F8FAFC;fillOpacity=50;fontFamily=Helvetica, Arial, sans-serif;fontColor=#475569;fontSize=13;fontStyle=2;align=center;verticalAlign=top;spacingTop=14;" vertex="1" parent="1">
          <mxGeometry x="60" y="130" width="310" height="390" as="geometry"/>
        </mxCell>

        <!-- APP 1 (TOP) -->
        <mxCell id="node_app1" value="&lt;div style=&quot;font-weight:700; font-size:15px; color:#1E3A8A; margin-bottom:4px;&quot;&gt;app1&lt;/div&gt;&lt;div style=&quot;font-size:22px;&quot;&gt;🖥️&lt;/div&gt;&lt;div style=&quot;font-size:11px; color:#64748B; margin-top:2px;&quot;&gt;Device 1&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="150" y="175" width="130" height="95" as="geometry"/>
        </mxCell>

        <!-- APP 2 (BOTTOM LEFT) -->
        <mxCell id="node_app2" value="&lt;div style=&quot;font-weight:700; font-size:15px; color:#1E3A8A; margin-bottom:4px;&quot;&gt;app2&lt;/div&gt;&lt;div style=&quot;font-size:22px;&quot;&gt;🖥️&lt;/div&gt;&lt;div style=&quot;font-size:11px; color:#64748B; margin-top:2px;&quot;&gt;Device 2&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="85" y="350" width="120" height="95" as="geometry"/>
        </mxCell>

        <!-- APP 3 (BOTTOM RIGHT) -->
        <mxCell id="node_app3" value="&lt;div style=&quot;font-weight:700; font-size:15px; color:#1E3A8A; margin-bottom:4px;&quot;&gt;app3&lt;/div&gt;&lt;div style=&quot;font-size:22px;&quot;&gt;🖥️&lt;/div&gt;&lt;div style=&quot;font-size:11px; color:#64748B; margin-top:2px;&quot;&gt;Device 3&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#3B82F6;strokeWidth=2;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="230" y="350" width="120" height="95" as="geometry"/>
        </mxCell>

        <!-- ZONE 2: SINGLE UNIFIED PURPLE API GATEWAY (INGRESS & EGRESS) -->
        <mxCell id="node_api_gw" value="&lt;div style=&quot;margin-bottom:6px;&quot;&gt;&lt;img src=&quot;{api_gw_data_uri}&quot; width=&quot;28&quot; height=&quot;28&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-size:10px; font-weight:800; color:#7C3AED; text-transform:uppercase; letter-spacing:0.5px; background:#EDE9FE; display:inline-block; padding:2px 8px; border-radius:4px; margin-bottom:4px;&quot;&gt;API GATEWAY&lt;/div&gt;&lt;div style=&quot;font-size:17px; font-weight:800; color:#1E1B4B;&quot;&gt;API Gateway&lt;/div&gt;&lt;div style=&quot;font-size:11px; color:#6B7280; margin-top:3px;&quot;&gt;HTTP / REST Endpoints&lt;/div&gt;&lt;div style=&quot;font-size:10px; font-weight:600; color:#7C3AED; margin-top:2px;&quot;&gt;Request &amp;amp; Response Delivery&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#8B5CF6;strokeWidth=2.2;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="455" y="230" width="200" height="160" as="geometry"/>
        </mxCell>

        <!-- ZONE 3: AWS BOUNDARY CONTAINER (RIGHT) -->
        <mxCell id="group_aws" value="AWS Cloud" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 6;strokeColor=#F59E0B;strokeWidth=2;fillColor=#FFFBEB;fillOpacity=35;fontFamily=Helvetica, Arial, sans-serif;fontColor=#B45309;fontSize=13;fontStyle=1;align=right;verticalAlign=bottom;spacingRight=18;spacingBottom=12;" vertex="1" parent="1">
          <mxGeometry x="700" y="170" width="430" height="265" as="geometry"/>
        </mxCell>

        <!-- AWS LAMBDA -->
        <mxCell id="node_lambda" value="&lt;div style=&quot;margin-bottom:4px;&quot;&gt;&lt;img src=&quot;{lambda_data_uri}&quot; width=&quot;30&quot; height=&quot;30&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;&lt;div style=&quot;font-size:16px; font-weight:700; color:#0F172A;&quot;&gt;AWS Lambda&lt;/div&gt;&lt;div style=&quot;font-size:11.5px; font-weight:600; color:#D97706;&quot;&gt;(Aws Lamda)&lt;/div&gt;&lt;div style=&quot;font-size:10px; color:#64748B;&quot;&gt;Serverless Compute&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#D97706;strokeWidth=2.5;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="735" y="295" width="195" height="118" as="geometry"/>
        </mxCell>

        <!-- CODE COMPONENT (ABOVE LAMBDA) -->
        <mxCell id="node_code" value="&lt;div style=&quot;font-weight:700; font-size:13px; color:#065F46;&quot;&gt;Code&lt;/div&gt;&lt;div style=&quot;font-size:9px; font-weight:600; color:#059669;&quot;&gt;DEPLOYED&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#ECFDF5;strokeColor=#10B981;strokeWidth=1.8;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="830" y="215" width="95" height="42" as="geometry"/>
        </mxCell>

        <!-- SECRET MANAGEMENT (UPPER RIGHT) -->
        <mxCell id="node_secrets" value="&lt;div style=&quot;font-size:9.5px; font-weight:700; color:#DC2626; text-transform:uppercase;&quot;&gt;Security&lt;/div&gt;&lt;div style=&quot;font-size:14px; font-weight:700; color:#991B1B; margin-top:2px;&quot;&gt;Secret Management&lt;/div&gt;&lt;div style=&quot;font-size:10px; color:#7F1D1D;&quot;&gt;KMS / Secrets Manager&lt;/div&gt;" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#EF4444;strokeWidth=2;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="945" y="215" width="165" height="66" as="geometry"/>
        </mxCell>

        <!-- ZONE 4: DBX DATABASE (OUTSIDE AWS CONTAINER, LOWER RIGHT) -->
        <mxCell id="node_dbx" value="&lt;table style=&quot;margin:auto;&quot;&gt;&lt;tr&gt;&lt;td style=&quot;vertical-align:middle; padding-right:10px;&quot;&gt;&lt;img src=&quot;{dbx_data_uri}&quot; width=&quot;21&quot; height=&quot;24&quot;/&gt;&lt;/td&gt;&lt;td style=&quot;text-align:left; vertical-align:middle;&quot;&gt;&lt;div style=&quot;font-size:15.5px; font-weight:800; color:#0369A1; line-height:1.2;&quot;&gt;DBX&lt;/div&gt;&lt;div style=&quot;font-size:11px; font-weight:600; color:#0284C7; line-height:1.2;&quot;&gt;Databricks / DB&lt;/div&gt;&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=14;fillColor=#F0F9FF;strokeColor=#0284C7;strokeWidth=2;shadow=1;fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="960" y="470" width="160" height="92" as="geometry"/>
        </mxCell>

        <!-- CONNECTORS / FLOW ARROWS -->

        <!-- 1. APPS CLUSTER -> UNIFIED API GATEWAY -->
        <mxCell id="edge_apps_to_gw" value="1. Request" style="edgeStyle=curvedEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#2563EB;strokeWidth=2.5;fontColor=#1D4ED8;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;exitX=1;exitY=0.25;entryX=0;entryY=0.25;" edge="1" parent="1" source="group_apps" target="node_api_gw">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="410" y="225"/>
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- 2. UNIFIED API GATEWAY -> AWS LAMBDA (Forward Flow: Left to Right) -->
        <mxCell id="edge_gw_to_lambda" value="2. Invoke" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#7C3AED;strokeWidth=2.5;fontColor=#6D28D9;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;exitX=1;exitY=0.59;entryX=0;entryY=0.25;" edge="1" parent="1" source="node_api_gw" target="node_lambda">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 3. CODE -> AWS LAMBDA (DOWNWARD ARROW) -->
        <mxCell id="edge_code_to_lambda" value="" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#10B981;strokeWidth=2.2;exitX=0.5;exitY=1;entryX=0.7;entryY=0;" edge="1" parent="1" source="node_code" target="node_lambda">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 4. SECRET MANAGEMENT -> AWS LAMBDA -->
        <mxCell id="edge_secrets_to_lambda" value="Secrets" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#EF4444;strokeWidth=2;dashed=1;dashPattern=5 3;fontColor=#DC2626;fontFamily=Helvetica, Arial, sans-serif;fontSize=10;fontStyle=1;exitX=0;exitY=0.75;entryX=1;entryY=0.25;" edge="1" parent="1" source="node_secrets" target="node_lambda">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 5. AWS LAMBDA -> DBX (WRITE / QUERY) -->
        <mxCell id="edge_lambda_to_dbx" value="SQL Query" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#0284C7;strokeWidth=2;fontColor=#0369A1;fontFamily=Helvetica, Arial, sans-serif;fontSize=10;fontStyle=1;exitX=1;exitY=0.8;entryX=0;entryY=0.25;" edge="1" parent="1" source="node_lambda" target="node_dbx">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 6. DBX -> AWS LAMBDA (READ / RESULT) -->
        <mxCell id="edge_dbx_to_lambda" value="" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#0284C7;strokeWidth=2;exitX=0;exitY=0.65;entryX=0.85;entryY=1;" edge="1" parent="1" source="node_dbx" target="node_lambda">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 7. AWS LAMBDA -> UNIFIED API GATEWAY (Return Flow: Right to Left) -->
        <mxCell id="edge_lambda_to_gw" value="5. Deliver" style="edgeStyle=straight;html=1;endArrow=block;endFill=1;strokeColor=#7C3AED;strokeWidth=2.5;fontColor=#6D28D9;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;exitX=0;exitY=0.64;entryX=1;entryY=0.88;" edge="1" parent="1" source="node_lambda" target="node_api_gw">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- 8. UNIFIED API GATEWAY -> APPS CLUSTER -->
        <mxCell id="edge_gw_to_apps" value="6. Response" style="edgeStyle=curvedEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#2563EB;strokeWidth=2.5;fontColor=#1D4ED8;fontFamily=Helvetica, Arial, sans-serif;fontSize=11;fontStyle=1;exitX=0;exitY=0.80;entryX=1;entryY=0.80;" edge="1" parent="1" source="node_api_gw" target="group_apps">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="410" y="390"/>
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
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#EF4444"/>
    </marker>
    <marker id="arrow-cyan" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#0284C7"/>
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
  <text x="76" y="47" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="22" font-weight="800" fill="#0F172A">Proposed: AWS Lambda</text>
  <text x="76" y="65" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="12" font-weight="500" fill="#64748B">Serverless Architecture &amp; Execution Lifecycle Dataflow</text>

  <!-- ================= ZONE 1: CLIENT APPS CONTAINER ================= -->
  <g>
    <!-- Cluster Boundary -->
    <rect x="60" y="130" width="310" height="390" rx="36" fill="#F8FAFC" stroke="#94A3B8" stroke-width="2" stroke-dasharray="8,6" opacity="0.95"/>
    <text x="215" y="156" font-family="Helvetica, Arial, sans-serif" font-size="12" font-weight="700" fill="#64748B" text-anchor="middle" letter-spacing="0.5">CLIENT APPLICATIONS</text>

    <!-- App 1 (Top Center) -->
    <g filter="url(#card-shadow)">
      <rect x="150" y="175" width="130" height="95" rx="12" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
      <text x="215" y="200" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="800" fill="#1E3A8A" text-anchor="middle">app1</text>
      <!-- Lucide Monitor Device Icon (Matching Current Diagram) -->
      <g transform="translate(201, 208) scale(1.15)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect width="20" height="14" x="2" y="3" rx="2"/>
        <path d="M8 21h8m-4-4v4"/>
      </g>
      <text x="215" y="258" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="600" fill="#64748B" text-anchor="middle">Device 1</text>
    </g>

    <!-- App 2 (Bottom Left) -->
    <g filter="url(#card-shadow)">
      <rect x="85" y="350" width="120" height="95" rx="12" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
      <text x="145" y="375" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="800" fill="#1E3A8A" text-anchor="middle">app2</text>
      <!-- Lucide Monitor Device Icon (Matching Current Diagram) -->
      <g transform="translate(131, 383) scale(1.15)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect width="20" height="14" x="2" y="3" rx="2"/>
        <path d="M8 21h8m-4-4v4"/>
      </g>
      <text x="145" y="433" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="600" fill="#64748B" text-anchor="middle">Device 2</text>
    </g>

    <!-- App 3 (Bottom Right) -->
    <g filter="url(#card-shadow)">
      <rect x="230" y="350" width="120" height="95" rx="12" fill="#FFFFFF" stroke="#3B82F6" stroke-width="2"/>
      <text x="290" y="375" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="800" fill="#1E3A8A" text-anchor="middle">app3</text>
      <!-- Lucide Monitor Device Icon (Matching Current Diagram) -->
      <g transform="translate(276, 383) scale(1.15)" stroke="#3B82F6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect width="20" height="14" x="2" y="3" rx="2"/>
        <path d="M8 21h8m-4-4v4"/>
      </g>
      <text x="290" y="433" font-family="Helvetica, Arial, sans-serif" font-size="10.5" font-weight="600" fill="#64748B" text-anchor="middle">Device 3</text>
    </g>
  </g>

  <!-- ================= ZONE 2: SINGLE UNIFIED API GATEWAY (INGRESS & EGRESS) ================= -->
  <g filter="url(#shadow)">
    <rect x="455" y="230" width="200" height="160" rx="14" fill="#FFFFFF" stroke="#8B5CF6" stroke-width="2.2"/>
    
    <!-- API Gateway Pill Badge -->
    <g transform="translate(505, 244)">
      <rect width="100" height="18" rx="4" fill="#EDE9FE"/>
      <text x="50" y="13" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="800" fill="#6D28D9" text-anchor="middle" letter-spacing="0.5">API GATEWAY</text>
    </g>

    <!-- AWS API Gateway Official Glyph -->
    <g transform="translate(539, 268) scale(0.667)">
      <rect width="48" height="48" rx="8" fill="#8B5CF6"/>
      <circle cx="24" cy="14" r="4" fill="#FFFFFF"/>
      <circle cx="14" cy="32" r="4" fill="#FFFFFF"/>
      <circle cx="34" cy="32" r="4" fill="#FFFFFF"/>
      <path d="M24 18V26M24 26L16 30M24 26L32 30" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"/>
    </g>

    <text x="555" y="323" font-family="Helvetica, Arial, sans-serif" font-size="17" font-weight="800" fill="#1E1B4B" text-anchor="middle">API Gateway</text>
    <text x="555" y="343" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="500" fill="#6B7280" text-anchor="middle">HTTP / REST Endpoints</text>
    <text x="555" y="361" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="600" fill="#7C3AED" text-anchor="middle">Request &amp; Response Delivery</text>
  </g>

  <!-- ================= ZONE 3: AWS BOUNDARY CONTAINER (RIGHT) ================= -->
  <g>
    <!-- AWS Cloud Boundary -->
    <rect x="700" y="170" width="430" height="265" rx="16" fill="#FFFBEB" fill-opacity="0.3" stroke="#F59E0B" stroke-width="2" stroke-dasharray="8,6"/>
    <!-- AWS Cloud Badge (Bottom Right of Dotted Square) -->
    <g transform="translate(1015, 398)">
      <rect width="98" height="24" rx="5" fill="#FEF3C7" stroke="#FDE68A" stroke-width="1"/>
      <text x="49" y="16" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="800" fill="#B45309" text-anchor="middle" letter-spacing="0.5">AWS CLOUD</text>
    </g>

    <!-- Code Component (Above Lambda) -->
    <g filter="url(#card-shadow)">
      <rect x="830" y="215" width="95" height="42" rx="8" fill="#FFFFFF" stroke="#10B981" stroke-width="1.8"/>
      <text x="877" y="235" font-family="Helvetica, Arial, sans-serif" font-size="13" font-weight="800" fill="#065F46" text-anchor="middle">Code</text>
      <text x="877" y="248" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="600" fill="#059669" text-anchor="middle">DEPLOYED</text>
    </g>

    <!-- Secret Management Component (Upper Right) -->
    <g filter="url(#card-shadow)">
      <rect x="945" y="215" width="165" height="66" rx="12" fill="#FFFFFF" stroke="#EF4444" stroke-width="2"/>
      <rect x="957" y="226" width="56" height="15" rx="3" fill="#FEE2E2"/>
      <text x="985" y="237" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="800" fill="#B91C1C" text-anchor="middle">SECURITY</text>
      <text x="1027" y="255" font-family="Helvetica, Arial, sans-serif" font-size="13.5" font-weight="800" fill="#991B1B" text-anchor="middle">Secret Management</text>
      <text x="1027" y="271" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="500" fill="#7F1D1D" text-anchor="middle">KMS / Secrets Manager</text>
    </g>

    <!-- AWS Lambda Card (Center / Lower) -->
    <g filter="url(#shadow)">
      <rect x="735" y="295" width="195" height="118" rx="14" fill="#FFFFFF" stroke="#D97706" stroke-width="2.5"/>
      <!-- Official AWS Lambda Logo (Matching Presentation) -->
      <g transform="translate(816, 308) scale(0.667)">
        <rect width="48" height="48" rx="8" fill="#FF9900"/>
        <!-- Greek Lambda Glyph -->
        <path d="M14 36L22.5 18H27L35.5 36H30.5L25 24L18.5 36H14Z" fill="#FFFFFF"/>
        <path d="M21 21.5L16.5 12H12L17.5 23.5L21 21.5Z" fill="#FFFFFF"/>
      </g>
      <text x="832" y="360" font-family="Helvetica, Arial, sans-serif" font-size="16" font-weight="800" fill="#0F172A" text-anchor="middle">AWS Lambda</text>
      <text x="832" y="378" font-family="Helvetica, Arial, sans-serif" font-size="11.5" font-weight="600" fill="#D97706" text-anchor="middle">(Aws Lamda)</text>
      <text x="832" y="394" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="500" fill="#64748B" text-anchor="middle">Serverless Compute</text>
    </g>
  </g>

  <!-- ================= ZONE 4: DBX DATABASE (LOWER RIGHT, OUTSIDE AWS) ================= -->
  <g filter="url(#shadow)">
    <!-- Seamless 3D Cylinder geometry with generous height & balanced aspect ratio -->
    <path d="M 960 472 L 960 568 A 80 15 0 0 0 1120 568 L 1120 472 Z" fill="#F0F9FF" stroke="#0284C7" stroke-width="2"/>
    <ellipse cx="1040" cy="472" rx="80" ry="15" fill="#E0F2FE" stroke="#0284C7" stroke-width="2"/>
    <path d="M 960 568 A 80 15 0 0 0 1120 568" fill="none" stroke="#0284C7" stroke-width="2"/>
    <!-- Official Databricks Logo & Typography Group (Horizontally & Vertically Balanced) -->
    <g transform="translate(982, 517) scale(1.4)">
      <path d="M13.7194 6.60746L7.25506 10.338L0.332928 6.35214L0 6.53654L0 9.43016L7.25506 13.6004L13.7194 9.88406V11.416L7.25506 15.1465L0.332928 11.1607L0 11.3451L0 11.8415L7.25506 16.0117L14.4962 11.8415V8.94789L14.1633 8.76349L7.25506 12.7351L0.776832 9.01881L0.776832 7.4869L7.25506 11.2032L14.4962 7.033V4.18193L14.1356 3.96917L7.25506 7.92661L1.10976 4.40888L7.25506 0.876967L12.3045 3.78477L12.7484 3.52945V3.17484L7.25506 0.0117187L0 4.18193L0 4.63583L7.25506 8.80605L13.7194 5.07555V6.60746Z" fill="#FF3621"/>
    </g>
    <text x="1015" y="525" font-family="Helvetica, Arial, sans-serif" font-size="15.5" font-weight="800" fill="#0369A1" text-anchor="start">DBX</text>
    <text x="1015" y="541" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="600" fill="#0284C7" text-anchor="start">Databricks / DB</text>
  </g>

  <!-- ================= FLOW CONNECTORS / CYCLE ARROWS ================= -->

  <!-- 1. APPS CLUSTER -> UNIFIED API GATEWAY -->
  <path d="M 280 222 C 340 222, 395 245, 447 265" fill="none" stroke="#2563EB" stroke-width="2.5" marker-end="url(#arrow-blue)"/>
  <rect x="376" y="224" width="68" height="18" rx="4" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
  <text x="410" y="237" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="700" fill="#1D4ED8" text-anchor="middle">1. Request</text>

  <!-- 2. UNIFIED API GATEWAY -> AWS LAMBDA -->
  <path d="M 655 325 L 727 325" fill="none" stroke="#7C3AED" stroke-width="2.5" marker-end="url(#arrow-purple)"/>
  <rect x="666" y="304" width="58" height="18" rx="4" fill="#F5F3FF" stroke="#DDD6FE" stroke-width="1"/>
  <text x="695" y="317" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="700" fill="#6D28D9" text-anchor="middle">2. Invoke</text>

  <!-- 3. CODE -> LAMBDA (Straight Downward Injection Arrow directly to Lambda) -->
  <path d="M 877 257 L 877 288" fill="none" stroke="#10B981" stroke-width="2.2" marker-end="url(#arrow-green)"/>

  <!-- 4. SECRET MANAGEMENT -> AWS LAMBDA (Diagonal Credential Flow) -->
  <path d="M 945 265 L 910 298" fill="none" stroke="#EF4444" stroke-width="2" stroke-dasharray="4,3" marker-end="url(#arrow-red)"/>
  <rect x="915" y="260" width="56" height="16" rx="3" fill="#FEF2F2" stroke="#FECACA" stroke-width="1"/>
  <text x="943" y="272" font-family="Helvetica, Arial, sans-serif" font-size="8.5" font-weight="700" fill="#DC2626" text-anchor="middle">Secrets</text>

  <!-- 5. LAMBDA -> DBX (SQL Query Request) -->
  <path d="M 925 413 L 980 475" fill="none" stroke="#0284C7" stroke-width="2.2" marker-end="url(#arrow-cyan)"/>
  <!-- 6. DBX -> LAMBDA (Read / Data Results) -->
  <path d="M 975 498 L 915 422" fill="none" stroke="#0284C7" stroke-width="2.2" marker-end="url(#arrow-cyan)"/>
  <rect x="922" y="438" width="76" height="18" rx="4" fill="#F0F9FF" stroke="#BAE6FD" stroke-width="1"/>
  <text x="960" y="451" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="700" fill="#0369A1" text-anchor="middle">SQL Query</text>

  <!-- 7. AWS LAMBDA -> UNIFIED API GATEWAY -->
  <path d="M 735 365 L 663 365" fill="none" stroke="#7C3AED" stroke-width="2.5" marker-end="url(#arrow-purple)"/>
  <rect x="666" y="372" width="58" height="18" rx="4" fill="#F5F3FF" stroke="#DDD6FE" stroke-width="1"/>
  <text x="695" y="385" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="700" fill="#6D28D9" text-anchor="middle">5. Deliver</text>

  <!-- 8. UNIFIED API GATEWAY -> APPS CLUSTER (Return Flow Back to Clients) -->
  <path d="M 455 355 C 415 365, 380 385, 356 395" fill="none" stroke="#2563EB" stroke-width="2.5" marker-end="url(#arrow-blue)"/>
  <rect x="376" y="370" width="76" height="18" rx="4" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
  <text x="414" y="383" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="700" fill="#1D4ED8" text-anchor="middle">6. Response</text>

</svg>
"""
    return svg

def main():
    drawio_path = Path("output/diagrams/proposed_aws_lambda.drawio")
    svg_path = Path("output/diagrams/proposed_aws_lambda.svg")
    png_path = Path("output/diagrams/proposed_aws_lambda.png")
    drawio_svg_path = Path("output/diagrams/proposed_aws_lambda.drawio.svg")

    temp_drawio = Path("TEMP/proposed_aws_lambda.drawio")
    temp_svg = Path("TEMP/proposed_aws_lambda.svg")
    temp_png = Path("TEMP/proposed_aws_lambda.png")
    temp_drawio_svg = Path("TEMP/proposed_aws_lambda.drawio.svg")

    artifact_dir = Path("/Users/marcelljw/.gemini/antigravity/brain/84c72c90-c57c-4576-9970-a360911a4b3f")
    artifact_png_path = artifact_dir / "proposed_aws_lambda.png"

    drawio_path.parent.mkdir(parents=True, exist_ok=True)
    temp_drawio.parent.mkdir(parents=True, exist_ok=True)

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
        print(f"rsvg-convert failed: {res.stderr}")

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

    # 6. Update master project TEMP/device_whitelist_system.drawio
    master_drawio = Path("TEMP/device_whitelist_system.drawio")
    if master_drawio.exists():
        master_tree = ET.parse(master_drawio)
        master_root = master_tree.getroot()
        for diag in list(master_root.findall("diagram")):
            if diag.attrib.get("id") == "proposed_aws_lambda" or "Proposed" in diag.attrib.get("name", ""):
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

    html_file = Path("TEMP/open_proposed_in_browser.html")
    html_file.write_text(f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url='{new_url}'" />
    <title>Opening Proposed AWS Lambda in Draw.io...</title>
</head>
<body>
    <p>Opening updated diagram in Draw.io... If not redirected, <a href="{new_url}">click here</a>.</p>
</body>
</html>""", encoding="utf-8")
    print(f"✓ Updated browser launcher: {html_file}")

if __name__ == "__main__":
    main()
