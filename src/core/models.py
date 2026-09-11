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
    document_number: str = "001/BAST/X/2026"
    day_name: str = "Senin"
    date_formatted: str = "10 September 2026"
    first_party_name: str
    first_party_title: str
    first_party_company: str
    second_party_name: str
    second_party_title: str
    second_party_company: str
    pks_number: str
    pks_date: str
    project_name: str
    milestone_name: str
    milestone_number: int = 1
    amount_idr: Optional[str] = None
    deliverables_summary: List[str] = Field(default_factory=list)


class MoMPayload(BaseModel):
    """Payload for Minutes of Meeting (MoM)."""
    project_name: str
    meeting_title: str
    date: str
    time: str = "09:00 - 10:30 WIB"
    location: str = "Online via Microsoft Teams"
    facilitator: Optional[str] = None
    attendees: List[Stakeholder] = Field(default_factory=list)
    agenda: List[str] = Field(default_factory=list)
    key_discussions: List[str] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
