"""Parse human durations such as "1h30m" or "45s" into seconds."""
import re

_UNITS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
_PART = re.compile(r"(\d+)([dhms])")


def parse_duration(text: str) -> int:
    """Return the number of seconds in TEXT, e.g. "1h30m" -> 5400."""
    text = text.strip().lower()
    if not text:
        raise ValueError("empty duration")
    pos, total = 0, 0
    for m in _PART.finditer(text):
        if m.start() != pos:
            raise ValueError(f"bad duration: {text!r}")
        total += int(m.group(1)) * _UNITS[m.group(2)]
        pos = m.end()
    if pos != len(text):
        raise ValueError(f"bad duration: {text!r}")
    return total
