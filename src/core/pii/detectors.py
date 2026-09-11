"""
PII Detectors & Recognition Pipeline
====================================
Modular regex detectors and dictionary-based entity matchers for discovering
personally identifiable information and enterprise-sensitive strings.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Pattern, Tuple
from src.core.pii.models import PiiCategory, PiiConfidence, PiiMatch, TextNode


# Default enterprise organization & role dictionary for seeded templates
DEFAULT_ORGANIZATION_RULES: List[Tuple[str, str]] = [
    (r"\bPT\.?\s+Toyota\s+Tsusho\s+Indonesia\b", "{{ client_company }}"),
    (r"\bToyota\s+Tsusho\s+Indonesia\b", "{{ client_company }}"),
    (r"\bToyota\s+Tsusho\b", "{{ client_short_name }}"),
    (r"\bTTI\b", "{{ client_abbr }}"),
    (r"\bPT\.?\s+Mitra\s+Integrasi\s+Informatika\b", "{{ vendor_company }}"),
    (r"\bMitra\s+Integrasi\s+Informatika\b", "{{ vendor_company }}"),
    (r"\bMetrodata\b", "{{ vendor_group }}"),
    (r"\bMII\b", "{{ vendor_abbr }}"),
    (r"\bSnowflake\b", "{{ tech_partner }}"),
]

# Known person names present in seeded templates (for dictionary-based matching)
DEFAULT_KNOWN_PERSONS: List[Tuple[str, str]] = [
    (r"\bTadahiko\s+Onaka\b", "{{ client_exec_name }}"),
    (r"\bMulyanah\b", "{{ client_pm_name }}"),
    (r"\bFredric\s+Retanubun\b", "{{ client_lead_name }}"),
    (r"\bAndri\s+Agusman\b", "{{ client_engineer_1 }}"),
    (r"\bAgung\s+Rachman\b", "{{ client_engineer_2 }}"),
    (r"\bAnisah\s+Pratiwi\b", "{{ client_engineer_3 }}"),
    (r"\bDebby\s+Lutfi\s+Adrianto\b", "{{ client_analyst_1 }}"),
    (r"\bAndri\s+Setiawan\b", "{{ client_analyst_2 }}"),
    (r"\bAgus\s+Suhanto\b", "{{ vendor_pm_name }}"),
    (r"\bAdam\s+Nevriyanto\b", "{{ vendor_lead_name }}"),
    (r"\bVicko\s+Bhayyu\b", "{{ vendor_consultant_name }}"),
    (r"\bLaura\s+Veneskey\b", "{{ vendor_author_name }}"),
    (r"\bGolden\s+Ray\s+Vistanu\b", "{{ vendor_contributor_name }}"),
]


class BaseDetector:
    """Base interface for all pattern detectors."""
    name: str = "base"
    category: PiiCategory = PiiCategory.CUSTOM
    confidence: PiiConfidence = PiiConfidence.MEDIUM

    def detect(self, node: TextNode) -> List[PiiMatch]:
        raise NotImplementedError


class RegexDetector(BaseDetector):
    """Generic regex-driven detector."""

    def __init__(
        self,
        name: str,
        category: PiiCategory,
        pattern: str | Pattern,
        confidence: PiiConfidence = PiiConfidence.HIGH,
        default_placeholder: str = "[REDACTED]",
        flags: int = re.IGNORECASE,
    ):
        self.name = name
        self.category = category
        self.confidence = confidence
        self.default_placeholder = default_placeholder
        if isinstance(pattern, str):
            self.pattern = re.compile(pattern, flags=flags)
        else:
            self.pattern = pattern

    def detect(self, node: TextNode) -> List[PiiMatch]:
        matches: List[PiiMatch] = []
        for m in self.pattern.finditer(node.text):
            raw_val = m.group(0).strip()
            if not raw_val:
                continue
            matches.append(
                PiiMatch(
                    category=self.category,
                    raw_value=raw_val,
                    location=node.location,
                    confidence=self.confidence,
                    suggested_placeholder=self.default_placeholder,
                    detector=self.name,
                    char_start=m.start(),
                    char_end=m.end(),
                )
            )
        return matches


class EmailDetector(RegexDetector):
    def __init__(self):
        super().__init__(
            name="email_regex",
            category=PiiCategory.EMAIL,
            pattern=r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            confidence=PiiConfidence.HIGH,
            default_placeholder="{{ contact_email }}",
        )


class PhoneDetector(RegexDetector):
    def __init__(self):
        # Matches +62..., 08..., or international numbers with separators
        pattern = r"(?:\+?62|08)[0-9\s\-]{8,14}\b"
        super().__init__(
            name="phone_regex",
            category=PiiCategory.PHONE,
            pattern=pattern,
            confidence=PiiConfidence.HIGH,
            default_placeholder="{{ contact_phone }}",
        )


class GovernmentIdDetector(RegexDetector):
    """Indonesian NIK (16 digits) or NPWP (Tax ID)."""
    def __init__(self):
        # 16-digit NIK or formatted NPWP
        pattern = r"\b[1-9]\d{15}\b|\b\d{2}\.\d{3}\.\d{3}\.\d{1}-\d{3}\.\d{3}\b"
        super().__init__(
            name="gov_id_regex",
            category=PiiCategory.GOVERNMENT_ID,
            pattern=pattern,
            confidence=PiiConfidence.HIGH,
            default_placeholder="{{ national_id }}",
        )


class ContractIdDetector(RegexDetector):
    """Enterprise contract / PKS / BAST identifiers, e.g. 0073/ECP/IMPL/I/2026."""
    def __init__(self):
        pattern = r"\b\d{3,4}/[A-Z0-9_-]+/[A-Z0-9_-]+/[IVXLCDM]+/\d{4}\b"
        super().__init__(
            name="contract_id_regex",
            category=PiiCategory.CONTRACT_ID,
            pattern=pattern,
            confidence=PiiConfidence.HIGH,
            default_placeholder="{{ contract_number }}",
        )


class NetworkDetector(RegexDetector):
    """IPv4 addresses and internal server endpoints."""
    def __init__(self):
        pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
        super().__init__(
            name="ip_address_regex",
            category=PiiCategory.NETWORK,
            pattern=pattern,
            confidence=PiiConfidence.MEDIUM,
            default_placeholder="{{ server_ip }}",
        )


class DictionaryDetector(BaseDetector):
    """Matches known entities (organizations, individuals, systems) with specific placeholders."""

    def __init__(
        self,
        name: str,
        category: PiiCategory,
        rules: List[Tuple[str, str]],
        confidence: PiiConfidence = PiiConfidence.HIGH,
    ):
        self.name = name
        self.category = category
        self.confidence = confidence
        self.rules = [(re.compile(pat, re.IGNORECASE), repl) for pat, repl in rules]

    def detect(self, node: TextNode) -> List[PiiMatch]:
        matches: List[PiiMatch] = []
        for compiled_re, placeholder in self.rules:
            for m in compiled_re.finditer(node.text):
                raw_val = m.group(0).strip()
                if not raw_val:
                    continue
                matches.append(
                    PiiMatch(
                        category=self.category,
                        raw_value=raw_val,
                        location=node.location,
                        confidence=self.confidence,
                        suggested_placeholder=placeholder,
                        detector=self.name,
                        char_start=m.start(),
                        char_end=m.end(),
                    )
                )
        return matches


class DetectorPipeline:
    """Manages an orchestrated collection of detectors."""

    def __init__(
        self,
        custom_org_rules: Optional[List[Tuple[str, str]]] = None,
        custom_person_rules: Optional[List[Tuple[str, str]]] = None,
        extra_detectors: Optional[List[BaseDetector]] = None,
    ):
        org_rules = custom_org_rules if custom_org_rules is not None else DEFAULT_ORGANIZATION_RULES
        person_rules = custom_person_rules if custom_person_rules is not None else DEFAULT_KNOWN_PERSONS

        self.detectors: List[BaseDetector] = [
            EmailDetector(),
            PhoneDetector(),
            GovernmentIdDetector(),
            ContractIdDetector(),
            NetworkDetector(),
            DictionaryDetector("org_dictionary", PiiCategory.ORGANIZATION, org_rules, PiiConfidence.HIGH),
            DictionaryDetector("person_dictionary", PiiCategory.PERSON, person_rules, PiiConfidence.HIGH),
        ]
        if extra_detectors:
            self.detectors.extend(extra_detectors)

    def scan_node(self, node: TextNode) -> List[PiiMatch]:
        """Scan a single TextNode across all registered detectors."""
        matches: List[PiiMatch] = []
        for det in self.detectors:
            matches.extend(det.detect(node))
        return self._deduplicate_matches(matches)

    @staticmethod
    def _deduplicate_matches(matches: List[PiiMatch]) -> List[PiiMatch]:
        """Deduplicate overlapping matches, keeping longer or higher confidence matches."""
        if not matches:
            return []
        # Sort by length descending, then confidence
        sorted_m = sorted(
            matches,
            key=lambda m: (len(m.raw_value), 1 if m.confidence == PiiConfidence.HIGH else 0),
            reverse=True,
        )
        seen_spans = set()
        deduped = []
        for m in sorted_m:
            span_key = (m.location, m.raw_value.lower())
            if span_key not in seen_spans:
                seen_spans.add(span_key)
                deduped.append(m)
        return deduped
