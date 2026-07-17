"""Validated data models for persisted study features."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from bible_app.core.references import normalized_reference


@dataclass
class HymnReference:
    title: str
    hymnal: str = ""
    number: str = ""
    page: int = 0
    added: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def validate(self):
        if not self.title.strip():
            raise ValueError("Hymn title is required.")
        self.page = int(self.page or 0)
        return True

    def to_dict(self):
        self.validate()
        return {
            "title": self.title.strip(),
            "hymnal": self.hymnal.strip(),
            "number": str(self.number).strip(),
            "page": self.page,
            "added": self.added,
        }


@dataclass
class UserCrossReference:
    target: str
    reason: str = "User link"

    def validate(self):
        self.target = normalized_reference(self.target)
        if not self.target:
            raise ValueError("Cross-reference target is required.")
        self.reason = self.reason.strip() or "User link"
        return True

    def to_dict(self):
        self.validate()
        return {"target": self.target, "reason": self.reason}


@dataclass
class StudyWorksheet:
    observation: str = ""
    interpretation: str = ""
    application: str = ""
    questions: str = ""
    prayer: str = ""
    related_hymn: str = ""
    tags: str = ""
    updated: str = ""

    def validate(self):
        return True

    def to_dict(self):
        self.validate()
        return {
            "observation": self.observation,
            "interpretation": self.interpretation,
            "application": self.application,
            "questions": self.questions,
            "prayer": self.prayer,
            "related_hymn": self.related_hymn,
            "tags": self.tags,
            "updated": self.updated,
        }


@dataclass
class BibleNote:
    reference: str
    text: str
    created: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    tags: List[str] = field(default_factory=list)

    def validate(self):
        self.reference = normalized_reference(self.reference)
        self.text = str(self.text).strip()
        self.tags = [str(tag).strip() for tag in self.tags if str(tag).strip()]
        if not self.reference or not self.text:
            raise ValueError("Reference and text are required.")
        return True

    def to_dict(self):
        self.validate()
        return {
            "reference": self.reference,
            "text": self.text,
            "created": self.created,
            "tags": self.tags,
        }


@dataclass
class JournalEntry:
    reference: str
    verse: str = ""
    reflection: str = ""
    prayer: str = ""
    images: List[str] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def validate(self):
        self.reference = normalized_reference(self.reference)
        self.reflection = str(self.reflection).strip()
        self.prayer = str(self.prayer).strip()
        self.images = [str(path).strip() for path in self.images if str(path).strip()]
        if not self.reference:
            raise ValueError("Journal reference is required.")
        if not self.reflection and not self.prayer and not self.images:
            raise ValueError("Journal entry must include reflection, prayer, or images.")
        return True

    def to_dict(self):
        self.validate()
        return {
            "created": self.created,
            "reference": self.reference,
            "verse": self.verse,
            "reflection": self.reflection,
            "prayer": self.prayer,
            "images": self.images,
        }
