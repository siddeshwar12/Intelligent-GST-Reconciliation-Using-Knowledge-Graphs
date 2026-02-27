"""
Simple script to run the GST Reconciliation System.

This starts the FastAPI server with the integrated dashboard.
"""

import uvicorn
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting GST Reconciliation System")
    print("=" * 60)
    print()
    print("📊 Dashboard: http://localhost:8000")
    print("📚 API Docs:  http://localhost:8000/docs")
    print("🔍 Health:    http://localhost:8000/health")
    print()
    print("=" * 60)
    print()
    
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
