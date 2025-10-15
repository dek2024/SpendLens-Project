"""
Data models for SpendLens application.
Follows Single Responsibility Principle - each class represents one domain concept.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Expense:
    """
    Represents a single expense entry.
    
    Attributes:
        date: Date of the expense
        category: Spending category (Food, Gas, etc.)
        amount: Dollar amount spent
        notes: Optional description or notes
    """
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
        """Create Expense from dictionary."""
        date_str = data.get("Date/Time", "")
        if isinstance(date_str, str):
            date = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            date = datetime.now()
            
        return cls(
            date=date,
            category=data.get("Category", "Uncategorized"),
            amount=float(data.get("Amount ($)", 0.0)),
            notes=data.get("Notes", "")
        )
    
    def __str__(self) -> str:
        return f"${self.amount:.2f} - {self.category} on {self.date.strftime('%Y-%m-%d')}"


@dataclass
class CategoryTotal:
    """
    Represents aggregated spending for a category.
    
    Attributes:
        category: Category name
        total: Total amount spent
        count: Number of transactions
    """
    category: str
    total: float
    count: int = 0
    
    def __str__(self) -> str:
        return f"{self.category}: ${self.total:.2f} ({self.count} transactions)"


@dataclass
class ParsedExpense:
    """
    Represents parsed expense data from text/voice input.
    
    Attributes:
        raw_text: Original input text
        detected_amount: Parsed dollar amount
        detected_date: Parsed date
        confidence: Parsing confidence score (0-1)
    """
    raw_text: str
    detected_amount: float
    detected_date: datetime
    confidence: float = 1.0
    
    def __str__(self) -> str:
        return f"Parsed: ${self.detected_amount:.2f} on {self.detected_date.strftime('%Y-%m-%d')}"
