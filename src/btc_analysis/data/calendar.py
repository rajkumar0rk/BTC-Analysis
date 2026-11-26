"""UTC execution grid calendars. Session schedules are explicit, not inferred holidays."""
from dataclasses import dataclass
from typing import Protocol


def grid(start: int, end: int, step: int = 60) -> None:
    if (type(start) is not int or type(end) is not int or type(step) is not int
            or step <= 0 or end <= start or start % step or end % step):
        raise ValueError("invalid aligned half-open UTC interval")


class Calendar(Protocol):
    @property
    def calendar_id(self) -> str: ...
    def intervals(self, start: int, end: int, step: int) -> tuple[tuple[int, int], ...]: ...


@dataclass(frozen=True, slots=True)
class ContinuousCalendar:
    calendar_id: str = "crypto-24x7"

    def intervals(self, start, end, step=60):
        grid(start, end, step)
        return ((start, end),)


@dataclass(frozen=True, slots=True)
class SessionCalendar:
    """Explicit UTC session intervals supplied by a reviewed exchange calendar.
    No automatic NSE holidays or DST inference. Coverage bounds must be supplied.
    """
    calendar_id: str
    coverage_start: int
    coverage_end: int
    sessions: tuple[tuple[int, int], ...]

    def __post_init__(self):
        grid(self.coverage_start, self.coverage_end)
        if not self.calendar_id or not isinstance(self.sessions, tuple):
            raise ValueError("immutable reviewed calendar required")
        last = self.coverage_start
        for a, b in self.sessions:
            grid(a, b)
            if a < last or b > self.coverage_end:
                raise ValueError("overlapping/out-of-coverage sessions")
            last = b

    def intervals(self, start, end, step=60):
        grid(start, end, step)
        if start < self.coverage_start or end > self.coverage_end:
            raise ValueError("calendar does not cover request")
        out = []
        for a, b in self.sessions:
            lo, hi = max(a, start), min(b, end)
            if lo < hi:
                grid(lo, hi, step)
                out.append((lo, hi))
        return tuple(out)
