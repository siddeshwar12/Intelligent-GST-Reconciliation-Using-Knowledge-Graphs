"""Graph database related exceptions."""

from .base_exception import GSTReconciliationException


class GraphException(GSTReconciliationException):
    """Base exception for graph database errors."""
    
    def __init__(self, message: str):
        super().__init__(message, "GRAPH_ERROR")


class GraphConnectionException(GraphException):
    """Exception for graph database connection errors."""
    
    def __init__(self, message: str = "Failed to connect to graph database"):
        super().__init__(message)


class GraphQueryException(GraphException):
    """Exception for graph query errors."""
    
    def __init__(self, query: str, error: str):
        message = f"Graph query failed: {error}\nQuery: {query}"
        super().__init__(message)
        self.query = query
        self.error = error
