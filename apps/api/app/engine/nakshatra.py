from dataclasses import dataclass

from app.engine.constants import (
    NAKSHATRA_LORD_CYCLE,
    NAKSHATRA_SPAN,
    NAKSHATRAS,
    PADA_SPAN,
    normalize,
)


@dataclass(frozen=True)
class NakshatraPosition:
    index: int  # 0..26
    name: str
    pada: int  # 1..4
    lord: str
    degrees_traversed: float  # degrees into the nakshatra, [0, 13.333)

    @property
    def fraction_traversed(self) -> float:
        return self.degrees_traversed / NAKSHATRA_SPAN


def nakshatra_of(longitude: float) -> NakshatraPosition:
    lon = normalize(longitude)
    index = min(int(lon // NAKSHATRA_SPAN), 26)
    traversed = lon - index * NAKSHATRA_SPAN
    pada = min(int(traversed // PADA_SPAN), 3) + 1
    return NakshatraPosition(
        index=index,
        name=NAKSHATRAS[index],
        pada=pada,
        lord=NAKSHATRA_LORD_CYCLE[index % 9],
        degrees_traversed=traversed,
    )
