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
        self.locale = locale.lower()
        self.locales_dir = Path(locales_dir) if locales_dir else LOCALES_DIR
        self._catalogs: Dict[str, Dict[str, Any]] = {}
        self._load_catalog(self.locale)
        if self.locale != "en":
            self._load_catalog("en")

    def _load_catalog(self, loc: str) -> None:
        if loc in self._catalogs:
            return
        p = self.locales_dir / f"{loc}.yaml"
        if p.is_file():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    self._catalogs[loc] = yaml.safe_load(f) or {}
            except Exception:
                self._catalogs[loc] = {}
        else:
            self._catalogs[loc] = {}

    def _lookup(self, data: Dict[str, Any], keypath: str) -> Optional[Any]:
        current: Any = data
        for part in keypath.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def t(self, keypath: str, default: Optional[str] = None, **kwargs: Any) -> str:
        """
        Translates a keypath (e.g. 'reference_slides.change_request.statuses.approved').
        Falls back to 'en' catalog if missing in current locale, and finally to default or keypath.
        Applies keyword formatting if format placeholders exist and kwargs are provided.
        """
        cat = self._catalogs.get(self.locale, {})
        val = self._lookup(cat, keypath)
        if val is not None and isinstance(val, str):
            if kwargs:
                try:
                    return val.format(**kwargs)
                except Exception:
                    return val
            return val

        en_cat = self._catalogs.get("en", {})
        val_en = self._lookup(en_cat, keypath)
        if val_en is not None and isinstance(val_en, str):
            if kwargs:
                try:
                    return val_en.format(**kwargs)
                except Exception:
                    return val_en
            return val_en

        res = default if default is not None else keypath
        if kwargs and isinstance(res, str):
            try:
                return res.format(**kwargs)
            except Exception:
                return res
        return res

    def get(self, keypath: str, default: Any = None) -> Any:
        """Retrieves raw data (dict, list, str, or scalar) with fallback to 'en'."""
        cat = self._catalogs.get(self.locale, {})
        val = self._lookup(cat, keypath)
        if val is not None:
            return val

        en_cat = self._catalogs.get("en", {})
        val_en = self._lookup(en_cat, keypath)
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

    def translate_term(self, term: str) -> str:
        """
        Looks up a standardized enterprise term in the glossary table.
        Matches case-insensitively against English source keys and values.
        """
        if self.locale == "en":
            return term

        cat = self._catalogs.get(self.locale, {})
        glossary = cat.get("glossary", {})
        en_glossary = self._catalogs.get("en", {}).get("glossary", {})

        # 1. Exact or normalized key lookup
        norm_key = re.sub(r"[^a-zA-Z0-9]+", "_", term.strip().lower()).strip("_")
        if norm_key in glossary:
            return str(glossary[norm_key])

        # 2. Reverse value lookup in English glossary -> Indonesian glossary
        for g_key, g_en_val in en_glossary.items():
            if term.strip().lower() == str(g_en_val).strip().lower():
                if g_key in glossary:
                    return str(glossary[g_key])

        return term

    def translate_hybrid(self, text: str) -> str:
        """
        Translates governance phrases into formal Indonesian while preserving English
        technical terms (Snowflake, dbt, Streamlit, Cortex AI, Virtual Warehouse, etc.).
        """
        if self.locale == "en" or not text:
            return text

        translated = text
        en_glossary = self._catalogs.get("en", {}).get("glossary", {})
        id_glossary = self._catalogs.get("id", {}).get("glossary", {})

        # Replace known glossary terms (sorted by descending length to match phrases before words)
        terms = sorted(en_glossary.items(), key=lambda item: len(str(item[1])), reverse=True)
        for g_key, en_val in terms:
            if g_key in id_glossary:
                id_val = str(id_glossary[g_key])
                pattern = re.compile(r"\b" + re.escape(str(en_val)) + r"\b", re.IGNORECASE)
                translated = pattern.sub(id_val, translated)

                # Also match stripped parenthetical form e.g. "Change Request (CR)" -> "Change Request"
                m = re.match(r"^(.*?)\s*\([^)]+\)$", str(en_val))
                if m:
                    base_en = m.group(1).strip()
                    if base_en:
                        base_id = re.sub(r"\s*\([^)]+\)$", "", id_val).strip()
                        pat_base = re.compile(r"\b" + re.escape(base_en) + r"\b", re.IGNORECASE)
                        translated = pat_base.sub(base_id, translated)

        return translated


_GLOBAL_ENGINES: Dict[str, LocaleEngine] = {}


def get_locale_engine(locale: str = "en", locales_dir: Optional[Union[str, Path]] = None) -> LocaleEngine:
    """Singleton getter for LocaleEngine."""
    loc = locale.lower()
    cache_key = f"{loc}:{str(locales_dir) if locales_dir else 'default'}"
    if cache_key not in _GLOBAL_ENGINES:
        _GLOBAL_ENGINES[cache_key] = LocaleEngine(locale=loc, locales_dir=locales_dir)
    return _GLOBAL_ENGINES[cache_key]


def list_available_locales(locales_dir: Optional[Union[str, Path]] = None) -> List[str]:
    """Returns list of all available locale codes found in the locales directory."""
    ld = Path(locales_dir) if locales_dir else LOCALES_DIR
    if not ld.is_dir():
        return ["en"]
    locales = []
    for f in ld.glob("*.yaml"):
        locales.append(f.stem.lower())
    return sorted(list(set(locales)))
