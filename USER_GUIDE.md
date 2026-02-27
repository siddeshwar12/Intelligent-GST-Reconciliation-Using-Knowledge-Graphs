# 🚀 GST Intelligent Reconciliation System - User Guide

## 📋 Quick Start

### Access the System
**URL:** http://localhost:8000

### Pages Available
1. **Dashboard** - http://localhost:8000 (Overview & Process Flow)
2. **Workflow** - http://localhost:8000/workflow (Complete Validation)
3. **Upload** - http://localhost:8000/upload (File Upload)
4. **Results** - http://localhost:8000/results (View Results)
5. **API Docs** - http://localhost:8000/docs (API Documentation)

---

## 🎯 Quick Demo (2 Minutes)

1. Open: http://localhost:8000/workflow
2. Click: "Generate Sample Data"
3. Click: "Start Complete Workflow"
4. Watch: Animated progress (10 seconds)
5. View: Results with statistics
6. Click: "Download PDF Report"

---

## 📊 What This System Does

### Purpose
Validates whether Input Tax Credit (ITC) claimed by a buyer is legally supported by seller filings and tax payment.

### How It Works
1. **Seller Files GSTR-1** → Declares all sales
2. **Government Generates GSTR-2B** → Auto-generated for buyer
3. **Buyer Claims ITC in GSTR-3B** → Files ITC claim
4. **System Validates** → Checks complete chain
5. **Report Generated** → Approval/Rejection with reasons

---

## 🎨 New Features

### Dark FinTech Theme
- Professional navy blue background
- Electric blue accents
- Smooth animations
- Modern design

### Interactive Dashboard
- Counter animations on stats
- Clickable process timeline
- Educational modals
- Real-time data

### Natural Language Reports
- Company names (Supplier & Buyer)
- Plain English explanations
- Clear action items
- Fraud indicators

---

## 📄 File Formats Supported

### CSV Format
```csv
invoice_number,invoice_date,supplier_gstin,total_amount,tax_amount
INV-001,2024-01-15,27AABCU1234M1Z5,10000,1800
```

### JSON Format
```json
[
  {
    "invoice_number": "INV-001",
    "invoice_date": "2024-01-15",
    "supplier_gstin": "27AABCU1234M1Z5",
    "total_amount": 10000,
    "tax_amount": 1800
  }
]
```

---

## 🔥 Advanced Features

1. **Knowledge Graph Modeling** - Neo4j graph database
2. **Multi-Hop ITC Validation** - Complete chain verification
3. **Risk-Based Classification** - 4-tier system
4. **Explainable Audit Trail** - Graph visualization
5. **Vendor Compliance ML** - Random Forest model
6. **Fraud Pattern Detection** - Network analysis
7. **PDF Report Generation** - Natural language reports

---

## 🛠️ Technical Stack

- **Backend:** FastAPI (Python)
- **Database:** Neo4j (Graph Database)
- **ML:** scikit-learn
- **Frontend:** Jinja2 + Vanilla JavaScript
- **Architecture:** Clean Architecture + DDD

---

## 📞 Support

For issues or questions, check the API documentation at http://localhost:8000/docs
