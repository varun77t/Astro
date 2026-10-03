"""Loads the YAML knowledge base. Parsed once per process; the files ship with the code."""

from functools import cache
from pathlib import Path

import yaml

from app.schemas.glossary import GlossaryEntry

KNOWLEDGE_DIR = Path(__file__).resolve().parent


@cache
def load_glossary() -> tuple[GlossaryEntry, ...]:
    raw = yaml.safe_load((KNOWLEDGE_DIR / "glossary.yaml").read_text(encoding="utf-8"))
    entries = tuple(GlossaryEntry.model_validate(item) for item in raw)
    ids = [e.id for e in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate glossary ids")
    return entries
