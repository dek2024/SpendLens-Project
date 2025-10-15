"""
Business logic for SpendLens application.
Implements SOLID principles with clean OOP architecture.

Design Patterns:
- Single Responsibility: Each class has one clear purpose
- Open/Closed: Extensible via interfaces
- Liskov Substitution: All implementations are interchangeable
- Interface Segregation: Focused interfaces (IStorage, IParser, IAIService)
- Dependency Inversion: Depends on abstractions, not concretions
"""

import re
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd
from word2number import w2n
import dateparser
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference

from models import Expense, CategoryTotal, ParsedExpense

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== INTERFACES (Dependency Inversion) ====================

class IParser(ABC):
    """Interface for parsing expense data from text."""
    
    @abstractmethod
    def parse_amount(self, text: str) -> float:
        """Extract dollar amount from text."""
        pass
    
    @abstractmethod
    def parse_date(self, text: str) -> datetime:
        """Extract date from natural language text."""
        pass
    
    @abstractmethod
    def parse_expense(self, text: str) -> ParsedExpense:
        """Parse complete expense from text."""
        pass


class IStorage(ABC):
    """Interface for expense storage operations."""
    
    @abstractmethod
    def load_expenses(self) -> List[Expense]:
        """Load all expenses from storage."""
        pass
    
    @abstractmethod
    def save_expenses(self, expenses: List[Expense]) -> None:
        """Save expenses to storage."""
        pass
    
    @abstractmethod
    def add_expense(self, expense: Expense) -> None:
        """Add single expense to storage."""
        pass
    
    @abstractmethod
    def clear_all(self) -> None:
        """Clear all expenses from storage."""
        pass


class IAIService(ABC):
    """Interface for AI-powered services."""
    
    @abstractmethod
    def transcribe_audio(self, audio_file) -> str:
        """Transcribe audio to text."""
        pass
    
    @abstractmethod
    def analyze_expenses(self, expenses: List[Expense], query: str) -> str:
        """Analyze expenses and answer user query."""
        pass


# ==================== IMPLEMENTATIONS ====================

class ExpenseParser(IParser):
    """
    Parses expense information from natural language text.
    Single Responsibility: Text parsing only.
    """
    
    def parse_amount(self, text: str) -> float:
        """
        Extract numeric or written dollar amounts from text.
        
        Args:
            text: Input text containing potential amount
            
        Returns:
            Extracted amount as float, or 0.0 if none found
            
        Examples:
            >>> parser.parse_amount("I spent $15.50 today")
            15.5
            >>> parser.parse_amount("Cost was twenty dollars")
            20.0
        """
        if not text:
            logger.warning("Empty text provided to parse_amount")
            return 0.0
        
        try:
            text_clean = text.replace(",", "").replace("$", "").lower()
            
            # Try numeric amount first
            match = re.search(r"\b(\d+(?:\.\d{1,2})?)\b", text_clean)
            if match:
                amount = float(match.group(1))
                logger.info(f"Parsed numeric amount: ${amount:.2f}")
                return amount
            
            # Try written numbers
            amount = float(w2n.word_to_num(text_clean))
            logger.info(f"Parsed written amount: ${amount:.2f}")
            return amount
            
        except Exception as e:
            logger.error(f"Failed to parse amount from '{text}': {e}")
            return 0.0
    
    def parse_date(self, text: str) -> datetime:
        """
        Parse date from natural language text.
        
        Handles phrases like:
        - 'yesterday', 'tomorrow', 'today'
        - 'next Wednesday', 'last Friday'
        - '3 days ago', 'two weeks ago'
        
        Args:
            text: Input text containing date information
            
        Returns:
            Parsed datetime, defaults to now if no date found
        """
        if not text:
            logger.warning("Empty text provided to parse_date")
            return datetime.now()
        
        try:
            text_lower = text.lower()
            today = datetime.now()
            
            # Handle explicit keywords
            if "yesterday" in text_lower:
                result = today - timedelta(days=1)
                logger.info(f"Parsed 'yesterday' as {result.date()}")
                return result
                
            elif "tomorrow" in text_lower:
                result = today + timedelta(days=1)
                logger.info(f"Parsed 'tomorrow' as {result.date()}")
                return result
                
            elif "last" in text_lower or "ago" in text_lower:
                parsed = dateparser.parse(
                    text,
                    settings={'PREFER_DATES_FROM': 'past', 'RELATIVE_BASE': today}
                )
                if parsed:
                    logger.info(f"Parsed past date: {parsed.date()}")
                    return parsed
                    
            elif "next" in text_lower:
                parsed = dateparser.parse(
                    text,
                    settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': today}
                )
                if parsed:
                    logger.info(f"Parsed future date: {parsed.date()}")
                    return parsed
            
            # General parsing
            parsed = dateparser.parse(text, settings={'RELATIVE_BASE': today})
            if parsed:
                logger.info(f"Parsed date: {parsed.date()}")
                return parsed
                
        except Exception as e:
            logger.error(f"Failed to parse date from '{text}': {e}")
        
        logger.info("No date found, defaulting to today")
        return today
    
    def parse_expense(self, text: str) -> ParsedExpense:
        """
        Parse complete expense information from text.
        
        Args:
            text: Natural language expense description
            
        Returns:
            ParsedExpense object with detected amount and date
        """
        logger.info(f"Parsing expense from: '{text}'")
        
        amount = self.parse_amount(text)
        date = self.parse_date(text)
        
        # Calculate confidence based on successful parsing
        confidence = 1.0
        if amount == 0.0:
            confidence -= 0.5
        
        return ParsedExpense(
            raw_text=text,
            detected_amount=amount,
            detected_date=date,
            confidence=confidence
        )


class ExcelStorage(IStorage):
    """
    Stores expenses in Excel format.
    Single Responsibility: File I/O operations only.
    """
    
    def __init__(self, file_path: str):
        """
        Initialize storage with file path.
        
        Args:
            file_path: Path to Excel file for storage
        """
        self.file_path = file_path
        logger.info(f"Initialized ExcelStorage with path: {file_path}")
    
    def load_expenses(self) -> List[Expense]:
        """
        Load all expenses from Excel file.
        
        Returns:
            List of Expense objects
        """
        import os
        
        if not os.path.exists(self.file_path):
            logger.info(f"File not found: {self.file_path}, returning empty list")
            return []
        
        try:
            df = pd.read_excel(self.file_path)
            logger.info(f"Loaded {len(df)} rows from {self.file_path}")
            
            # Filter out TOTAL rows and invalid entries
            df = df[
                (df["Category"].notna()) &
                (df["Category"].str.upper() != "TOTAL")
            ]
            
            expenses = [Expense.from_dict(row) for _, row in df.iterrows()]
            logger.info(f"Parsed {len(expenses)} valid expenses")
            return expenses
            
        except Exception as e:
            logger.error(f"Failed to load expenses: {e}")
            return []
    
    def save_expenses(self, expenses: List[Expense]) -> None:
        """
        Save all expenses to Excel file.
        
        Args:
            expenses: List of Expense objects to save
        """
        try:
            data = [exp.to_dict() for exp in expenses]
            df = pd.DataFrame(data)
            df.to_excel(self.file_path, index=False)
            logger.info(f"Saved {len(expenses)} expenses to {self.file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save expenses: {e}")
            raise
    
    def add_expense(self, expense: Expense) -> None:
        """
        Add single expense to storage.
        
        Args:
            expense: Expense object to add
        """
        expenses = self.load_expenses()
        expenses.append(expense)
        self.save_expenses(expenses)
        logger.info(f"Added expense: {expense}")
    
    def clear_all(self) -> None:
        """Clear all expenses from storage."""
        self.save_expenses([])
        logger.info("Cleared all expenses")


class ExpenseAnalyzer:
    """
    Analyzes expense data and generates insights.
    Single Responsibility: Data analysis only.
    """
    
    def calculate_category_totals(self, expenses: List[Expense]) -> List[CategoryTotal]:
        """
        Calculate total spending by category.
        
        Args:
            expenses: List of expenses to analyze
            
        Returns:
            List of CategoryTotal objects, sorted by total descending
        """
        logger.info(f"Calculating category totals for {len(expenses)} expenses")
        
        category_data: Dict[str, Dict] = {}
        
        for exp in expenses:
            if exp.category not in category_data:
                category_data[exp.category] = {"total": 0.0, "count": 0}
            
            category_data[exp.category]["total"] += exp.amount
            category_data[exp.category]["count"] += 1
        
        totals = [
            CategoryTotal(cat, data["total"], data["count"])
            for cat, data in category_data.items()
        ]
        
        # Sort by total descending
        totals.sort(key=lambda x: x.total, reverse=True)
        
        logger.info(f"Calculated {len(totals)} category totals")
        return totals
    
    def get_total_spending(self, expenses: List[Expense]) -> float:
        """Calculate total amount spent across all expenses."""
        total = sum(exp.amount for exp in expenses)
        logger.info(f"Total spending: ${total:.2f}")
        return total
    
    def filter_by_date_range(
        self, 
        expenses: List[Expense],
        start_date: datetime,
        end_date: datetime
    ) -> List[Expense]:
        """Filter expenses within a date range."""
        filtered = [
            exp for exp in expenses
            if start_date <= exp.date <= end_date
        ]
        logger.info(f"Filtered {len(filtered)} expenses between {start_date.date()} and {end_date.date()}")
        return filtered


class ExcelFormatter:
    """
    Formats Excel files with professional styling.
    Single Responsibility: Excel formatting only.
    """
    
    def format_workbook(self, file_path: str) -> None:
        """
        Apply professional formatting to Excel workbook.
        
        Args:
            file_path: Path to Excel file to format
        """
        try:
            logger.info(f"Formatting Excel file: {file_path}")
            
            wb = load_workbook(file_path)
            ws = wb.active
            ws.title = "Expense Summary"
            
            # Header styling
            header_fill = PatternFill(
                start_color="1F4E78",
                end_color="1F4E78",
                fill_type="solid"
            )
            header_font = Font(color="FFFFFF", bold=True, size=12)
            
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # Alternating row colors
            alt_fill = PatternFill(
                start_color="F2F2F2",
                end_color="F2F2F2",
                fill_type="solid"
            )
            for row in range(2, ws.max_row + 1):
                if row % 2 == 0:
                    for cell in ws[row]:
                        cell.fill = alt_fill
            
            # Currency formatting
            for cell in ws["C"][1:]:
                cell.number_format = '"$"#,##0.00'
            
            # Borders
            thin_border = Border(
                left=Side(style="thin", color="CCCCCC"),
                right=Side(style="thin", color="CCCCCC"),
                top=Side(style="thin", color="CCCCCC"),
                bottom=Side(style="thin", color="CCCCCC")
            )
            for row in ws.iter_rows():
                for cell in row:
                    cell.border = thin_border
                    cell.alignment = Alignment(vertical="center", wrap_text=True)
            
            # Auto-adjust column widths
            for col_cells in ws.columns:
                max_len = max(len(str(c.value)) if c.value else 0 for c in col_cells)
                ws.column_dimensions[get_column_letter(col_cells[0].column)].width = max_len + 4
            
            # Add chart
            if ws.max_row > 2:  # Only add chart if there's data
                chart = BarChart()
                chart.title = "Spending by Category"
                chart.y_axis.title = "Amount ($)"
                chart.x_axis.title = "Category"
                
                data = Reference(ws, min_col=3, min_row=1, max_row=ws.max_row - 1)
                categories = Reference(ws, min_col=2, min_row=2, max_row=ws.max_row - 1)
                chart.add_data(data, titles_from_data=True)
                chart.set_categories(categories)
                ws.add_chart(chart, f"A{ws.max_row + 3}")
            
            wb.save(file_path)
            logger.info("Excel formatting completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to format Excel file: {e}")
            raise


class OpenAIService(IAIService):
    """
    AI-powered services using OpenAI API.
    Single Responsibility: AI/ML operations only.
    """
    
    def __init__(self, client):
        """
        Initialize with OpenAI client.
        
        Args:
            client: OpenAI client instance
        """
        self.client = client
        logger.info("Initialized OpenAIService")
    
    def transcribe_audio(self, audio_file) -> str:
        """
        Transcribe audio file to text using Whisper.
        
        Args:
            audio_file: Audio file object
            
        Returns:
            Transcribed text
        """
        try:
            logger.info("Transcribing audio...")
            transcript = self.client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file
            )
            text = transcript.text.strip()
            logger.info(f"Transcription complete: '{text}'")
            return text
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    def analyze_expenses(self, expenses: List[Expense], query: str) -> str:
        """
        Analyze expenses using GPT and answer user query.
        
        Args:
            expenses: List of expenses to analyze
            query: User's question about their spending
            
        Returns:
            AI-generated analysis response
        """
        try:
            logger.info(f"Analyzing expenses for query: '{query}'")
            
            # Convert expenses to readable format
            expense_data = "\n".join([
                f"{exp.date.strftime('%Y-%m-%d')}: ${exp.amount:.2f} - {exp.category} ({exp.notes})"
                for exp in expenses
            ])
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial assistant analyzing expense data. Provide clear, concise, and helpful insights."
                    },
                    {
                        "role": "user",
                        "content": f"Here are my expenses:\n{expense_data}\n\nQuestion: {query}"
                    }
                ],
            )
            
            answer = response.choices[0].message.content
            logger.info("Expense analysis complete")
            return answer
            
        except Exception as e:
            logger.error(f"Expense analysis failed: {e}")
            return f"Sorry, I couldn't analyze your expenses: {str(e)}"


class ExpenseController:
    """
    Main controller coordinating all expense operations.
    Implements Dependency Inversion - depends on interfaces, not concrete classes.
    """
    
    def __init__(
        self,
        storage: IStorage,
        parser: IParser,
        analyzer: ExpenseAnalyzer,
        formatter: ExcelFormatter,
        ai_service: Optional[IAIService] = None
    ):
        """
        Initialize controller with dependencies.
        
        Args:
            storage: Storage implementation
            parser: Parser implementation
            analyzer: Analyzer instance
            formatter: Formatter instance
            ai_service: Optional AI service implementation
        """
        self.storage = storage
        self.parser = parser
        self.analyzer = analyzer
        self.formatter = formatter
        self.ai_service = ai_service
        logger.info("ExpenseController initialized with dependencies")
    
    def parse_and_create_expense(
        self,
        text: str,
        category: str,
        manual_amount: Optional[float] = None,
        manual_date: Optional[datetime] = None
    ) -> Expense:
        """
        Parse text and create expense with optional manual overrides.
        
        Args:
            text: Natural language expense description
            category: Expense category
            manual_amount: Override parsed amount
            manual_date: Override parsed date
            
        Returns:
            Created Expense object
        """
        parsed = self.parser.parse_expense(text)
        
        expense = Expense(
            date=manual_date if manual_date else parsed.detected_date,
            category=category,
            amount=manual_amount if manual_amount is not None else parsed.detected_amount,
            notes=text
        )
        
        logger.info(f"Created expense: {expense}")
        return expense
    
    def add_expense(
        self,
        text: str,
        category: str,
        manual_amount: Optional[float] = None,
        manual_date: Optional[datetime] = None
    ) -> Expense:
        """
        Create and save expense.
        
        Returns:
            Created and saved Expense object
        """
        expense = self.parse_and_create_expense(text, category, manual_amount, manual_date)
        self.storage.add_expense(expense)
        return expense
    
    def get_all_expenses(self) -> List[Expense]:
        """Get all expenses from storage."""
        return self.storage.load_expenses()
    
    def get_dashboard_data(self) -> Dict:
        """
        Get comprehensive dashboard data.
        
        Returns:
            Dictionary with expenses, totals, and category breakdowns
        """
        expenses = self.storage.load_expenses()
        category_totals = self.analyzer.calculate_category_totals(expenses)
        total_spending = self.analyzer.get_total_spending(expenses)
        
        return {
            "expenses": expenses,
            "category_totals": category_totals,
            "total_spending": total_spending,
            "expense_count": len(expenses)
        }
    
    def export_to_excel(self, file_path: str) -> None:
        """
        Export expenses to formatted Excel file.
        
        Args:
            file_path: Destination file path
        """
        expenses = self.storage.load_expenses()
        
        # Add TOTAL row
        total = self.analyzer.get_total_spending(expenses)
        total_expense = Expense(
            date=datetime.now(),
            category="TOTAL",
            amount=total,
            notes=""
        )
        expenses.append(total_expense)
        
        # Save and format
        temp_storage = ExcelStorage(file_path)
        temp_storage.save_expenses(expenses)
        self.formatter.format_workbook(file_path)
        
        logger.info(f"Exported {len(expenses)-1} expenses to {file_path}")
    
    def clear_all_expenses(self) -> None:
        """Clear all expenses from storage."""
        self.storage.clear_all()
        logger.info("All expenses cleared")
