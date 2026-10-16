"""
Enterprise Consulting Locale Engine
===================================
Bilingual localization subsystem providing formal enterprise English-to-Indonesian
translations for governance, category trackers, badges, and deliverable lifecycles,
while preserving technical cloud terminology in English.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
LOCALES_DIR = ROOT_DIR / "presets" / "locales"


class LocaleEngine:
    """Resolves localized copy strings with dot-notation lookup, formatting, and fallback to English."""

    def __init__(self, locale: str = "en", locales_dir: Optional[Union[str, Path]] = None) -> None:
        self.locale = locale.lower() if locale else "en"
        self.locales_dir = Path(locales_dir).resolve() if locales_dir else LOCALES_DIR.resolve()
        self._catalogs: Dict[str, Dict[str, Any]] = {}
        self._lookup_cache: Dict[tuple[str, str], Any] = {}
        self._reverse_glossary: Dict[str, Dict[str, str]] = {}
        self._hybrid_rules_cache: Dict[str, List[tuple[re.Pattern, str]]] = {}
        self._load_catalog(self.locale)
        if self.locale != "en":
            self._load_catalog("en")

    def _load_catalog(self, loc: str) -> None:
        if not loc or not isinstance(loc, str) or loc in self._catalogs:
            return
        # Path traversal defense: validate identifier syntax
        if not re.match(r"^[a-zA-Z0-9_\-]+$", loc):
            self._catalogs[loc] = {}
            return
        try:
            p = (self.locales_dir / f"{loc}.yaml").resolve()
            if not p.is_relative_to(self.locales_dir):
                self._catalogs[loc] = {}
                return
            if p.is_file():
                with open(p, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    self._catalogs[loc] = data if isinstance(data, dict) else {}
            else:
                self._catalogs[loc] = {}
        except Exception:
            self._catalogs[loc] = {}

    def _lookup(self, data: Dict[str, Any], keypath: str) -> Optional[Any]:
        if not keypath or not isinstance(keypath, str) or not isinstance(data, dict):
            return None
        current: Any = data
        for part in keypath.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def _cached_lookup(self, loc: str, keypath: str) -> Optional[Any]:
        cache_key = (loc, keypath)
        if cache_key in self._lookup_cache:
            return self._lookup_cache[cache_key]
        cat = self._catalogs.get(loc, {})
        val = self._lookup(cat, keypath)
        if len(self._lookup_cache) < 4096:
            self._lookup_cache[cache_key] = val
        return val

    def t(self, keypath: str, default: Optional[str] = None, **kwargs: Any) -> str:
        """
        Translates a keypath (e.g. 'reference_slides.change_request.statuses.approved').
        Falls back to 'en' catalog if missing in current locale, and finally to default or keypath.
        Applies keyword formatting if format placeholders exist and kwargs are provided.
        """
        def _format_token(val_str: str, kw: Dict[str, Any]) -> str:
            if not kw:
                return val_str
            try:
                return val_str.format(**kw)
            except (KeyError, ValueError, IndexError):
                # Resilient token substitution: preserve unprovided placeholders without failure
                def _rep(match: re.Match) -> str:
                    k = match.group(1)
                    return str(kw[k]) if k in kw else match.group(0)
                return re.sub(r"\{([a-zA-Z0-9_]+)\}", _rep, val_str)

        val = self._cached_lookup(self.locale, keypath)
        if val is not None and not isinstance(val, (dict, list)):
            val_str = str(val) if not isinstance(val, str) else val
            return _format_token(val_str, kwargs)

        val_en = self._cached_lookup("en", keypath)
        if val_en is not None and not isinstance(val_en, (dict, list)):
            val_str = str(val_en) if not isinstance(val_en, str) else val_en
            return _format_token(val_str, kwargs)

        res = default if default is not None else keypath
        if kwargs and isinstance(res, str):
            return _format_token(res, kwargs)
        return str(res) if res is not None else ""

    def get(self, keypath: str, default: Any = None) -> Any:
        """Retrieves raw data (dict, list, str, or scalar) with fallback to 'en'."""
        val = self._cached_lookup(self.locale, keypath)
        if val is not None:
            return val

        val_en = self._cached_lookup("en", keypath)
        if val_en is not None:
            return val_en

        return default

    def get_dict(self, keypath: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Retrieves a dictionary structure from catalog with fallback."""
        val = self.get(keypath, default)
        return val if isinstance(val, dict) else (default or {})

    def get_list(self, keypath: str, default: Optional[List[Any]] = None) -> List[Any]:
        """Retrieves a list structure from catalog with fallback."""
        val = self.get(keypath, default)
        return val if isinstance(val, list) else (default or [])

    def _get_reverse_glossary(self) -> Dict[str, str]:
        if "en" not in self._reverse_glossary:
            en_cat = self._catalogs.get("en", {})
            en_glossary = en_cat.get("glossary") if isinstance(en_cat, dict) else None
            rev: Dict[str, str] = {}
            if isinstance(en_glossary, dict):
                for g_key, g_en_val in en_glossary.items():
                    if g_en_val is not None:
                        norm = str(g_en_val).strip().lower()
                        rev[norm] = g_key
            self._reverse_glossary["en"] = rev
        return self._reverse_glossary["en"]

    def translate_term(self, term: str) -> str:
        """
        Looks up a standardized enterprise term in the glossary table.
        Matches case-insensitively against English source keys and values using O(1) indexed lookup.
        """
        if self.locale == "en":
            return term
        if not term or not isinstance(term, str):
            return "" if term is None else str(term)

        cat = self._catalogs.get(self.locale, {})
        cat_glossary = cat.get("glossary") if isinstance(cat, dict) else None
        glossary = cat_glossary if isinstance(cat_glossary, dict) else {}

        # 1. Exact or normalized key lookup
        stripped_lower = term.strip().lower()
        norm_key = re.sub(r"[^a-zA-Z0-9]+", "_", stripped_lower).strip("_")
        if norm_key in glossary:
            return str(glossary[norm_key])

        # 2. Reverse value lookup using cached reverse glossary index O(1)
        rev_map = self._get_reverse_glossary()
        if stripped_lower in rev_map:
            g_key = rev_map[stripped_lower]
            if g_key in glossary:
                return str(glossary[g_key])

        return term

    def _get_hybrid_rules(self) -> List[tuple[re.Pattern, str]]:
        if self.locale in self._hybrid_rules_cache:
            return self._hybrid_rules_cache[self.locale]

        en_cat = self._catalogs.get("en", {})
        en_glossary = en_cat.get("glossary") if isinstance(en_cat, dict) else None
        en_glossary = en_glossary if isinstance(en_glossary, dict) else {}

        target_cat = self._catalogs.get(self.locale) or self._catalogs.get("id") or {}
        target_glossary = target_cat.get("glossary") if isinstance(target_cat, dict) else None
        target_glossary = target_glossary if isinstance(target_glossary, dict) else {}

        rules: List[tuple[re.Pattern, str]] = []
        terms = sorted(en_glossary.items(), key=lambda item: len(str(item[1] or "")), reverse=True)
        for g_key, en_val in terms:
            if en_val is None or g_key not in target_glossary:
                continue
            target_val = str(target_glossary[g_key])
            en_str = str(en_val)
            # Smart boundary: lookarounds (?<!\w) ... (?!\w) handle words and parenthesized terms safely
            pat_str = rf"(?<!\w){re.escape(en_str)}(?!\w)"
            try:
                rules.append((re.compile(pat_str, re.IGNORECASE), target_val))
            except Exception:
                continue

            # Also match stripped parenthetical form e.g. "Change Request (CR)" -> "Change Request"
            m = re.match(r"^(.*?)\s*\([^)]+\)$", en_str)
            if m:
                base_en = m.group(1).strip()
                if base_en:
                    base_target = re.sub(r"\s*\([^)]+\)$", "", target_val).strip()
                    pat_base_str = rf"(?<!\w){re.escape(base_en)}(?!\w)"
                    try:
                        rules.append((re.compile(pat_base_str, re.IGNORECASE), base_target))
                    except Exception:
                        pass

        self._hybrid_rules_cache[self.locale] = rules
        return rules

    def translate_hybrid(self, text: str) -> str:
        """
        Translates governance phrases into formal Indonesian while preserving English
        technical terms (Snowflake, dbt, Streamlit, Cortex AI, Virtual Warehouse, etc.).
        """
        if self.locale == "en" or not text or not isinstance(text, str):
            return text

        rules = self._get_hybrid_rules()
        translated = text
        for pattern, target_val in rules:
            translated = pattern.sub(target_val, translated)

        return translated


_GLOBAL_ENGINES: Dict[str, LocaleEngine] = {}


def get_locale_engine(locale: str = "en", locales_dir: Optional[Union[str, Path]] = None) -> LocaleEngine:
    """Singleton getter for LocaleEngine."""
    loc = locale.lower() if locale else "en"
    cache_key = f"{loc}:{str(locales_dir) if locales_dir else 'default'}"
    if cache_key not in _GLOBAL_ENGINES:
        _GLOBAL_ENGINES[cache_key] = LocaleEngine(locale=loc, locales_dir=locales_dir)
    return _GLOBAL_ENGINES[cache_key]


def list_available_locales(locales_dir: Optional[Union[str, Path]] = None) -> List[str]:
    """Returns list of all available locale codes found in the locales directory."""
    ld = Path(locales_dir).resolve() if locales_dir else LOCALES_DIR.resolve()
    if not ld.is_dir():
        return ["en"]
    locales = []
    try:
        for f in ld.glob("*.yaml"):
            if f.is_file() and re.match(r"^[a-zA-Z0-9_\-]+$", f.stem):
                locales.append(f.stem.lower())
    except OSError:
        return ["en"]
    return sorted(list(set(locales))) or ["en"]
