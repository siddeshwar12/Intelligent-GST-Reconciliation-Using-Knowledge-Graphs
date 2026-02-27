"""Error codes for the application."""

# General error codes
ERROR_CODES = {
    "UNKNOWN_ERROR": "An unknown error occurred",
    "VALIDATION_ERROR": "Validation failed",
    "NOT_FOUND": "Resource not found",
    "DUPLICATE_ERROR": "Resource already exists",
    "GRAPH_ERROR": "Graph database error",
    "RECONCILIATION_ERROR": "Reconciliation error",
}

# Validation errors
VALIDATION_ERRORS = {
    "INVALID_GSTIN": "Invalid GSTIN format",
    "INVALID_IRN": "Invalid IRN format",
    "INVALID_AMOUNT": "Invalid amount",
    "INVALID_DATE": "Invalid date format",
    "INVALID_PERIOD": "Invalid GST period",
    "MISSING_REQUIRED_FIELD": "Required field is missing",
}

# Graph database errors
GRAPH_ERRORS = {
    "CONNECTION_FAILED": "Failed to connect to graph database",
    "QUERY_FAILED": "Graph query execution failed",
    "CONSTRAINT_VIOLATION": "Database constraint violated",
    "NODE_NOT_FOUND": "Node not found in graph",
}

# Reconciliation errors
RECONCILIATION_ERRORS = {
    "TAXPAYER_NOT_FOUND": "Taxpayer not found",
    "INVOICE_NOT_FOUND": "Invoice not found",
    "NO_DATA_FOR_PERIOD": "No data available for the specified period",
    "RECONCILIATION_FAILED": "Reconciliation process failed",
    "ITC_VALIDATION_FAILED": "ITC validation failed",
}
