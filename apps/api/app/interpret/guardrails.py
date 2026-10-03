"""What readings can't say, and the note they always carry.

Readings are frank: a hard placement is called hard, and the text says plainly what the
tradition reads into it (delays, friction, losses, health troubles, broken studies). The user
decides what to believe.

What stays off-limits is what no chart can honestly claim, or what could hurt someone who
takes it literally: timing of death, naming a specific illness or accident, telling anyone to
skip medical care or to put money into something specific, selling remedies, and claiming
certainty. Applies to the rule texts today and to LLM output in Phase 6.
"""

import re

# (pattern, why). Word-bounded and case-insensitive.
BANNED = [
    (r"death|dies?|dying|fatal|lifespan|longevity|early end", "no predicting death"),
    (r"accidents?|injur(y|ies)|surgery", "no predicting a specific harm"),
    (
        r"diseases?|cancer|diabetes|tumou?rs?|infertil\w*|heart attack|stroke|paralysis",
        "no naming a specific illness",
    ),
    (
        r"stop (taking|your) (medicine|medication|treatment)|instead of (a|your) doctor",
        "never discourage medical care",
    ),
    (
        r"stocks?|crypto\w*|lottery|gambl\w*|invest in|buy (gold|property|land|shares)",
        "no specific financial calls",
    ),
    (r"gemstones?|remed(y|ies)|puja|yantra|pay for", "no selling remedies"),
    (r"guarantee[ds]?|definitely|certainly|without fail|is certain|for sure", "no certainty"),
]
_BANNED = [(re.compile(rf"\b(?:{p})\b", re.IGNORECASE), why) for p, why in BANNED]

NOTE = (
    "These readings say plainly what Vedic tradition reads in your chart. "
    "What you make of them is up to you."
)


def violations(text: str) -> list[str]:
    """Reasons a piece of text can't be shown; empty when it's fine."""
    return [f"{why}: “{m.group(0)}”" for rx, why in _BANNED if (m := rx.search(text))]
