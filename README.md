# Intelligent GST Reconciliation Using Knowledge Graphs

A FastAPI application for exploring GST input-tax-credit reconciliation with graph modeling, risk classification, audit trails, and an interactive dashboard.

## Highlights

- Invoice, taxpayer, vendor, and mismatch modeling with Neo4j
- Risk-based reconciliation and explainable audit output
- Dashboard, upload workflow, report generation, and API documentation
- Optional Neo4j and Redis integrations; the application can start in a limited mode when they are unavailable

## Run locally

Prerequisites: Python 3.10+.

```bash
git clone https://github.com/siddeshwar12/Intelligent-GST-Reconciliation-Using-Knowledge-Graphs.git
cd Intelligent-GST-Reconciliation-Using-Knowledge-Graphs/backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Optionally create a `.env` from the root `.env.example` and configure Neo4j or Redis. Then run:

```bash
python run_server.py
```

Open:

- Dashboard: [http://localhost:8000](http://localhost:8000)
- API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

## Test checklist

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api
```

Then upload a CSV or JSON sample through the dashboard and review the generated reconciliation results.

## Configuration

Neo4j and Redis are optional for development. Use the provided environment template to configure them when needed.

## Responsible use

This is a demonstration project for GST reconciliation workflows. Validate output against official records and applicable regulations before using it in a business process.
