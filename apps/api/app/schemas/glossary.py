from typing import Literal

from pydantic import BaseModel

GlossaryKind = Literal["planet", "sign", "house", "dignity", "state", "concept"]


class GlossaryEntry(BaseModel):
    id: str  # e.g. "planet.venus", "house.7", "dignity.exalted"
    kind: GlossaryKind
    term: str
    transliteration: str
    sanskrit: str
    short: str
    body: str


class GlossaryResponse(BaseModel):
    entries: list[GlossaryEntry]
