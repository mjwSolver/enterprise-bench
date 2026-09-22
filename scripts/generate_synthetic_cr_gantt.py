"""
Synthetic Gantt Schedule Graphic Generator
=========================================
Generates a 100% synthetic, leak-free mock project schedule image for Change Request
attachments, replacing any legacy real client screenshots.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np


def generate_synthetic_gantt(output_path: str = "assets/synthetic_cr_gantt.png") -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6.2), dpi=150)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    # Hide standard axes
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    # Top Banner: Illustrative Simulation Header
    banner = patches.Rectangle((0, 93), 100, 7, facecolor="#0F172A", edgecolor="none")
    ax.add_patch(banner)
    ax.text(2, 96.5, "CR-07: WORKSTREAM SCHEDULE SIMULATION", color="#F8FAFC", fontsize=11, fontweight="bold", va="center")
    ax.text(98, 96.5, "[ILLUSTRATIVE SIMULATION — SYNTHETIC SCHEDULE]", color="#38BDF8", fontsize=9, fontweight="bold", ha="right", va="center")

    # Table Header Row
    th = patches.Rectangle((0, 85), 100, 7, facecolor="#F1F5F9", edgecolor="#CBD5E1", linewidth=1)
    ax.add_patch(th)
    ax.text(2, 88.5, "WBS", color="#334155", fontsize=9.5, fontweight="bold", va="center")
    ax.text(10, 88.5, "Task Description", color="#334155", fontsize=9.5, fontweight="bold", va="center")
    ax.text(38, 88.5, "Dur.", color="#334155", fontsize=9.5, fontweight="bold", va="center")
    ax.text(44, 88.5, "Start", color="#334155", fontsize=9.5, fontweight="bold", va="center")
    ax.text(52, 88.5, "Finish", color="#334155", fontsize=9.5, fontweight="bold", va="center")

    # Gantt Timeline Header
    timeline_header = patches.Rectangle((60, 85), 40, 7, facecolor="#E2E8F0", edgecolor="#CBD5E1", linewidth=1)
    ax.add_patch(timeline_header)
    weeks = [("Week 1 (Jun 22)", 60, 13.3), ("Week 2 (Jun 29)", 73.3, 13.3), ("Week 3 (Jul 06)", 86.6, 13.4)]
    for w_name, wx, ww in weeks:
        ax.text(wx + ww / 2, 88.5, w_name, color="#1E293B", fontsize=8.5, fontweight="bold", ha="center", va="center")
        ax.plot([wx, wx], [0, 92], color="#E2E8F0", linestyle="--", linewidth=0.8, zorder=1)

    # Rows Data
    rows = [
        {"wbs": "1.0", "name": "CR-07 Ingestion Pipeline Optimization", "dur": "15d", "start": "22/06", "end": "10/07", "is_summary": True, "gx": 60, "gw": 39, "color": "#0F172A"},
        {"wbs": "1.1", "name": "  Joint Technical Assessment & Scoping", "dur": "2d", "start": "22/06", "end": "23/06", "is_summary": False, "gx": 60, "gw": 5.2, "color": "#0284C7"},
        {"wbs": "1.2", "name": "  Architecture & FSD Addendum Drafting", "dur": "3d", "start": "24/06", "end": "26/06", "is_summary": False, "gx": 65.2, "gw": 7.8, "color": "#0284C7"},
        {"wbs": "1.3", "name": "  Snowflake Data Mart Optimization", "dur": "5d", "start": "29/06", "end": "03/07", "is_summary": False, "gx": 73.3, "gw": 13.0, "color": "#2563EB"},
        {"wbs": "1.4", "name": "  Streamlit Financial UI Adaptation", "dur": "4d", "start": "01/07", "end": "06/07", "is_summary": False, "gx": 78.5, "gw": 10.4, "color": "#2563EB"},
        {"wbs": "1.5", "name": "  System Integration Testing (SIT)", "dur": "3d", "start": "06/07", "end": "08/07", "is_summary": False, "gx": 86.6, "gw": 7.8, "color": "#0D9488"},
        {"wbs": "1.6", "name": "  User Acceptance Testing (UAT)", "dur": "2d", "start": "08/07", "end": "09/07", "is_summary": False, "gx": 91.8, "gw": 5.2, "color": "#16A34A"},
        {"wbs": "1.7", "name": "  Production Deployment & Sign-off", "dur": "1d", "start": "10/07", "end": "10/07", "is_summary": False, "gx": 97.0, "gw": 2.5, "color": "#D97706"},
    ]

    y_pos = 76
    row_height = 8.5

    for i, r in enumerate(rows):
        y = y_pos - i * row_height
        bg_col = "#F8FAFC" if i % 2 == 1 else "#FFFFFF"
        if r["is_summary"]:
            bg_col = "#F1F5F9"
        row_rect = patches.Rectangle((0, y - 2), 100, row_height, facecolor=bg_col, edgecolor="#F1F5F9", linewidth=0.5, zorder=0)
        ax.add_patch(row_rect)

        # Text labels
        weight = "bold" if r["is_summary"] else "normal"
        text_col = "#0F172A" if r["is_summary"] else "#334155"
        ax.text(2, y + 2, r["wbs"], color=text_col, fontsize=9, fontweight=weight, va="center")
        ax.text(10, y + 2, r["name"], color=text_col, fontsize=9, fontweight=weight, va="center")
        ax.text(38, y + 2, r["dur"], color=text_col, fontsize=9, va="center")
        ax.text(44, y + 2, r["start"], color=text_col, fontsize=8.5, va="center")
        ax.text(52, y + 2, r["end"], color=text_col, fontsize=8.5, va="center")

        # Gantt Bar
        bar_h = 3.2 if not r["is_summary"] else 4.0
        bar_y = y + 0.4 if not r["is_summary"] else y
        bar = patches.FancyBboxPatch(
            (r["gx"], bar_y),
            r["gw"],
            bar_h,
            boxstyle="round,pad=0.2,rounding_size=0.8",
            facecolor=r["color"],
            edgecolor="none",
            zorder=3,
        )
        ax.add_patch(bar)

    # Bottom Footer Disclaimer
    footer = patches.Rectangle((0, 0), 100, 7, facecolor="#F8FAFC", edgecolor="#E2E8F0", linewidth=1)
    ax.add_patch(footer)
    ax.text(
        2,
        3.5,
        "Confidential  |  Nusantara Global Logistics (NGL)  |  Simulated Execution Schedule for Commercial Change Request CR-07",
        color="#64748B",
        fontsize=8,
        va="center",
    )
    ax.text(98, 3.5, "Status: Approved Simulation", color="#059669", fontsize=8, fontweight="bold", ha="right", va="center")

    plt.tight_layout(pad=0)
    plt.savefig(str(out), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    return out


if __name__ == "__main__":
    p = generate_synthetic_gantt("clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/synthetic_cr_gantt.png")
    print(f"Generated synthetic Gantt placeholder at {p}")
