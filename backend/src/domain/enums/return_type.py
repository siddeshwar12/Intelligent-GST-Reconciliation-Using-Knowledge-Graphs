from enum import Enum


class ReturnType(str, Enum):
    """GST Return Types."""
    
    GSTR1 = "GSTR-1"  # Outward supplies
    GSTR2A = "GSTR-2A"  # Auto-drafted ITC
    GSTR2B = "GSTR-2B"  # Auto-generated ITC statement
    GSTR3B = "GSTR-3B"  # Summary return
    GSTR9 = "GSTR-9"  # Annual return
    PURCHASE_REGISTER = "PURCHASE_REGISTER"  # Internal purchase register
    E_INVOICE = "E_INVOICE"  # e-Invoice data
    E_WAY_BILL = "E_WAY_BILL"  # e-Way bill data
