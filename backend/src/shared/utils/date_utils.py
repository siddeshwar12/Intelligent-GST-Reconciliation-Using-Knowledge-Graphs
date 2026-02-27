"""Date utility functions."""

from datetime import datetime
from typing import Tuple


def parse_gst_period(period: str) -> Tuple[int, int]:
    """
    Parse GST period string to month and year.
    
    Args:
        period: Period string in format MMYYYY (e.g., "032024")
        
    Returns:
        Tuple of (month, year)
        
    Example:
        >>> parse_gst_period("032024")
        (3, 2024)
    """
    if len(period) != 6:
        raise ValueError(f"Invalid period format: {period}. Expected MMYYYY")
    
    month = int(period[:2])
    year = int(period[2:])
    
    if not (1 <= month <= 12):
        raise ValueError(f"Invalid month: {month}")
    
    return month, year


def get_financial_year(date: datetime) -> str:
    """
    Get financial year for a given date.
    Indian financial year: April to March
    
    Args:
        date: Date to get financial year for
        
    Returns:
        Financial year string in format YYYY-YY
        
    Example:
        >>> get_financial_year(datetime(2024, 3, 15))
        '2023-24'
        >>> get_financial_year(datetime(2024, 4, 15))
        '2024-25'
    """
    if date.month >= 4:
        start_year = date.year
        end_year = date.year + 1
    else:
        start_year = date.year - 1
        end_year = date.year
    
    return f"{start_year}-{str(end_year)[-2:]}"


def format_period(month: int, year: int) -> str:
    """
    Format month and year to GST period string.
    
    Args:
        month: Month (1-12)
        year: Year (YYYY)
        
    Returns:
        Period string in format MMYYYY
        
    Example:
        >>> format_period(3, 2024)
        '032024'
    """
    return f"{month:02d}{year}"
