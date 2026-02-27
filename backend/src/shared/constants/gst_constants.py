"""GST-related constants."""

# Standard GST rates in India
GST_RATES = [0, 0.25, 3, 5, 12, 18, 28]

# Indian state codes for GSTIN
STATE_CODES = {
    "01": "Jammu and Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "26": "Dadra and Nagar Haveli and Daman and Diu",
    "27": "Maharashtra",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman and Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh",
    "97": "Other Territory",
    "99": "Centre Jurisdiction"
}

# GST return types
RETURN_TYPES = [
    "GSTR-1",   # Outward supplies
    "GSTR-2A",  # Auto-drafted ITC
    "GSTR-2B",  # Auto-generated ITC statement
    "GSTR-3B",  # Summary return
    "GSTR-4",   # Composition scheme
    "GSTR-5",   # Non-resident taxable person
    "GSTR-6",   # Input Service Distributor
    "GSTR-7",   # TDS return
    "GSTR-8",   # E-commerce operator
    "GSTR-9",   # Annual return
    "GSTR-9C",  # Reconciliation statement
]

# Mismatch types
MISMATCH_TYPES = [
    "AMOUNT_MISMATCH",
    "TAX_AMOUNT_MISMATCH",
    "MISSING_IN_GSTR2B",
    "MISSING_IN_GSTR1",
    "MISSING_IN_PURCHASE_REGISTER",
    "GSTIN_MISMATCH",
    "DATE_MISMATCH",
    "INVOICE_NUMBER_MISMATCH",
    "TAX_RATE_MISMATCH",
    "HSN_CODE_MISMATCH",
    "DUPLICATE_ENTRY",
    "IRN_MISMATCH",
    "REVERSE_CHARGE_MISMATCH",
]

# Risk levels
RISK_LEVELS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

# Invoice types
INVOICE_TYPES = ["B2B", "B2C", "B2CL", "EXPORT", "CDNR", "CDNUR"]

# Tax components
TAX_COMPONENTS = ["CGST", "SGST", "IGST", "CESS"]
