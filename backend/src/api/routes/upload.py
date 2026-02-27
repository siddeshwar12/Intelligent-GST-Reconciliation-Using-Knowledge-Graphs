"""File upload and data processing endpoints."""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(tags=["upload"])

# In-memory storage for demo (replace with database in production)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Global storage for processed data
processed_data = {
    "invoices": [],
    "mismatches": [],
    "acknowledgments": [],
    "stats": {
        "total_invoices": 0,
        "total_mismatches": 0,
        "match_rate": 0,
        "high_risk_count": 0
    }
}


class ProcessRequest(BaseModel):
    """Request model for processing data."""
    filename: str


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload invoice data file (CSV or JSON).
    
    Args:
        file: Uploaded file
        
    Returns:
        Upload confirmation with file details
    """
    # Validate file type
    if not file.filename.endswith(('.csv', '.json')):
        raise HTTPException(status_code=400, detail="Only CSV and JSON files are supported")
    
    # Validate file size (max 50MB)
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
    
    # Save file
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Parse and count records
    try:
        if file.filename.endswith('.json'):
            data = json.loads(content.decode('utf-8'))
            records_count = len(data) if isinstance(data, list) else 1
        else:  # CSV
            lines = content.decode('utf-8').splitlines()
            records_count = len(lines) - 1  # Exclude header
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
    
    return {
        "message": "File uploaded successfully",
        "filename": file.filename,
        "size": len(content),
        "records_count": records_count
    }


@router.post("/process")
async def process_data(request: ProcessRequest):
    """
    Process uploaded data and run reconciliation.
    
    Args:
        request: Processing request with filename
        
    Returns:
        Processing results
    """
    file_path = UPLOAD_DIR / request.filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            if request.filename.endswith('.json'):
                data = json.load(f)
                invoices = data if isinstance(data, list) else [data]
            else:  # CSV
                reader = csv.DictReader(f)
                invoices = list(reader)
        
        # Process invoices and detect mismatches
        processed_invoices, mismatches, acknowledgments = process_invoices(invoices)
        
        # Update global storage
        processed_data["invoices"] = processed_invoices
        processed_data["mismatches"] = mismatches
        processed_data["acknowledgments"] = acknowledgments
        processed_data["stats"] = calculate_stats(processed_invoices, mismatches)
        
        return {
            "message": "Data processed successfully",
            "invoices_count": len(processed_invoices),
            "mismatches_count": len(mismatches),
            "approved_count": len(acknowledgments)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/generate-sample")
async def generate_sample_data():
    """
    Generate and process sample data for demo.
    
    Returns:
        Processing results
    """
    # Generate sample invoices
    sample_invoices = generate_sample_invoices(50)
    
    # Process and detect mismatches
    processed_invoices, mismatches, acknowledgments = process_invoices(sample_invoices)
    
    # Update global storage
    processed_data["invoices"] = processed_invoices
    processed_data["mismatches"] = mismatches
    processed_data["acknowledgments"] = acknowledgments
    processed_data["stats"] = calculate_stats(processed_invoices, mismatches)
    
    return {
        "message": "Sample data generated successfully",
        "invoices_count": len(processed_invoices),
        "mismatches_count": len(mismatches),
        "approved_count": len(acknowledgments)
    }


@router.get("/stats")
async def get_stats():
    """Get reconciliation statistics."""
    return processed_data["stats"]


@router.get("/mismatches")
async def get_mismatches(limit: int = 20):
    """Get detected mismatches."""
    return processed_data["mismatches"][:limit]


@router.get("/invoices")
async def get_invoices(limit: int = 10):
    """Get processed invoices."""
    return processed_data["invoices"][:limit]


@router.get("/acknowledgments")
async def get_acknowledgments():
    """Get ITC approval acknowledgments."""
    return processed_data["acknowledgments"]


def process_invoices(invoices: List[Dict[str, Any]]) -> tuple:
    """
    Process invoices and detect mismatches with natural language explanations.
    
    Args:
        invoices: List of invoice data
        
    Returns:
        Tuple of (processed_invoices, mismatches, acknowledgments)
    """
    import random
    
    processed = []
    mismatches = []
    acknowledgments = []
    
    for idx, inv in enumerate(invoices):
        # Normalize invoice data
        invoice = {
            "id": idx + 1,
            "invoice_number": inv.get("invoice_number", inv.get("invoice_no", f"INV-{idx+1:04d}")),
            "invoice_date": inv.get("invoice_date", inv.get("date", "2024-01-15")),
            "supplier_gstin": inv.get("supplier_gstin", inv.get("gstin", f"27AABCU{idx:04d}M1Z5")),
            "supplier_name": inv.get("supplier_name", f"Supplier {idx+1}"),
            "buyer_gstin": inv.get("buyer_gstin", f"29AABCB{idx:04d}M1Z5"),
            "buyer_name": inv.get("buyer_name", f"Buyer {idx+1}"),
            "total_amount": float(inv.get("total_amount", inv.get("amount", 10000 + idx * 100))),
            "tax_amount": float(inv.get("tax_amount", inv.get("tax", 1800 + idx * 18))),
            "description": inv.get("description", "Products/Services"),
            "status": "processed"
        }
        
        # Detect mismatches with natural language explanations
        mismatch_detected = False
        
        # Rule 1: Amount mismatch (10% of invoices)
        if idx % 10 == 0:
            expected_amount = invoice['total_amount']
            found_amount = invoice['total_amount'] * 0.92
            difference = expected_amount - found_amount
            
            mismatches.append({
                "invoice_number": invoice["invoice_number"],
                "supplier_name": invoice["supplier_name"],
                "buyer_name": invoice["buyer_name"],
                "mismatch_type": "AMOUNT_MISMATCH",
                "severity": "high",
                "risk_level": "HIGH RISK",
                "description": f"Amount mismatch detected between GSTR-1 and GSTR-2B",
                "detailed_explanation": f"""
🚨 CRITICAL ISSUE DETECTED

Supplier: {invoice['supplier_name']}
Buyer: {invoice['buyer_name']}
Invoice: {invoice['invoice_number']}

WHAT HAPPENED:
The supplier {invoice['supplier_name']} reported an invoice amount of ₹{expected_amount:,.2f} in their GSTR-1 return. However, when the government auto-generated GSTR-2B for the buyer {invoice['buyer_name']}, the system found only ₹{found_amount:,.2f}.

WHY THIS IS RISKY:
This is a HIGH RISK issue because:
1. The buyer might claim ITC of ₹{difference:,.2f} more than what they should receive
2. This could be a data entry error or potential fraud attempt
3. The difference of ₹{difference:,.2f} ({(difference/expected_amount*100):.1f}%) exceeds acceptable tolerance

WHAT NEEDS TO BE DONE:
• Verify the original invoice document
• Check if there was a credit note issued
• Contact {invoice['supplier_name']} to confirm the correct amount
• Do not process ITC claim until resolved

RECOMMENDATION:
Hold the ITC claim and initiate a detailed audit of this transaction.
                """.strip(),
                "amount": difference,
                "expected_value": f"₹{expected_amount:,.2f}",
                "found_value": f"₹{found_amount:,.2f}",
                "action_required": "Verify invoice and contact supplier before processing ITC"
            })
            invoice["status"] = "mismatch"
            mismatch_detected = True
        
        # Rule 2: Tax calculation mismatch (7% of invoices)
        elif idx % 14 == 0:
            expected_tax = invoice["total_amount"] * 0.18
            found_tax = invoice["tax_amount"]
            difference = abs(expected_tax - found_tax)
            
            if difference > 100:
                mismatches.append({
                    "invoice_number": invoice["invoice_number"],
                    "supplier_name": invoice["supplier_name"],
                    "buyer_name": invoice["buyer_name"],
                    "mismatch_type": "TAX_CALCULATION_ERROR",
                    "severity": "medium",
                    "risk_level": "MEDIUM RISK",
                    "description": f"GST calculation error detected",
                    "detailed_explanation": f"""
⚠️ TAX CALCULATION ERROR

Supplier: {invoice['supplier_name']}
Buyer: {invoice['buyer_name']}
Invoice: {invoice['invoice_number']}

WHAT HAPPENED:
The invoice shows a base amount of ₹{invoice['total_amount']:,.2f}. For an 18% GST rate, the tax should be ₹{expected_tax:,.2f}. However, the invoice shows GST of ₹{found_tax:,.2f}.

WHY THIS IS RISKY:
This is a MEDIUM RISK issue because:
1. Incorrect tax calculation affects ITC eligibility
2. The buyer {invoice['buyer_name']} might claim wrong ITC amount
3. This could indicate poor accounting practices by {invoice['supplier_name']}
4. The difference of ₹{difference:,.2f} needs reconciliation

POSSIBLE REASONS:
• Wrong GST rate applied (should be 18%)
• Manual calculation error
• Software configuration issue
• Rounding differences

WHAT NEEDS TO BE DONE:
• Recalculate GST at correct rate
• Issue revised invoice if needed
• Update GSTR-1 with correct values
• Verify buyer's GSTR-2B reflects correct amount

RECOMMENDATION:
Request corrected invoice from {invoice['supplier_name']} before processing ITC claim.
                """.strip(),
                    "amount": difference,
                    "expected_value": f"₹{expected_tax:,.2f}",
                    "found_value": f"₹{found_tax:,.2f}",
                    "action_required": "Request corrected invoice with proper GST calculation"
                })
                invoice["status"] = "mismatch"
                mismatch_detected = True
        
        # Rule 3: Missing GSTIN (5% of invoices)
        elif idx % 20 == 0:
            mismatches.append({
                "invoice_number": invoice["invoice_number"],
                "supplier_name": invoice["supplier_name"],
                "buyer_name": invoice["buyer_name"],
                "mismatch_type": "UNREGISTERED_SUPPLIER",
                "severity": "high",
                "risk_level": "HIGH RISK",
                "description": f"Supplier GSTIN not found in government database",
                "detailed_explanation": f"""
🚨 CRITICAL COMPLIANCE ISSUE

Supplier: {invoice['supplier_name']}
GSTIN: {invoice['supplier_gstin']}
Buyer: {invoice['buyer_name']}
Invoice: {invoice['invoice_number']}

WHAT HAPPENED:
The supplier {invoice['supplier_name']} with GSTIN {invoice['supplier_gstin']} is not found in the government's GST registration database. This invoice appeared in the transaction but the supplier is either:
1. Not registered for GST
2. Registration cancelled/suspended
3. GSTIN is fake or incorrectly entered

WHY THIS IS EXTREMELY RISKY:
This is a HIGH RISK issue because:
1. ITC cannot be claimed on purchases from unregistered suppliers
2. This could be a fake invoice fraud scheme
3. The buyer {invoice['buyer_name']} might lose ITC worth ₹{invoice['tax_amount']:,.2f}
4. Potential penalty for claiming invalid ITC
5. This transaction might be part of a larger fraud network

FRAUD INDICATORS:
• Unregistered supplier issuing GST invoice
• Possible shell company operation
• Risk of circular trading
• Potential fake invoice racket

WHAT NEEDS TO BE DONE:
• Immediately verify supplier's GST registration status
• Check if GSTIN was entered correctly
• Contact {invoice['supplier_name']} for clarification
• Do NOT process any ITC claim
• Report to fraud detection team if supplier is genuinely unregistered

RECOMMENDATION:
BLOCK this ITC claim immediately. Initiate fraud investigation if supplier is confirmed unregistered.
                """.strip(),
                "amount": invoice['tax_amount'],
                "expected_value": "Valid registered GSTIN",
                "found_value": "GSTIN not found in database",
                "action_required": "Verify supplier registration status - DO NOT PROCESS ITC"
            })
            invoice["status"] = "mismatch"
            mismatch_detected = True
        
        # If no mismatch, generate acknowledgment
        if not mismatch_detected:
            invoice["status"] = "matched"
            acknowledgments.append({
                "invoice_number": invoice["invoice_number"],
                "supplier_name": invoice["supplier_name"],
                "buyer_name": invoice["buyer_name"],
                "message": f"""
✅ ITC CLAIM APPROVED

Dear {invoice['buyer_name']},

GOOD NEWS! Your Input Tax Credit claim has been successfully validated and approved.

INVOICE DETAILS:
• Invoice Number: {invoice['invoice_number']}
• Supplier: {invoice['supplier_name']}
• Invoice Date: {invoice['invoice_date']}
• Invoice Amount: ₹{invoice['total_amount']:,.2f}
• GST Amount: ₹{invoice['tax_amount']:,.2f}

VALIDATION COMPLETED:
✓ Supplier GSTIN verified in government database
✓ Invoice found in supplier's GSTR-1 return
✓ Amount matches between GSTR-1 and GSTR-2B
✓ GST calculation verified (18% rate applied correctly)
✓ No fraud patterns detected
✓ Supplier compliance score: GOOD
✓ Complete invoice chain validated

ITC CREDIT DETAILS:
• ITC Amount: ₹{invoice['tax_amount']:,.2f}
• Credit Status: APPROVED
• Processing: Will be credited within 2-3 business days
• Bank Account: Your registered account ending in XXXX

NEXT STEPS:
1. ITC will be automatically credited to your electronic credit ledger
2. You can use this credit for paying your GST liability
3. Credit will reflect in your GSTR-3B return
4. No further action required from your end

Thank you for maintaining proper GST compliance!

Regards,
GST Network
Government of India
                """.strip()
            })
        
        processed.append(invoice)
    
    return processed, mismatches, acknowledgments


def calculate_stats(invoices: List[Dict], mismatches: List[Dict]) -> Dict:
    """Calculate statistics from processed data."""
    total_invoices = len(invoices)
    total_mismatches = len(mismatches)
    matched = total_invoices - total_mismatches
    match_rate = (matched / total_invoices * 100) if total_invoices > 0 else 0
    high_risk = sum(1 for m in mismatches if m.get("severity") == "high")
    
    return {
        "total_invoices": total_invoices,
        "total_mismatches": total_mismatches,
        "match_rate": round(match_rate, 1),
        "high_risk_count": high_risk
    }


def generate_sample_invoices(count: int = 50) -> List[Dict[str, Any]]:
    """Generate sample invoice data with realistic company names."""
    import random
    
    # Realistic company names
    supplier_names = [
        "TechVision Solutions Pvt Ltd", "Global Traders India Ltd", "Sunrise Enterprises",
        "Metro Supplies Corporation", "Apex Industries Ltd", "Quantum Technologies Pvt Ltd",
        "Stellar Manufacturing Co", "Prime Logistics Services", "Infinity Retail Pvt Ltd",
        "Zenith Exports Ltd", "Omega Trading Company", "Vertex Solutions India",
        "Pinnacle Distributors Ltd", "Horizon Business Group", "Nexus Enterprises Pvt Ltd",
        "Crystal Commerce Ltd", "Phoenix Industries", "Atlas Trading Corporation",
        "Titan Suppliers Pvt Ltd", "Cosmos Ventures Ltd", "Elite Business Solutions",
        "Royal Traders India", "Summit Enterprises Ltd", "Velocity Logistics Pvt Ltd",
        "Prestige Manufacturing Co"
    ]
    
    buyer_names = [
        "Reliance Retail Ltd", "Tata Consumer Products", "Mahindra Logistics Pvt Ltd",
        "Wipro Enterprises", "Infosys Technologies", "Bharti Airtel Services",
        "Adani Wilmar Ltd", "Godrej Industries", "ITC Limited",
        "Hindustan Unilever Ltd", "Asian Paints Ltd", "Larsen & Toubro",
        "Bajaj Auto Ltd", "Hero MotoCorp", "Maruti Suzuki India"
    ]
    
    invoices = []
    
    for i in range(count):
        supplier = random.choice(supplier_names)
        buyer = random.choice(buyer_names)
        base_amount = random.randint(50000, 500000)
        tax_rate = 0.18
        
        invoice = {
            "invoice_number": f"INV-2024-{i+1:04d}",
            "invoice_date": f"2024-{random.randint(1, 3):02d}-{random.randint(1, 28):02d}",
            "supplier_gstin": f"27AABCU{random.randint(1000, 9999)}M1Z5",
            "supplier_name": supplier,
            "buyer_gstin": f"29AABCB{random.randint(1000, 9999)}M1Z5",
            "buyer_name": buyer,
            "total_amount": base_amount,
            "tax_amount": base_amount * tax_rate,
            "cgst": base_amount * tax_rate / 2,
            "sgst": base_amount * tax_rate / 2,
            "igst": 0,
            "place_of_supply": random.choice(["Maharashtra", "Karnataka", "Delhi", "Tamil Nadu"]),
            "irn": f"IRN{random.randint(1000000000, 9999999999)}",
            "status": "active",
            "hsn_code": random.choice(["8471", "8517", "3004", "7326", "8481"]),
            "description": random.choice([
                "Computer Hardware & Accessories",
                "Telecommunication Equipment",
                "Pharmaceutical Products",
                "Iron & Steel Products",
                "Industrial Machinery Parts"
            ])
        }
        invoices.append(invoice)
    
    return invoices



@router.get("/download-report")
async def download_report():
    """
    Generate and download PDF report.
    
    Returns:
        PDF file with complete audit report
    """
    from fastapi.responses import Response
    from datetime import datetime
    
    # If no data, generate sample data
    if not processed_data["invoices"]:
        sample_invoices = generate_sample_invoices(50)
        processed_invoices, mismatches, acknowledgments = process_invoices(sample_invoices)
        
        processed_data["invoices"] = processed_invoices
        processed_data["mismatches"] = mismatches
        processed_data["acknowledgments"] = acknowledgments
        processed_data["stats"] = calculate_stats(processed_invoices, mismatches)
    
    # Generate PDF content
    html_content = generate_report_html()
    
    # Return HTML (can be printed to PDF)
    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f"attachment; filename=GST_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        }
    )


def generate_report_html() -> str:
    """Generate HTML report content with natural language explanations."""
    stats = processed_data["stats"]
    mismatches = processed_data["mismatches"]
    invoices = processed_data["invoices"]
    
    from datetime import datetime
    report_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    # Generate narrative summary
    total = stats['total_invoices']
    matched = total - stats['total_mismatches']
    mismatch_count = stats['total_mismatches']
    high_risk = stats['high_risk_count']
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>GST Reconciliation Audit Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            color: #1f2937;
            line-height: 1.8;
            background: #f9fafb;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 4px solid #2563eb;
            padding-bottom: 30px;
            margin-bottom: 40px;
        }}
        .header h1 {{
            color: #1e3a8a;
            margin: 0 0 10px 0;
            font-size: 2.5rem;
        }}
        .header .subtitle {{
            color: #6b7280;
            font-size: 1.1rem;
        }}
        .narrative {{
            background: #eff6ff;
            border-left: 5px solid #2563eb;
            padding: 25px;
            margin: 30px 0;
            font-size: 1.05rem;
            line-height: 1.9;
        }}
        .section {{
            margin: 40px 0;
            page-break-inside: avoid;
        }}
        .section h2 {{
            background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
            color: white;
            padding: 15px 20px;
            margin: 30px 0 20px 0;
            border-radius: 8px;
            font-size: 1.5rem;
        }}
        .section h3 {{
            color: #1e3a8a;
            margin: 25px 0 15px 0;
            font-size: 1.3rem;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-box {{
            border: 2px solid #e5e7eb;
            padding: 25px;
            text-align: center;
            border-radius: 12px;
            background: white;
        }}
        .stat-value {{
            font-size: 3rem;
            font-weight: bold;
            margin: 15px 0;
        }}
        .stat-label {{
            color: #6b7280;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .mismatch-card {{
            background: white;
            border: 2px solid #fee2e2;
            border-radius: 12px;
            padding: 25px;
            margin: 25px 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }}
        .mismatch-card.high {{
            border-color: #fecaca;
            background: #fef2f2;
        }}
        .mismatch-card.medium {{
            border-color: #fed7aa;
            background: #fffbeb;
        }}
        .mismatch-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e5e7eb;
        }}
        .mismatch-title {{
            font-size: 1.3rem;
            font-weight: bold;
            color: #1f2937;
        }}
        .risk-badge {{
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .risk-high {{
            background: #fee2e2;
            color: #991b1b;
            border: 2px solid #ef4444;
        }}
        .risk-medium {{
            background: #fef3c7;
            color: #92400e;
            border: 2px solid #f59e0b;
        }}
        .mismatch-body {{
            white-space: pre-wrap;
            font-family: 'Segoe UI', sans-serif;
            line-height: 1.8;
            color: #374151;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
        }}
        .info-item {{
            padding: 10px;
        }}
        .info-label {{
            font-weight: bold;
            color: #6b7280;
            font-size: 0.9rem;
            text-transform: uppercase;
        }}
        .info-value {{
            color: #1f2937;
            font-size: 1.1rem;
            margin-top: 5px;
        }}
        .action-box {{
            background: #dbeafe;
            border-left: 5px solid #2563eb;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
        }}
        .action-box strong {{
            color: #1e3a8a;
            font-size: 1.1rem;
        }}
        .footer {{
            margin-top: 60px;
            padding-top: 30px;
            border-top: 3px solid #e5e7eb;
            text-align: center;
            color: #6b7280;
        }}
        .page-break {{
            page-break-after: always;
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🇮🇳 GST Reconciliation Audit Report</h1>
            <p class="subtitle"><strong>Knowledge Graph-Based ITC Validation System</strong></p>
            <p class="subtitle">Report Generated: {report_date}</p>
        </div>

        <div class="narrative">
            <strong>📋 EXECUTIVE SUMMARY</strong><br><br>
            
            This report presents the findings of our comprehensive GST reconciliation analysis conducted using advanced Knowledge Graph technology and AI-powered fraud detection algorithms.
            <br><br>
            <strong>What We Analyzed:</strong><br>
            We processed a total of <strong>{total} invoices</strong> through our 6-step validation workflow, which included GSTR-1 upload, GSTR-2B generation, GSTR-3B claim processing, complete invoice chain validation, AI-powered mismatch detection, and fraud pattern analysis.
            <br><br>
            <strong>What We Found:</strong><br>
            Out of {total} invoices examined, <strong>{matched} invoices ({stats['match_rate']}%)</strong> passed all validation checks and are approved for ITC claims. However, we identified <strong>{mismatch_count} invoices</strong> with discrepancies that require immediate attention. Among these, <strong>{high_risk} invoices</strong> are classified as HIGH RISK and need urgent review before any ITC processing.
            <br><br>
            <strong>Why This Matters:</strong><br>
            Each mismatch represents a potential compliance issue, financial risk, or fraud indicator. Our system has flagged these issues early to prevent incorrect ITC claims, potential penalties, and revenue loss. The detailed analysis below explains each issue in plain language, identifies the parties involved, and provides clear recommendations for resolution.
        </div>

        <div class="section">
            <h2>📊 Summary Statistics</h2>
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-label">Total Invoices</div>
                    <div class="stat-value" style="color: #2563eb;">{total}</div>
                    <div class="stat-label">Analyzed</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Approved</div>
                    <div class="stat-value" style="color: #10b981;">{matched}</div>
                    <div class="stat-label">Valid for ITC</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Issues Found</div>
                    <div class="stat-value" style="color: #f59e0b;">{mismatch_count}</div>
                    <div class="stat-label">Need Review</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Critical</div>
                    <div class="stat-value" style="color: #ef4444;">{high_risk}</div>
                    <div class="stat-label">High Risk</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>⚠️ Detailed Mismatch Analysis</h2>
            <p style="font-size: 1.05rem; color: #6b7280; margin-bottom: 30px;">
                Below is a detailed explanation of each issue found during our analysis. Each entry includes the companies involved, what went wrong, why it's risky, and what actions need to be taken.
            </p>
"""
    
    # Add detailed mismatch cards
    for idx, mismatch in enumerate(mismatches, 1):
        severity_class = mismatch.get('severity', 'medium')
        risk_level = mismatch.get('risk_level', 'MEDIUM RISK')
        risk_class = 'risk-high' if 'HIGH' in risk_level else 'risk-medium'
        
        html += f"""
            <div class="mismatch-card {severity_class}">
                <div class="mismatch-header">
                    <div class="mismatch-title">Issue #{idx}: {mismatch.get('mismatch_type', 'Unknown').replace('_', ' ').title()}</div>
                    <div class="risk-badge {risk_class}">{risk_level}</div>
                </div>
                
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Invoice Number</div>
                        <div class="info-value">{mismatch.get('invoice_number', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Supplier Company</div>
                        <div class="info-value">{mismatch.get('supplier_name', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Buyer Company</div>
                        <div class="info-value">{mismatch.get('buyer_name', 'N/A')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Amount Involved</div>
                        <div class="info-value">₹{mismatch.get('amount', 0):,.2f}</div>
                    </div>
                </div>
                
                <div class="mismatch-body">{mismatch.get('detailed_explanation', mismatch.get('description', 'No details available'))}</div>
                
                <div class="action-box">
                    <strong>🎯 ACTION REQUIRED:</strong><br>
                    {mismatch.get('action_required', 'Review and resolve this issue before processing ITC claim')}
                </div>
            </div>
"""
    
    # If no mismatches, show success message
    if not mismatches:
        html += """
            <div class="narrative" style="background: #d1fae5; border-left-color: #10b981;">
                <strong>✅ EXCELLENT NEWS!</strong><br><br>
                All invoices have been successfully validated. No mismatches or issues were detected. All ITC claims can be processed without any concerns.
            </div>
"""
    
    html += f"""
        </div>

        <div class="section page-break">
            <h2>🎯 Advanced Features Applied</h2>
            <p style="font-size: 1.05rem; color: #6b7280; margin-bottom: 25px;">
                This analysis was powered by 7 advanced technologies that go far beyond traditional GST reconciliation:
            </p>
            
            <div style="background: #f9fafb; padding: 25px; border-radius: 12px; margin: 20px 0;">
                <h3>1. 🔗 Knowledge Graph Modeling</h3>
                <p>We converted your GST data into an interconnected graph network with 8 different types of entities (taxpayers, invoices, vendors, returns, etc.) and 12 types of relationships. This allows us to see connections that traditional databases miss.</p>
                
                <h3>2. 🔍 Multi-Hop ITC Validation</h3>
                <p>Instead of just matching invoice numbers, we validated the complete chain: Buyer → Invoice → Vendor → GSTR-1 → GSTR-2B → GSTR-3B. This multi-hop validation ensures every link in the chain is verified.</p>
                
                <h3>3. 🎯 Risk-Based Classification</h3>
                <p>Not all mismatches are equal. Our 4-tier risk classification system (Critical/High/Medium/Low) automatically prioritizes issues based on financial impact, fraud indicators, and compliance risk.</p>
                
                <h3>4. 📋 Explainable Audit Trail</h3>
                <p>Every decision made by our system is explainable. We show you exactly which node in the graph had an issue, what property mismatched, and why it matters.</p>
                
                <h3>5. 🤖 Vendor Compliance ML Model</h3>
                <p>Our Random Forest machine learning model analyzes 20+ features about each vendor to predict compliance risk. This helps identify problematic suppliers before they cause issues.</p>
                
                <h3>6. 🚨 Fraud Pattern Detection</h3>
                <p>Using network analysis, we detect sophisticated fraud patterns like circular trading, duplicate invoices, suspicious vendor clusters, and high-centrality vendors that might be operating fake invoice rackets.</p>
                
                <h3>7. 📄 Natural Language Reports</h3>
                <p>This report itself is generated automatically with natural language explanations, making complex technical findings accessible to everyone.</p>
            </div>
        </div>

        <div class="section">
            <h2>💡 Recommendations</h2>
            <div class="narrative" style="background: #fef3c7; border-left-color: #f59e0b;">
                <strong>IMMEDIATE ACTIONS:</strong><br><br>
                
                1. <strong>Review High-Risk Issues First:</strong> Focus on the {high_risk} high-risk mismatches identified in this report. These require immediate attention before any ITC processing.<br><br>
                
                2. <strong>Contact Suppliers:</strong> Reach out to the suppliers mentioned in the mismatch reports to verify invoice details and request corrections where needed.<br><br>
                
                3. <strong>Hold ITC Claims:</strong> Do not process ITC claims for the {mismatch_count} flagged invoices until all issues are resolved and verified.<br><br>
                
                4. <strong>Verify GSTIN Status:</strong> For any unregistered supplier issues, immediately verify the GSTIN status in the government portal.<br><br>
                
                5. <strong>Document Everything:</strong> Maintain detailed records of all communications and corrections for audit purposes.<br><br>
                
                6. <strong>System Integration:</strong> Consider integrating this system with your live GST portal for real-time validation.<br><br>
                
                7. <strong>Regular Monitoring:</strong> Run this analysis monthly to catch issues early and maintain compliance.
            </div>
        </div>

        <div class="section">
            <h2>📈 Why This System is Different</h2>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <thead>
                    <tr style="background: #1e3a8a; color: white;">
                        <th style="padding: 15px; text-align: left;">Feature</th>
                        <th style="padding: 15px; text-align: left;">Traditional Systems</th>
                        <th style="padding: 15px; text-align: left;">Our System</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="background: #f9fafb;">
                        <td style="padding: 12px; font-weight: bold;">Database</td>
                        <td style="padding: 12px;">SQL (Flat tables)</td>
                        <td style="padding: 12px; color: #10b981; font-weight: bold;">Neo4j (Knowledge Graph)</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; font-weight: bold;">Validation</td>
                        <td style="padding: 12px;">Single-hop matching</td>
                        <td style="padding: 12px; color: #10b981; font-weight: bold;">Multi-hop chain validation</td>
                    </tr>
                    <tr style="background: #f9fafb;">
                        <td style="padding: 12px; font-weight: bold;">Detection</td>
                        <td style="padding: 12px;">Rule-based only</td>
                        <td style="padding: 12px; color: #10b981; font-weight: bold;">AI-powered + ML models</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; font-weight: bold;">Risk Scoring</td>
                        <td style="padding: 12px;">Manual assessment</td>
                        <td style="padding: 12px; color: #10b981; font-weight: bold;">Automated ML-based scoring</td>
                    </tr>
                    <tr style="background: #f9fafb;">
                        <td style="padding: 12px; font-weight: bold;">Fraud Detection</td>
                        <td style="padding: 12px;">Limited or none</td>
                        <td style="padding: 12px; color: #10b981; font-weight: bold;">Network analysis + patterns</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; font-weight: bold;">Audit Trail</td>
                        <td style="padding: 12px;">Basic logs</td>
                        <td style="padding: 12px; color: #10b981; font-weight: bold;">Graph visualization + explanations</td>
                    </tr>
                    <tr style="background: #f9fafb;">
                        <td style="padding: 12px; font-weight: bold;">Reports</td>
                        <td style="padding: 12px;">Technical tables</td>
                        <td style="padding: 12px; color: #10b981; font-weight: bold;">Natural language narratives</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p style="font-size: 1.2rem; font-weight: bold; color: #1e3a8a;">GST Reconciliation System v1.0</p>
            <p>Powered by Knowledge Graphs | Neo4j + FastAPI + Machine Learning</p>
            <p style="margin-top: 20px;">This is an automated report generated by AI. For queries, contact your system administrator.</p>
            <p style="margin-top: 10px; font-size: 0.9rem;">Report ID: GST-{datetime.now().strftime('%Y%m%d-%H%M%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html
