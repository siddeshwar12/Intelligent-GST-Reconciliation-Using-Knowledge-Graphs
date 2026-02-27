"""Core reconciliation engine for GST invoice matching."""

from typing import List, Tuple, Optional
from uuid import UUID, uuid4
from datetime import datetime

from ....domain.entities import Invoice, Mismatch, Taxpayer
from ....domain.enums import MismatchType, RiskLevel, MismatchStatus
from ....domain.value_objects import Amount
from ....infrastructure.graph.repositories import (
    InvoiceRepository,
    TaxpayerRepository,
    MismatchRepository
)
from ....shared.utils import logger
from ....config import settings


class ReconciliationEngine:
    """
    Core reconciliation engine that matches invoices across different sources
    and identifies mismatches.
    """
    
    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        taxpayer_repo: TaxpayerRepository,
        mismatch_repo: MismatchRepository
    ):
        self.invoice_repo = invoice_repo
        self.taxpayer_repo = taxpayer_repo
        self.mismatch_repo = mismatch_repo
        self.amount_tolerance = settings.amount_tolerance_percent
        self.date_tolerance = settings.date_tolerance_days
    
    async def reconcile_taxpayer(
        self,
        taxpayer_id: UUID,
        period: str
    ) -> Tuple[int, List[Mismatch]]:
        """
        Reconcile all invoices for a taxpayer in a given period.
        
        Args:
            taxpayer_id: Taxpayer UUID
            period: Period in format MMYYYY (e.g., "032024")
            
        Returns:
            Tuple of (total_invoices_processed, list_of_mismatches)
        """
        logger.info(f"Starting reconciliation for taxpayer {taxpayer_id}, period {period}")
        
        reconciliation_run_id = uuid4()
        mismatches = []
        processed_count = 0
        
        # Get taxpayer
        taxpayer = await self.taxpayer_repo.get_by_id(taxpayer_id)
        if not taxpayer:
            logger.error(f"Taxpayer {taxpayer_id} not found")
            return 0, []
        
        # Get all purchase register invoices for the period
        purchase_invoices = await self._get_invoices_by_source(
            taxpayer_id, 
            "PURCHASE_REGISTER", 
            period
        )
        
        logger.info(f"Found {len(purchase_invoices)} purchase register invoices")
        
        # For each purchase invoice, try to find matching GSTR-2B entry
        for purchase_inv in purchase_invoices:
            processed_count += 1
            
            # Find potential matches in GSTR-2B
            gstr2b_matches = await self.invoice_repo.find_matching_invoices(
                purchase_inv,
                ["GSTR-2B"]
            )
            
            if not gstr2b_matches:
                # Missing in GSTR-2B - create mismatch
                mismatch = await self._create_missing_mismatch(
                    purchase_inv,
                    taxpayer_id,
                    MismatchType.MISSING_IN_GSTR2B,
                    reconciliation_run_id
                )
                mismatches.append(mismatch)
                logger.warning(f"Invoice {purchase_inv.invoice_number} missing in GSTR-2B")
                continue
            
            # Check if any match is exact
            exact_match = None
            for gstr2b_inv in gstr2b_matches:
                if self._is_exact_match(purchase_inv, gstr2b_inv):
                    exact_match = gstr2b_inv
                    break
            
            if exact_match:
                # Perfect match - create MATCHES relationship
                await self._create_match_relationship(purchase_inv, exact_match)
                logger.debug(f"Exact match found for invoice {purchase_inv.invoice_number}")
            else:
                # Partial match - analyze mismatch
                best_match = gstr2b_matches[0]  # Closest match
                mismatch = await self._analyze_mismatch(
                    purchase_inv,
                    best_match,
                    taxpayer_id,
                    reconciliation_run_id
                )
                if mismatch:
                    mismatches.append(mismatch)
                    logger.warning(
                        f"Mismatch detected for invoice {purchase_inv.invoice_number}: "
                        f"{mismatch.mismatch_type.value}"
                    )
        
        logger.info(
            f"Reconciliation complete: {processed_count} invoices processed, "
            f"{len(mismatches)} mismatches found"
        )
        
        return processed_count, mismatches
    
    async def _get_invoices_by_source(
        self,
        taxpayer_id: UUID,
        source_type: str,
        period: str
    ) -> List[Invoice]:
        """Get invoices by source type and period."""
        # This would use a repository method - simplified for now
        # In real implementation, add this method to InvoiceRepository
        return []
    
    def _is_exact_match(self, inv1: Invoice, inv2: Invoice) -> bool:
        """
        Check if two invoices are an exact match.
        
        Args:
            inv1: First invoice
            inv2: Second invoice
            
        Returns:
            True if exact match
        """
        return (
            inv1.invoice_number == inv2.invoice_number and
            inv1.supplier_gstin == inv2.supplier_gstin and
            inv1.total_amount == inv2.total_amount and
            inv1.invoice_date == inv2.invoice_date
        )
    
    async def _create_match_relationship(
        self,
        inv1: Invoice,
        inv2: Invoice
    ) -> None:
        """Create MATCHES relationship between two invoices."""
        # This would create a relationship in Neo4j
        # Implementation would go in a repository method
        pass
    
    async def _analyze_mismatch(
        self,
        inv1: Invoice,
        inv2: Invoice,
        taxpayer_id: UUID,
        reconciliation_run_id: UUID
    ) -> Optional[Mismatch]:
        """
        Analyze mismatch between two invoices.
        
        Args:
            inv1: First invoice (e.g., from purchase register)
            inv2: Second invoice (e.g., from GSTR-2B)
            taxpayer_id: Taxpayer UUID
            reconciliation_run_id: Reconciliation run UUID
            
        Returns:
            Mismatch entity if mismatch found, None otherwise
        """
        # Determine mismatch type
        mismatch_type = self._determine_mismatch_type(inv1, inv2)
        
        # Calculate amount difference
        amount_diff = inv1.total_amount.subtract(inv2.total_amount)
        variance_percent = abs(inv1.total_amount.variance_percent(inv2.total_amount))
        
        # Determine risk level
        risk_level = RiskLevel.from_amount_variance(float(variance_percent))
        
        # Generate description and root cause
        description = self._generate_mismatch_description(inv1, inv2, mismatch_type)
        root_cause = self._determine_root_cause(inv1, inv2, mismatch_type)
        recommendation = self._generate_recommendation(mismatch_type, risk_level)
        
        # Create mismatch entity
        mismatch = Mismatch(
            id=uuid4(),
            invoice_id_1=inv1.id,
            invoice_id_2=inv2.id,
            taxpayer_id=taxpayer_id,
            mismatch_type=mismatch_type,
            risk_level=risk_level,
            status=MismatchStatus.OPEN,
            amount_difference=Amount.from_float(abs(float(amount_diff.value))),
            tax_impact=inv1.total_tax.subtract(inv2.total_tax),
            itc_impact=inv1.total_tax.subtract(inv2.total_tax),  # Simplified
            description=description,
            root_cause=root_cause,
            recommendation=recommendation,
            reconciliation_run_id=reconciliation_run_id,
            detected_at=datetime.utcnow()
        )
        
        # Save to database
        await self.mismatch_repo.create(mismatch)
        
        return mismatch
    
    async def _create_missing_mismatch(
        self,
        invoice: Invoice,
        taxpayer_id: UUID,
        mismatch_type: MismatchType,
        reconciliation_run_id: UUID
    ) -> Mismatch:
        """
        Create mismatch for missing invoice.
        
        Args:
            invoice: Missing invoice
            taxpayer_id: Taxpayer UUID
            mismatch_type: Type of mismatch
            reconciliation_run_id: Reconciliation run UUID
            
        Returns:
            Created mismatch
        """
        # Missing invoice is always high risk
        risk_level = RiskLevel.HIGH
        
        description = (
            f"Invoice {invoice.invoice_number} dated {invoice.invoice_date.date()} "
            f"for amount {invoice.total_amount} is missing in GSTR-2B"
        )
        
        root_cause = "Invoice not reported by supplier in GSTR-1 or not reflected in GSTR-2B"
        recommendation = "Verify with supplier and check GSTR-2B for next period"
        
        mismatch = Mismatch(
            id=uuid4(),
            invoice_id_1=invoice.id,
            invoice_id_2=None,
            taxpayer_id=taxpayer_id,
            mismatch_type=mismatch_type,
            risk_level=risk_level,
            status=MismatchStatus.OPEN,
            amount_difference=invoice.total_amount,
            tax_impact=invoice.total_tax,
            itc_impact=invoice.total_tax,
            description=description,
            root_cause=root_cause,
            recommendation=recommendation,
            reconciliation_run_id=reconciliation_run_id,
            detected_at=datetime.utcnow()
        )
        
        await self.mismatch_repo.create(mismatch)
        return mismatch
    
    def _determine_mismatch_type(self, inv1: Invoice, inv2: Invoice) -> MismatchType:
        """Determine the type of mismatch between two invoices."""
        # Check amount mismatch
        if not inv1.total_amount.is_within_tolerance(inv2.total_amount, self.amount_tolerance):
            return MismatchType.AMOUNT_MISMATCH
        
        # Check tax amount mismatch
        if not inv1.total_tax.is_within_tolerance(inv2.total_tax, self.amount_tolerance):
            return MismatchType.TAX_AMOUNT_MISMATCH
        
        # Check date mismatch
        date_diff = abs((inv1.invoice_date - inv2.invoice_date).days)
        if date_diff > self.date_tolerance:
            return MismatchType.DATE_MISMATCH
        
        # Check GSTIN mismatch
        if inv1.supplier_gstin != inv2.supplier_gstin:
            return MismatchType.GSTIN_MISMATCH
        
        # Default to amount mismatch
        return MismatchType.AMOUNT_MISMATCH
    
    def _generate_mismatch_description(
        self,
        inv1: Invoice,
        inv2: Invoice,
        mismatch_type: MismatchType
    ) -> str:
        """Generate human-readable mismatch description."""
        if mismatch_type == MismatchType.AMOUNT_MISMATCH:
            variance = inv1.total_amount.variance_percent(inv2.total_amount)
            return (
                f"Amount mismatch for invoice {inv1.invoice_number}: "
                f"Purchase Register shows {inv1.total_amount}, "
                f"GSTR-2B shows {inv2.total_amount} "
                f"(variance: {variance:.2f}%)"
            )
        elif mismatch_type == MismatchType.TAX_AMOUNT_MISMATCH:
            return (
                f"Tax amount mismatch for invoice {inv1.invoice_number}: "
                f"Purchase Register tax: {inv1.total_tax}, "
                f"GSTR-2B tax: {inv2.total_tax}"
            )
        elif mismatch_type == MismatchType.DATE_MISMATCH:
            date_diff = abs((inv1.invoice_date - inv2.invoice_date).days)
            return (
                f"Date mismatch for invoice {inv1.invoice_number}: "
                f"Purchase Register date: {inv1.invoice_date.date()}, "
                f"GSTR-2B date: {inv2.invoice_date.date()} "
                f"({date_diff} days difference)"
            )
        else:
            return f"{mismatch_type.value} detected for invoice {inv1.invoice_number}"
    
    def _determine_root_cause(
        self,
        inv1: Invoice,
        inv2: Invoice,
        mismatch_type: MismatchType
    ) -> str:
        """Determine root cause of mismatch."""
        if mismatch_type == MismatchType.AMOUNT_MISMATCH:
            if inv1.total_amount > inv2.total_amount:
                return "Supplier reported lower amount in GSTR-1 than recorded in purchase register"
            else:
                return "Supplier reported higher amount in GSTR-1 than recorded in purchase register"
        elif mismatch_type == MismatchType.TAX_AMOUNT_MISMATCH:
            return "Tax calculation difference between purchase register and GSTR-1"
        elif mismatch_type == MismatchType.DATE_MISMATCH:
            return "Invoice date recorded differently in purchase register and GSTR-1"
        else:
            return "Data entry or reporting discrepancy"
    
    def _generate_recommendation(
        self,
        mismatch_type: MismatchType,
        risk_level: RiskLevel
    ) -> str:
        """Generate recommendation for resolving mismatch."""
        if risk_level == RiskLevel.CRITICAL:
            return "Immediate action required: Contact supplier and verify invoice details"
        elif risk_level == RiskLevel.HIGH:
            return "High priority: Reconcile with supplier within 7 days"
        elif risk_level == RiskLevel.MEDIUM:
            return "Review and reconcile with supplier within 15 days"
        else:
            return "Low priority: Review during monthly reconciliation"
