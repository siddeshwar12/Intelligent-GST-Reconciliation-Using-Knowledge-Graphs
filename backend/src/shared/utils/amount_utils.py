"""Amount utility functions."""

from decimal import Decimal, ROUND_HALF_UP


def format_amount(amount: float, currency: str = "₹") -> str:
    """
    Format amount with currency symbol.
    
    Args:
        amount: Amount to format
        currency: Currency symbol
        
    Returns:
        Formatted string
        
    Example:
        >>> format_amount(100000.50)
        '₹1,00,000.50'
    """
    decimal_amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return f"{currency}{decimal_amount:,.2f}"


def parse_amount(amount_str: str) -> float:
    """
    Parse amount string to float.
    
    Args:
        amount_str: Amount string (may contain currency symbols and commas)
        
    Returns:
        Float amount
        
    Example:
        >>> parse_amount("₹1,00,000.50")
        100000.50
    """
    # Remove currency symbols and commas
    cleaned = amount_str.replace("₹", "").replace(",", "").strip()
    return float(cleaned)


def calculate_percentage(part: float, total: float) -> float:
    """
    Calculate percentage.
    
    Args:
        part: Part value
        total: Total value
        
    Returns:
        Percentage value
        
    Example:
        >>> calculate_percentage(25, 100)
        25.0
    """
    if total == 0:
        return 0.0
    return (part / total) * 100
