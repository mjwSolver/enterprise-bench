"""
Enterprise Consulting Locale Engine
===================================
Bilingual localization subsystem providing formal enterprise English-to-Indonesian
translations for governance, category trackers, badges, and deliverable lifecycles,
while preserving technical cloud terminology in English.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
LOCALES_DIR = ROOT_DIR / "presets" / "locales"


class LocaleEngine:
    """Resolves localized copy strings with dot-notation lookup and fallback to canonical English."""

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

    def t(self, keypath: str, default: Optional[str] = None) -> str:
        """
        Translates a keypath (e.g. 'reference_slides.change_request.statuses.approved').
        Falls back to 'en' catalog if missing in current locale, and finally to default or keypath.
        """
        cat = self._catalogs.get(self.locale, {})
        val = self._lookup(cat, keypath)
        if val is not None and isinstance(val, str):
            return val

        en_cat = self._catalogs.get("en", {})
        val_en = self._lookup(en_cat, keypath)
        if val_en is not None and isinstance(val_en, str):
            return val_en

        return default if default is not None else keypath


_GLOBAL_ENGINES: Dict[str, LocaleEngine] = {}


def get_locale_engine(locale: str = "en") -> LocaleEngine:
    """Singleton getter for LocaleEngine."""
    loc = locale.lower()
    if loc not in _GLOBAL_ENGINES:
        _GLOBAL_ENGINES[loc] = LocaleEngine(loc)
    return _GLOBAL_ENGINES[loc]
