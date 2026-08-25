"""State shared between the assistant's pages."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from ..models import Assignment
from ..reminder_workbook import Participant


@dataclass
class GeneratedItem:
    assignment: Assignment
    pdf: Path
    jpg: Path
    ics: Path


@dataclass
class WizardState:
    workbook_path: Path | None = None
    weeks: dict[date, list[Assignment]] = field(default_factory=dict)
    selected_dates: list[date] = field(default_factory=list)
    assignments: list[Assignment] = field(default_factory=list)
    generated: list[GeneratedItem] = field(default_factory=list)
    reminder_mode: str = "ambos"

    def reset_from_workbook(self) -> None:
        self.weeks = {}
        self.selected_dates = []
        self.assignments = []
        self.generated = []


@dataclass
class ReminderState:
    workbook_path: Path | None = None
    # Which source PDF each week comes from — normally they all point to
    # `workbook_path` (a single file chosen by hand), but when searching the
    # Padlet there can be several documents (VMC for the current bimester
    # and the next one published at the same time) and each week needs to
    # know which one it came from, because that week's image crop
    # (`GenerateCropThread`) has to open the right PDF.
    workbook_paths_by_date: dict[date, Path] = field(default_factory=dict)
    weeks: dict[date, list[Participant]] = field(default_factory=dict)
    selected_date: date | None = None
    participants: list[Participant] = field(default_factory=list)
    week_jpg: Path | None = None
    top_adjust_pt: float = 0.0
    bottom_adjust_pt: float = 0.0

    def reset_from_workbook(self) -> None:
        self.workbook_paths_by_date = {}
        self.weeks = {}
        self.selected_date = None
        self.participants = []
        self.week_jpg = None
        self.top_adjust_pt = 0.0
        self.bottom_adjust_pt = 0.0
