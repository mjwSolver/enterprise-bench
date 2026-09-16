"""
Enterprise Core Data Models
============================
Shared Pydantic v2 data contracts for enterprise deliverables, contracts,
milestones, presentations, and specification documents.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Stakeholder(BaseModel):
    name: str
    role: str
    organization: str
    email: Optional[str] = None
    phone: Optional[str] = None


class ActionItem(BaseModel):
    task: str
    owner: str
    due_date: Optional[str] = None
    status: str = "Open"
    notes: Optional[str] = None


class Milestone(BaseModel):
    id: int
    title: str
    due_date: Optional[str] = None
    status: str = "Pending"
    deliverables: List[str] = Field(default_factory=list)
    percentage: float = 0.0


class ProjectInfo(BaseModel):
    project_name: str
    project_code: Optional[str] = None
    client_name: str = "Enterprise Client Inc."
    vendor_name: str = "Consulting Partner LLC"
    contract_number: Optional[str] = None
    contract_date: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    project_manager_client: Optional[str] = None
    project_manager_vendor: Optional[str] = None
    stakeholders: List[Stakeholder] = Field(default_factory=list)
    milestones: List[Milestone] = Field(default_factory=list)


class BASTPayload(BaseModel):
    """Payload for Berita Acara Serah Terima (Handover Certificate)."""
    document_number: Optional[str] = "001/BAST/X/2026"
    project_name: str = "Enterprise Consulting Services"
    pks_number: str = "[CONTRACT_NO_001/VND/IMPL/I/2026]"
    day_name: str = "Senin"
    date_formatted: str = "16 Januari 2026"
    client_name: str = "Enterprise Client Inc."
    client_signatory_name: str = "Client Sponsor"
    client_signatory_title: str = "Project Leader"
    vendor_name: str = "Consulting Partner LLC"
    vendor_signatory_name: str = "Engagement Lead"
    vendor_signatory_title: str = "Division Manager"
    milestone_term: str = "termin pertama setelah Assessment dan Architecture Design"
    payment_term: str = "Pembayaran Tahap I sebesar 40% dari total Biaya Pekerjaan"
    amount_idr: Optional[str] = None
    deliverables_summary: List[str] = Field(default_factory=list)


class MoMPayload(BaseModel):
    """Payload for Minutes of Meeting (MoM)."""
    project_name: str = "Enterprise Consulting Delivery"
    meeting_title: Optional[str] = None
    client_name: str = "Enterprise Client Inc."
    client_abbr: str = "CLI"
    vendor_name: str = "Consulting Partner LLC"
    vendor_abbr: str = "VND"
    meeting_datetime: str = "16 Sep 2026 / 10:00 - 11:30 WIB"
    venue: str = "Online via Microsoft Teams"
    agenda: str = "Weekly Sprint & Architecture Review"
    facilitator: str = "Engagement Lead"
    client_attendees: List[str] = Field(default_factory=list)
    vendor_attendees: List[str] = Field(default_factory=list)
    discussions: str = "Review of sprint progress and technical deliverables."
    next_actions: str = "Follow-up items and target delivery dates."


class ProjectCharterPayload(BaseModel):
    """Payload for Project Charter (Governance Baseline)."""
    project_name: str = "Enterprise Strategic Modernization"
    project_sponsor: str = "Executive Sponsor (CFO & VP)"
    prepared_by: str = "Engagement Manager"
    charter_date: str = "17 Desember 2025"
    client_name: str = "Enterprise Client Inc."
    vendor_name: str = "Consulting Partner LLC"
    project_sponsor_org: str = "Executive Committee"
    project_owner_org: str = "Steering Advisory"
    client_end_users: str = "Business Analytics & Accounting"


class PKSPayload(BaseModel):
    """Payload for Master Service Agreement (Perjanjian Kerjasama / PKS)."""
    project_name_en: str = "ENTERPRISE DATA PLATFORM SERVICES"
    project_name_id: str = "JASA PENGEMBANGAN PLATFORM DATA ENTERPRISE"
    pks_number: str = "[CONTRACT_NO_001/VND/IMPL/I/2026]"
    agreement_date_en: str = "16 January 2026"
    agreement_date_id: str = "16 Januari 2026"
    agreement_duration_en: str = "5 (Five) months"
    agreement_duration_id: str = "5 (Lima) bulan"
    agreement_effective_date_en: str = "16 January 2026"
    agreement_effective_date_id: str = "16 Januari 2026"
    client_legal_name: str = "PT ENTERPRISE CLIENT INDONESIA"
    client_name: str = "PT Enterprise Client Indonesia"
    vendor_legal_name: str = "PT CONSULTING PARTNER INDONESIA"
    vendor_name: str = "PT Consulting Partner Indonesia"
    client_signatory_name: str = "Chief Executive Officer"
    client_signatory_title: str = "Director"
    vendor_signatory_name: str = "Managing Director"
    vendor_signatory_title: str = "President Director"
    phase_initiating_target: str = "16 January 2026 – 31 January 2026"
    phase_development_target: str = "1 February 2026 – 28 February 2026"
    phase_testing_target: str = "1 March 2026 – 31 March 2026"
    phase_golive_target: str = "1 April 2026"
    phase_warranty_target: str = "2 April 2026 – 2 June 2026"


class POCScopePayload(BaseModel):
    """Payload for Proof of Concept (POC) Scope & Environment Agreement."""
    client_name: str = "Enterprise Client Inc."
    trial_period: str = "16 January 2026 – 16 February 2026"
    snowflake_account_url: str = "https://xy12345.snowflakecomputing.com"
    admin_username: str = "poc_admin"
    initial_password: str = "[SECURE_TEMPORARY_PASSWORD]"
    poc_objectives: str = (
        "1. Ingestion of sample ERP accounting data into Snowflake staging tables.\n"
        "2. Validation of virtual warehouse scaling and query response SLA (<2s).\n"
        "3. Verification of executive dashboard semantic metrics and drill-down performance."
    )


class BASTChangeRequestPayload(BaseModel):
    """Payload for Handover Certificate - Change Request (BAST CR)."""
    document_number: Optional[str] = "001/BAST-CR/X/2026"
    project_name: str = "Enterprise Consulting Services"
    pks_number: str = "[CONTRACT_NO_001/VND/IMPL/I/2026]"
    quotation_number: str = "[QUOTATION_NO_001/VND/CR/2026]"
    day_name: str = "Kamis"
    date_formatted: str = "16 Januari 2026"
    client_name: str = "Enterprise Client Inc."
    client_signatory_name: str = "Client Sponsor"
    client_signatory_title: str = "Project Leader"
    vendor_name: str = "Consulting Partner LLC"
    vendor_signatory_name: str = "Engagement Lead"
    vendor_signatory_title: str = "Division Manager"
    cr_summary: str = "Change Request #1 (Inventory Aging Analytics Extension)"
    payment_term: str = "sebesar Rp182.500.000,00 (seratus delapan puluh dua juta lima ratus ribu rupiah)"



