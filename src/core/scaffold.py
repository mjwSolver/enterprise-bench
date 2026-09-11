"""
Project Payload Scaffolding Subsystem
=====================================
Generates standardized enterprise consulting project payloads, milestones,
and Jinja2 stamping variables for BAST, PKS, MoM, and FSD documents.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict, List, Optional


DAY_NAMES_ID = {
    0: "Senin",
    1: "Selasa",
    2: "Rabu",
    3: "Kamis",
    4: "Jumat",
    5: "Sabtu",
    6: "Minggu",
}

MONTH_NAMES_ID = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}


def _extract_abbr(name: str, fallback: str = "CORP") -> str:
    """Extract an uppercase abbreviation from an entity name."""
    clean = re.sub(r"[^A-Za-z0-9 ]+", " ", name).strip()
    words = [w for w in clean.split() if w]
    if not words:
        return fallback
    if len(words) == 1:
        return words[0][:4].upper()
    return "".join(w[0] for w in words).upper()


def _extract_short_name(name: str) -> str:
    """Extract a concise brand name by stripping corporate entity prefixes/suffixes."""
    cleaned = re.sub(r"\b(PT\.?|Inc\.?|LLC|Corp\.?|Ltd\.?|GmbH|Co\.?)\b", "", name, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned if cleaned else name


def create_project_scaffold(
    project_name: str,
    client: str = "Enterprise Client Inc.",
    vendor: str = "Consulting Partner LLC",
    client_lead: str = "Client Sponsor",
    vendor_lead: str = "Engagement Lead",
) -> Dict[str, Any]:
    """
    Generate a comprehensive project payload dictionary containing standard fields:
      - project_name, client_name, client_lead, vendor_name, vendor_lead, created_at
      - milestones: list of standard milestones with id, title, target_date, status, deliverables
      - variables: standard Jinja2 stamping keys commonly used across BAST, PKS, MoM, and FSD documents
    """
    today = date.today()
    created_at = today.strftime("%Y-%m-%d")

    day_name_id = DAY_NAMES_ID.get(today.weekday(), "Senin")
    month_name_id = MONTH_NAMES_ID.get(today.month, "September")
    date_formatted_id = f"{today.day} {month_name_id} {today.year}"

    project_slug = re.sub(r"[^A-Za-z0-9_]+", "", project_name).upper()
    client_short = _extract_short_name(client)
    client_abbr = _extract_abbr(client, fallback="CLI")
    vendor_short = _extract_short_name(vendor)
    vendor_abbr = _extract_abbr(vendor, fallback="VND")

    milestones: List[Dict[str, Any]] = [
        {
            "id": 1,
            "title": "Milestone 1: Initiation & Architecture Blueprint",
            "target_date": "2026-10-15",
            "status": "In Progress",
            "deliverables": [
                "Project Charter",
                "Project Management Plan (PMP)",
                "Functional Specification Document (FSD)",
                "Solution Architecture Blueprint",
            ],
        },
        {
            "id": 2,
            "title": "Milestone 2: Core Delivery & SIT Acceptance",
            "target_date": "2026-11-30",
            "status": "Planned",
            "deliverables": [
                "Technical Specification Document (TSD)",
                "SIT Test Scenarios & Results",
                "Core Engine Deployment",
                "BAST Milestone 1",
            ],
        },
        {
            "id": 3,
            "title": "Milestone 3: UAT Acceptance & Operational Readiness",
            "target_date": "2026-12-20",
            "status": "Planned",
            "deliverables": [
                "UAT Test Scenarios & Sign-off",
                "User Guide & Administrator Guide",
                "Security Scan & Remediation Report",
            ],
        },
        {
            "id": 4,
            "title": "Milestone 4: Production Go-Live & Final Handover",
            "target_date": "2027-01-15",
            "status": "Planned",
            "deliverables": [
                "Production Cutover Checklist",
                "Final Handover Certificate (BAST Milestone 2)",
                "Warranty & Support Transition Plan",
            ],
        },
    ]

    variables: Dict[str, Any] = {
        # Organization / Corporate Names
        "client_name": client,
        "client_company": client,
        "client_short_name": client_short,
        "client_abbr": client_abbr,
        "vendor_name": vendor,
        "vendor_company": vendor,
        "vendor_short_name": vendor_short,
        "vendor_abbr": vendor_abbr,
        "vendor_group": vendor,
        "tech_partner": "Cloud Platform",

        # Stakeholders & Governance Leads
        "client_lead": client_lead,
        "client_lead_name": client_lead,
        "client_pm_name": client_lead,
        "client_exec_name": "Executive Sponsor",
        "vendor_lead": vendor_lead,
        "vendor_lead_name": vendor_lead,
        "vendor_pm_name": vendor_lead,
        "vendor_consultant_name": "Lead Solutions Consultant",
        "vendor_author_name": vendor_lead,
        "vendor_contributor_name": "Principal Architect",
        "first_party_name": client_lead,
        "first_party_title": "Project Director",
        "first_party_company": client,
        "second_party_name": vendor_lead,
        "second_party_title": "Engagement Director",
        "second_party_company": vendor,

        # Contract, Legal & Commercial
        "contract_number": f"PKS/{project_slug}/2026",
        "contract_date": created_at,
        "pks_number": f"PKS/{project_slug}/2026",
        "pks_date": created_at,
        "quotation_number": f"QUO/{project_slug}/2026",
        "total_mandays": 120,
        "warranty_months": 3,
        "payment_terms": "30 Days Net upon BAST Acceptance",
        "amount_idr": "Rp 750.000.000",
        "amount_words": "Tujuh Ratus Lima Puluh Juta Rupiah",
        "currency": "IDR",

        # Project Scope, Identification & Timeline
        "project_name": project_name,
        "project_title": project_name,
        "project_code": f"PRJ-{project_slug[:3]}-01",
        "project_version": "1.0.0",
        "effective_date": created_at,
        "start_date": created_at,
        "end_date": "2027-01-31",
        "location": "Jakarta, Indonesia",

        # BAST (Berita Acara Serah Terima) Handover Stamping
        "document_number": f"001/BAST/{project_slug}/2026",
        "day_name": day_name_id,
        "date_formatted": date_formatted_id,
        "milestone_name": "Milestone 1: Initiation & Architecture Blueprint",
        "milestone_number": 1,
        "deliverables_summary": [
            "Project Charter",
            "Project Management Plan (PMP)",
            "Functional Specification Document (FSD)",
            "Solution Architecture Blueprint",
        ],

        # Minutes of Meeting (MoM) Stamping
        "meeting_title": f"{project_name} Kick-off Meeting",
        "meeting_time": "09:00 - 10:30 WIB",
        "meeting_location": "Online via Microsoft Teams",
        "facilitator": vendor_lead,
        "agenda": [
            "Project Scope & Architecture Overview",
            "Milestone Timelines & Delivery Stages",
            "Resource Allocation & Access Provisioning",
            "Risk Assessment & Communication Cadence",
        ],
        "key_discussions": [
            f"Review and agreement on core deliverables for {project_name}.",
            "Confirmation of project team roles between client and vendor.",
            "Establishment of weekly progress sync schedule.",
        ],
        "action_items": [
            {
                "task": "Provision development and test environment credentials",
                "owner": client_lead,
                "due_date": "2026-09-18",
                "status": "Open",
            },
            {
                "task": "Deliver finalized Architecture Blueprint & FSD draft",
                "owner": vendor_lead,
                "due_date": "2026-09-25",
                "status": "Open",
            },
        ],
    }

    scaffold: Dict[str, Any] = {
        "project_name": project_name,
        "client_name": client,
        "client_lead": client_lead,
        "vendor_name": vendor,
        "vendor_lead": vendor_lead,
        "created_at": created_at,
        "milestones": milestones,
        "variables": variables,
    }

    return scaffold
