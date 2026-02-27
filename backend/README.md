# GST Reconciliation System - Backend

Intelligent GST Reconciliation using Knowledge Graphs, built with clean architecture principles.

## Architecture

This backend follows **Clean Architecture** with clear separation of concerns:

```
Domain Layer (Core Business Logic)
    ↑
Application Layer (Use Cases)
    ↑
Infrastructure Layer (Technical Implementation)
    ↑
API Layer (HTTP Interface)
```

## Tech Stack

- **Framework**: FastAPI
- **Graph Database**: Neo4j
- **Cache**: Redis
- **ML**: scikit-learn
- **Language**: Python 3.10+

## Project Structure

```
backend/
├── src/
│   ├── api/              # API routes, controllers, schemas
│   ├── application/      # Use cases, application services
│   ├── domain/           # Core business logic (entities, value objects)
│   ├── infrastructure/   # Technical implementations
│   │   ├── graph/        # Neo4j operations
│   │   ├── reconciliation/  # Reconciliation engine
│   │   ├── audit/        # Audit trail generation
│   │   ├── ml/           # ML models
│   │   └── data_ingestion/  # Data parsers and loaders
│   ├── shared/           # Common utilities
│   └── config/           # Configuration
├── tests/                # Test suite
├── scripts/              # Utility scripts
└── requirements.txt
```

## Setup Instructions

### Prerequisites

1. **Python 3.10+**
2. **Neo4j 5.x** - Graph database
3. **Redis** - Caching layer (optional but recommended)

### Installation

1. **Clone the repository**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

4. **Set up Neo4j**

Option A: Docker
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:5.16.0
```

Option B: Local installation
- Download from https://neo4j.com/download/
- Install and start Neo4j
- Set password via Neo4j Browser (http://localhost:7474)

5. **Set up Redis** (optional)
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

6. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

Required environment variables:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=gst_reconciliation

REDIS_HOST=localhost
REDIS_PORT=6379
```

7. **Initialize database schema**
```bash
python scripts/setup_graph_schema.py
```

8. **Generate mock data** (optional)
```bash
python scripts/generate_mock_data.py
```

### Running the Application

**Development mode:**
```bash
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

**Production mode:**
```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

Access the API:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Running Tests
```bash
pytest
pytest --cov=src tests/  # With coverage
```

### Code Quality
```bash
black src/  # Format code
flake8 src/  # Lint
mypy src/  # Type checking
```

### Database Management

**View Neo4j Browser:**
http://localhost:7474

**Clear database:**
```cypher
MATCH (n) DETACH DELETE n
```

**View schema:**
```cypher
CALL db.schema.visualization()
```

## API Endpoints

### Reconciliation
- `POST /api/v1/reconcile` - Trigger reconciliation
- `GET /api/v1/reconciliation/{id}` - Get reconciliation status

### Mismatches
- `GET /api/v1/mismatches` - List all mismatches
- `GET /api/v1/mismatches/{id}` - Get mismatch details
- `PUT /api/v1/mismatches/{id}/resolve` - Resolve mismatch

### Audit Trail
- `GET /api/v1/audit-trail/{invoice_id}` - Get audit trail
- `GET /api/v1/audit-trail/{id}/export` - Export audit report

### Vendors
- `GET /api/v1/vendors` - List vendors
- `GET /api/v1/vendors/{id}/risk-score` - Get vendor risk score
- `GET /api/v1/vendors/{id}/compliance` - Get compliance history

### Data Ingestion
- `POST /api/v1/data/upload/gstr1` - Upload GSTR-1 data
- `POST /api/v1/data/upload/gstr2b` - Upload GSTR-2B data
- `POST /api/v1/data/upload/purchase-register` - Upload purchase register

## Key Features

### 1. Knowledge Graph Schema
- Taxpayers, Invoices, Returns, Payments as nodes
- Rich relationships for ITC validation
- Multi-hop traversal support

### 2. Reconciliation Engine
- Automatic invoice matching
- 4-tier risk classification (Critical, High, Medium, Low)
- Root cause analysis

### 3. Audit Trail
- Explainable reconciliation paths
- Graph visualization data
- Evidence collection

### 4. ML-based Risk Prediction
- Vendor compliance scoring
- Anomaly detection
- Predictive analytics

## Architecture Principles

### Clean Architecture
- **Domain Layer**: Pure business logic, no dependencies
- **Application Layer**: Use cases orchestrating domain logic
- **Infrastructure Layer**: Technical implementations
- **API Layer**: HTTP interface

### Design Patterns
- Repository Pattern for data access
- Strategy Pattern for matching algorithms
- Factory Pattern for entity creation
- Dependency Injection throughout

### Extensibility
- Easy to add new GST return types
- Pluggable matching strategies
- Configurable business rules
- Modular ML models

## Contributing

1. Follow clean architecture principles
2. Write tests for new features
3. Update documentation
4. Run code quality checks before committing

## License

Proprietary - All rights reserved
