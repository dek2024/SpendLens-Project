"""
Data models for SpendLens application.
Follows Single Responsibility Principle - each class represents one domain concept.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import pandas as pd


@dataclass
class Expense:
    """Represents a single expense entry."""
    date: datetime
    category: str
    amount: float
    notes: str = ""

    def to_dict(self) -> dict:
        """Convert expense to dictionary for DataFrame compatibility."""
        return {
            "Date/Time": self.date.strftime("%Y-%m-%d"),
            "Category": self.category,
            "Amount ($)": self.amount,
            "Notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Expense':
        """Create Expense from dictionary row."""
        date_val = data.get("Date/Time") or data.get("Date")
        if isinstance(date_val, str):
            try:
                date = datetime.strptime(date_val, "%Y-%m-%d")
            except ValueError:
                date = pd.to_datetime(date_val, errors="coerce") or datetime.now()
        else:
            date = datetime.now()

        return cls(
            date=date,
            category=data.get("Category", "Uncategorized"),
            amount=float(data.get("Amount ($)") or data.get("Amount") or 0.0),
            notes=data.get("Notes", "")
        )

    def __str__(self) -> str:
        return f"${self.amount:.2f} - {self.category} on {self.date.strftime('%Y-%m-%d')}"


@dataclass
class CategoryTotal:
    """Represents aggregated spending for a category."""
    category: str
    total: float
    count: int = 0

    def __str__(self) -> str:
        return f"{self.category}: ${self.total:.2f} ({self.count} transactions)"


@dataclass
class ParsedExpense:
    """Represents parsed expense data from text/voice input."""
    raw_text: str
    detected_amount: float
    detected_date: datetime
    confidence: float = 1.0

    def __str__(self) -> str:
        return f"Parsed: ${self.detected_amount:.2f} on {self.detected_date.strftime('%Y-%m-%d')}"
