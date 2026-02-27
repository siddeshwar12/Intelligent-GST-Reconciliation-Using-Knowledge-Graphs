"""Knowledge base for GST Reconciliation Chatbot."""

KNOWLEDGE_BASE = {
    "gst_basics": {
        "what is gst": "GST (Goods and Services Tax) is an indirect tax levied on the supply of goods and services in India. It replaced multiple indirect taxes.",
        "what is itc": "ITC (Input Tax Credit) means that a business can reduce the tax it has paid on purchases from the tax it collects on sales. This prevents double taxation.",
        "what is gstr-1": "GSTR-1 is a monthly return filed by registered sellers containing details of all outward supplies (sales) made during the month.",
        "what is gstr-2b": "GSTR-2B is an auto-generated statement by the government showing all purchases made by a buyer based on GSTR-1 filed by their suppliers. Buyers cannot modify this document.",
        "what is gstr-3b": "GSTR-3B is a monthly summary return where businesses declare their sales, purchases, and the tax payable. This is where buyers claim their Input Tax Credit (ITC).",
        "what is gstin": "GSTIN (Goods and Services Tax Identification Number) is a unique 15-digit identification number assigned to every GST registered business.",
    },
    
    "system_features": {
        "what does this system do": "This GST Reconciliation System validates Input Tax Credit (ITC) claims by matching data across GSTR-1, GSTR-2B, and GSTR-3B returns. It uses Knowledge Graphs and AI to detect mismatches and fraud patterns.",
        "what is knowledge graph": "A Knowledge Graph is a network database that stores GST data as interconnected nodes (taxpayers, invoices, vendors) and relationships. This allows us to trace complete invoice chains and detect patterns that traditional databases miss.",
        "what are the 7 advanced features": "1. Knowledge Graph Modeling (Neo4j), 2. Multi-Hop ITC Validation, 3. Risk-Based Classification, 4. Explainable Audit Trail, 5. Vendor Compliance ML Model, 6. Fraud Pattern Detection, 7. Natural Language Reports",
        "how does multi-hop validation work": "Instead of just matching invoice numbers, we validate the complete chain: Buyer → Invoice → Vendor → GSTR-1 → GSTR-2B → GSTR-3B. Every link in the chain is verified.",
        "what is risk classification": "Our system classifies mismatches into 4 tiers: Critical (>20% difference), High (10-20%), Medium (5-10%), Low (<5%). This helps prioritize which issues need immediate attention.",
    },
    
    "mismatches": {
        "what is a mismatch": "A mismatch occurs when the tax amount in GSTR-1 (seller's filing) doesn't match GSTR-2B (government statement) or GSTR-3B (buyer's claim). This could indicate errors, fraud, or compliance issues.",
        "types of mismatches": "Common types include: Amount Mismatch (tax amounts don't match), Invoice Not Found (invoice missing in government records), Unregistered Supplier (GSTIN not valid), Date Mismatch (filing dates don't align), Payment Not Verified (tax payment not confirmed).",
        "what causes mismatches": "Mismatches can be caused by: calculation errors, delayed filings, fraudulent invoices, unregistered suppliers, data entry mistakes, or intentional tax evasion.",
        "how to fix mismatches": "1. Contact the supplier to verify invoice details, 2. Request correction in their next GSTR-1 filing, 3. Verify GSTIN status on government portal, 4. Hold ITC claim until resolved, 5. Document all communications for audit.",
    },
    
    "reports": {
        "what is in the report": "The PDF report includes: Executive Summary, Statistics (total invoices, approved, mismatches, high risk), Detailed Mismatch Analysis with company names, Natural Language Explanations, Risk Assessment, Recommendations, and Advanced Features Documentation.",
        "how to download report": "Go to the Results page and click the 'Download PDF Report' button. The report will download as an HTML file that you can open in any browser or print to PDF.",
        "what is natural language report": "Instead of technical jargon, our reports explain issues in simple English. For example: 'TechCorp filed ₹1,800 tax but GSTR-2B shows only ₹1,584 - a 12% mismatch' rather than just showing numbers.",
    },
    
    "workflow": {
        "what is the workflow": "The 5-step workflow is: 1. Seller files GSTR-1, 2. Government generates GSTR-2B, 3. Buyer claims ITC in GSTR-3B, 4. Our AI validates the complete chain, 5. System generates approval report.",
        "how long does validation take": "Validation is instant for uploaded data. The system processes 50 invoices in under 2 seconds. For larger datasets (1000+ invoices), it takes about 10-15 seconds.",
        "can i upload my own data": "Yes! Go to the Upload page and either drag-drop your CSV/JSON files or click 'Browse Files'. You can also generate sample data for testing (50, 200, 500, or 1000 invoices).",
    },
    
    "fraud_detection": {
        "how does fraud detection work": "Our system uses network analysis to detect: circular trading (companies trading with each other in loops), duplicate invoices, suspicious vendor clusters, high-centrality vendors (potential fake invoice rackets), and unusual transaction patterns.",
        "what is circular trading": "Circular trading is when companies create fake transactions in a loop (A→B→C→A) to generate fake ITC claims without actual goods/services being exchanged. Our graph database can detect these patterns.",
        "what is vendor risk score": "Our Random Forest ML model analyzes 20+ features about each vendor (filing history, transaction patterns, compliance record) to predict risk. Scores range from 0-100, with higher scores indicating higher risk.",
    },
    
    "technical": {
        "what technology is used": "Backend: Python + FastAPI, Database: Neo4j (Knowledge Graph), ML: scikit-learn (Random Forest), Frontend: HTML/CSS/JavaScript, Caching: Redis (optional), Deployment: Docker",
        "what is neo4j": "Neo4j is a graph database that stores data as nodes and relationships instead of tables. Perfect for GST data because it can trace invoice chains and detect fraud patterns that SQL databases cannot.",
        "can this work without neo4j": "Yes! The system works in 'limited mode' without Neo4j, using in-memory storage. However, you'll miss advanced features like fraud network detection and multi-hop validation.",
        "how to integrate with live gst portal": "You can integrate via API by: 1. Fetching GSTR data from GST portal API, 2. Converting to our format, 3. Processing through our system, 4. Sending results back. Contact your system administrator for API keys.",
    },
    
    "usage": {
        "how to use this system": "1. Go to Upload page, 2. Upload your invoice data (CSV/JSON) or generate sample data, 3. System automatically processes and detects mismatches, 4. View results on Results page, 5. Download comprehensive PDF report.",
        "what file formats are supported": "CSV and JSON formats. CSV should have columns: invoice_number, vendor_gstin, buyer_gstin, amount, tax_amount, date. JSON should be an array of invoice objects.",
        "what is the file size limit": "Maximum file size is 50MB. This can handle approximately 100,000 invoices. For larger datasets, split into multiple files.",
        "how often should i run this": "Run monthly after GSTR-3B filing deadline to catch issues early. For high-volume businesses, consider weekly runs to maintain compliance.",
    },
    
    "troubleshooting": {
        "report not downloading": "Make sure you have data uploaded or generated. The system automatically generates sample data if none exists. Check your browser's download settings.",
        "no mismatches found": "This is good news! It means all invoices passed validation. The report will show 100% approval rate with detailed statistics.",
        "high risk count is high": "Review the detailed mismatch analysis in the report. Contact suppliers for high-risk invoices immediately. Do not process ITC claims until resolved.",
        "system is slow": "For large datasets (1000+ invoices), processing may take 10-15 seconds. Consider using Redis caching and Neo4j indexes for better performance.",
    }
}

def get_answer(question: str) -> str:
    """Get answer from knowledge base using keyword matching."""
    question_lower = question.lower().strip()
    
    # Direct keyword matching
    for category, qa_pairs in KNOWLEDGE_BASE.items():
        for key, answer in qa_pairs.items():
            if key in question_lower or any(word in question_lower for word in key.split()):
                return answer
    
    # Fuzzy matching for common variations
    keywords_map = {
        "help": "I can help you with questions about GST reconciliation, ITC validation, mismatches, reports, workflow, fraud detection, and system usage. Try asking: 'What is ITC?', 'How does this system work?', 'What are mismatches?', 'How to download report?'",
        "hello": "Hello! I'm your GST Reconciliation Assistant. I can answer questions about ITC validation, mismatches, reports, and how to use this system. What would you like to know?",
        "hi": "Hi there! I'm here to help with your GST reconciliation queries. Ask me anything about ITC, GSTR returns, mismatches, or how to use this system.",
        "thanks": "You're welcome! Feel free to ask if you have more questions about GST reconciliation.",
        "thank": "Happy to help! Let me know if you need anything else.",
    }
    
    for keyword, response in keywords_map.items():
        if keyword in question_lower:
            return response
    
    # Default response with suggestions
    return """I'm not sure about that specific question. Here are some topics I can help with:

📊 **GST Basics**: What is GST, ITC, GSTR-1, GSTR-2B, GSTR-3B?
🔧 **System Features**: What does this system do? What are the 7 advanced features?
⚠️ **Mismatches**: What are mismatches? How to fix them?
📄 **Reports**: What's in the report? How to download?
🔄 **Workflow**: What is the validation workflow?
🚨 **Fraud Detection**: How does fraud detection work?
💻 **Technical**: What technology is used?
📖 **Usage**: How to use this system?

Try asking a specific question like: "What is ITC?" or "How to download report?" """
