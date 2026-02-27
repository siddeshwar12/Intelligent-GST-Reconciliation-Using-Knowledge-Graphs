"""
Example Cypher Queries for GST Reconciliation
Demonstrates node creation, relationships, and multi-hop ITC traversal
"""

# ============================================================================
# NODE CREATION QUERIES
# ============================================================================

CREATE_TAXPAYER = """
CREATE (t:Taxpayer:Entity {
    id: $id,
    gstin: $gstin,
    legal_name: $legal_name,
    trade_name: $trade_name,
    taxpayer_type: $taxpayer_type,
    registration_date: date($registration_date),
    state_code: $state_code,
    pan: $pan,
    business_type: $business_type,
    is_active: true,
    created_at: datetime(),
    updated_at: datetime()
})
RETURN t
"""

CREATE_GSTIN = """
CREATE (g:GSTIN:Identifier {
    gstin: $gstin,
    state_code: substring($gstin, 0, 2),
    pan: substring($gstin, 2, 10),
    entity_number: substring($gstin, 12, 1),
    checksum: substring($gstin, 14, 1),
    is_valid: true,
    created_at: datetime()
})
RETURN g
"""

CREATE_INVOICE = """
CREATE (i:Invoice:Document {
    id: $id,
    invoice_number: $invoice_number,
    invoice_date: date($invoice_date),
    financial_year: $financial_year,
    
    taxable_value: $taxable_value,
    cgst_amount: $cgst_amount,
    sgst_amount: $sgst_amount,
    igst_amount: $igst_amount,
    cess_amount: $cess_amount,
    total_tax: $total_tax,
    total_amount: $total_amount,
    
    irn: $irn,
    place_of_supply: $place_of_supply,
    reverse_charge: $reverse_charge,
    invoice_type: $invoice_type,
    document_type: $document_type,
    
    source_type: $source_type,
    source_period: $source_period,
    filing_status: $filing_status,
    
    is_matched: false,
    has_mismatch: false,
    itc_eligible: $itc_eligible,
    
    created_at: datetime(),
    updated_at: datetime()
})
RETURN i
"""

CREATE_LINE_ITEM = """
CREATE (l:LineItem:Detail {
    id: $id,
    item_number: $item_number,
    description: $description,
    hsn_code: $hsn_code,
    
    quantity: $quantity,
  