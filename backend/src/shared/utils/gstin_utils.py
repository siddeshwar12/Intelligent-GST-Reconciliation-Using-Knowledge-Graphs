"""GSTIN utility functions."""

import re


GSTIN_PATTERN = re.compile(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$')


def validate_gstin(gstin: str) -> bool:
    """
    Validate GSTIN format.
    
    Args:
        gstin: GSTIN string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not gstin or len(gstin) != 15:
        return False
    return bool(GSTIN_PATTERN.match(gstin))


def extract_state_code(gstin: str) -> str:
    """
    Extract state code from GSTIN.
    
    Args:
        gstin: Valid GSTIN string
        
    Returns:
        State code (first 2 digits)
    """
    if not validate_gstin(gstin):
        raise ValueError(f"Invalid GSTIN: {gstin}")
    return gstin[:2]


def extract_pan(gstin: str) -> str:
    """
    Extract PAN from GSTIN.
    
    Args:
        gstin: Valid GSTIN string
        
    Returns:
        PAN (characters 3-12)
    """
    if not validate_gstin(gstin):
        raise ValueError(f"Invalid GSTIN: {gstin}")
    return gstin[2:12]
