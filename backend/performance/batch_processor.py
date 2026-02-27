"""
Batch processing utilities for handling 10k+ invoices efficiently.

This module provides batch processing capabilities for:
- Reconciliation operations
- Mismatch detection
- ITC validation
- Vendor risk assessment
"""

import logging
from typing import List, Dict, Any, Callable, Optional, Iterator
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Generic batch processor for handling large datasets.
    
    Features:
    - Configurable batch size
    - Progress tracking
    - Error handling and retry logic
    - Parallel processing support
    - Performance metrics
    """
    
    def __init__(
        self,
        batch_size: int = 500,
        max_workers: int = 4,
        retry_attempts: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize batch processor.
        
        Args:
            batch_size: Number of items per batch
            max_workers: Maximum parallel workers
            retry_attempts: Number of retry attempts on failure
            retry_delay: Delay between retries in seconds
        """
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        # Metrics
        self.total_processed = 0
        self.total_failed = 0
        self.total_time = 0.0
        self.batch_times: List[float] = []
    
    def process_batches(
        self,
        items: List[Any],
        process_func: Callable[[List[Any]], Any],
        parallel: bool = False
    ) -> List[Any]:
        """
        Process items in batches.
        
        Args:
            items: List of items to process
            process_func: Function to process each batch
            parallel: Enable parallel processing
            
        Returns:
            List of results from all batches
        """
        start_time = time.time()
        results = []
        
        # Split into batches
        batches = self._create_batches(items)
        total_batches = len(batches)
        
        logger.info(
            f"Processing {len(items)} items in {total_batches} batches "
            f"(batch_size={self.batch_size})"
        )
        
        if parallel and self.max_workers > 1:
            results = self._process_parallel(batches, process_func)
        else:
            results = self._process_sequential(batches, process_func)
        
        # Update metrics
        self.total_time = time.time() - start_time
        
        logger.info(
            f"Batch processing complete: {self.total_processed} processed, "
            f"{self.total_failed} failed, {self.total_time:.2f}s total"
        )
        
        return results
    
    def _create_batches(
        self,
        items: List[Any]
    ) -> List[List[Any]]:
        """Split items into batches."""
        batches = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batches.append(batch)
        return batches
    
    def _process_sequential(
        self,
        batches: List[List[Any]],
        process_func: Callable[[List[Any]], Any]
    ) -> List[Any]:
        """Process batches sequentially."""
        results = []
        
        for i, batch in enumerate(batches, 1):
            logger.info(f"Processing batch {i}/{len(batches)}")
            
            batch_start = time.time()
            result = self._process_batch_with_retry(batch, process_func)
            batch_time = time.time() - batch_start
            
            self.batch_times.append(batch_time)
            
            if result is not None:
                results.append(result)
                self.total_processed += len(batch)
            else:
                self.total_failed += len(batch)
            
            logger.info(
                f"Batch {i} completed in {batch_time:.2f}s "
                f"(avg: {sum(self.batch_times)/len(self.batch_times):.2f}s)"
            )
        
        return results
    
    def _process_parallel(
        self,
        batches: List[List[Any]],
        process_func: Callable[[List[Any]], Any]
    ) -> List[Any]:
        """Process batches in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all batches
            future_to_batch = {
                executor.submit(self._process_batch_with_retry, batch, process_func): i
                for i, batch in enumerate(batches, 1)
            }
            
            # Process completed batches
            for future in as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                        self.total_processed += len(batches[batch_num - 1])
                    else:
                        self.total_failed += len(batches[batch_num - 1])
                    
                    logger.info(f"Batch {batch_num} completed")
                    
                except Exception as e:
                    logger.error(f"Batch {batch_num} failed: {e}")
                    self.total_failed += len(batches[batch_num - 1])
        
        return results
    
    def _process_batch_with_retry(
        self,
        batch: List[Any],
        process_func: Callable[[List[Any]], Any]
    ) -> Optional[Any]:
        """Process a batch with retry logic."""
        for attempt in range(self.retry_attempts):
            try:
                return process_func(batch)
                
            except Exception as e:
                logger.warning(
                    f"Batch processing failed (attempt {attempt + 1}/{self.retry_attempts}): {e}"
                )
                
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Batch processing failed after {self.retry_attempts} attempts")
                    return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get processing metrics."""
        avg_batch_time = sum(self.batch_times) / len(self.batch_times) if self.batch_times else 0
        
        return {
            "total_processed": self.total_processed,
            "total_failed": self.total_failed,
            "total_time_seconds": round(self.total_time, 2),
            "average_batch_time_seconds": round(avg_batch_time, 2),
            "throughput_items_per_second": round(
                self.total_processed / self.total_time if self.total_time > 0 else 0,
                2
            )
        }


class ReconciliationBatchProcessor:
    """
    Specialized batch processor for GST reconciliation.
    
    Handles:
    - Invoice matching in batches
    - Mismatch detection in batches
    - ITC validation in batches
    """
    
    def __init__(
        self,
        neo4j_connection,
        batch_size: int = 500,
        parallel: bool = False
    ):
        """
        Initialize reconciliation batch processor.
        
        Args:
            neo4j_connection: Neo4j connection instance
            batch_size: Batch size for processing
            parallel: Enable parallel processing
        """
        self.connection = neo4j_connection
        self.batch_size = batch_size
        self.parallel = parallel
        self.processor = BatchProcessor(batch_size=batch_size)
    
    def reconcile_invoices_batch(
        self,
        taxpayer_gstin: str,
        period: str
    ) -> Dict[str, Any]:
        """
        Reconcile invoices in batches.
        
        Args:
            taxpayer_gstin: Taxpayer GSTIN
            period: Period in MMYYYY format
            
        Returns:
            Reconciliation results with metrics
        """
        start_time = time.time()
        
        # Get all invoices to process
        invoices = self._get_invoices_to_process(taxpayer_gstin, period)
        
        logger.info(f"Found {len(invoices)} invoices to reconcile")
        
        # Process in batches
        results = self.processor.process_batches(
            items=invoices,
            process_func=self._process_invoice_batch,
            parallel=self.parallel
        )
        
        # Aggregate results
        total_matches = sum(r.get("matches", 0) for r in results if r)
        total_mismatches = sum(r.get("mismatches", 0) for r in results if r)
        
        processing_time = time.time() - start_time
        
        return {
            "taxpayer_gstin": taxpayer_gstin,
            "period": period,
            "total_invoices": len(invoices),
            "total_matches": total_matches,
            "total_mismatches": total_mismatches,
            "processing_time_seconds": round(processing_time, 2),
            "metrics": self.processor.get_metrics()
        }
    
    def _get_invoices_to_process(
        self,
        taxpayer_gstin: str,
        period: str
    ) -> List[Dict[str, Any]]:
        """Get invoices that need processing."""
        query = """
        MATCH (buyer:Taxpayer {gstin: $taxpayer_gstin})-[:RECEIVED_BY]-(i:Invoice)
        WHERE i.source_type = 'PURCHASE_REGISTER'
        AND i.source_period = $period
        AND NOT EXISTS((i)-[:MATCHES]-())
        AND NOT EXISTS((i)-[:HAS_MISMATCH]-())
        
        RETURN i {
            .id,
            .invoice_number,
            .invoice_date,
            .supplier_gstin,
            .recipient_gstin,
            .total_amount,
            .total_tax
        } as invoice
        ORDER BY i.total_amount DESC
        """
        
        try:
            records = self.connection.execute_query(
                query,
                {
                    "taxpayer_gstin": taxpayer_gstin,
                    "period": period
                }
            )
            return [dict(r["invoice"]) for r in records]
            
        except Exception as e:
            logger.error(f"Failed to get invoices: {e}")
            return []
    
    def _process_invoice_batch(
        self,
        invoices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process a batch of invoices."""
        matches = 0
        mismatches = 0
        
        for invoice in invoices:
            # Find GSTR-2B matches
            gstr2b_matches = self._find_gstr2b_matches(invoice)
            
            if gstr2b_matches:
                # Create match relationship
                self._create_match(invoice["id"], gstr2b_matches[0]["id"])
                matches += 1
            else:
                # Create mismatch
                self._create_mismatch(invoice)
                mismatches += 1
        
        return {
            "matches": matches,
            "mismatches": mismatches,
            "processed": len(invoices)
        }
    
    def _find_gstr2b_matches(
        self,
        invoice: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find GSTR-2B matches for an invoice."""
        query = """
        MATCH (gstr2b:Invoice)
        WHERE gstr2b.source_type = 'GSTR-2B'
        AND gstr2b.invoice_number = $invoice_number
        AND gstr2b.supplier_gstin = $supplier_gstin
        AND abs(gstr2b.total_amount - $total_amount) <= ($total_amount * 0.05)
        RETURN gstr2b {.id, .invoice_number, .total_amount} as invoice
        LIMIT 1
        """
        
        try:
            records = self.connection.execute_query(
                query,
                {
                    "invoice_number": invoice["invoice_number"],
                    "supplier_gstin": invoice["supplier_gstin"],
                    "total_amount": invoice["total_amount"]
                }
            )
            return [dict(r["invoice"]) for r in records]
            
        except Exception as e:
            logger.error(f"Failed to find matches: {e}")
            return []
    
    def _create_match(
        self,
        invoice1_id: str,
        invoice2_id: str
    ) -> bool:
        """Create MATCHES relationship."""
        query = """
        MATCH (i1:Invoice {id: $invoice1_id})
        MATCH (i2:Invoice {id: $invoice2_id})
        MERGE (i1)-[r:MATCHES]-(i2)
        SET r.matched_at = datetime(),
            r.confidence_score = 1.0
        RETURN r
        """
        
        try:
            self.connection.execute_write(
                query,
                {
                    "invoice1_id": invoice1_id,
                    "invoice2_id": invoice2_id
                }
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to create match: {e}")
            return False
    
    def _create_mismatch(
        self,
        invoice: Dict[str, Any]
    ) -> bool:
        """Create mismatch node."""
        query = """
        CREATE (m:Mismatch {
            id: randomUUID(),
            mismatch_type: 'MISSING_IN_GSTR2B',
            severity: 'HIGH',
            description: 'Invoice missing in GSTR-2B',
            taxpayer_gstin: $recipient_gstin,
            period: $period,
            amount_difference: $total_amount,
            detected_at: datetime(),
            resolved: false
        })
        
        WITH m
        MATCH (i:Invoice {id: $invoice_id})
        MERGE (i)-[:HAS_MISMATCH]->(m)
        
        RETURN m
        """
        
        try:
            self.connection.execute_write(
                query,
                {
                    "invoice_id": invoice["id"],
                    "recipient_gstin": invoice["recipient_gstin"],
                    "period": invoice.get("source_period", ""),
                    "total_amount": invoice["total_amount"]
                }
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to create mismatch: {e}")
            return False


class VendorRiskBatchProcessor:
    """Batch processor for vendor risk assessment."""
    
    def __init__(
        self,
        neo4j_connection,
        batch_size: int = 100
    ):
        """
        Initialize vendor risk batch processor.
        
        Args:
            neo4j_connection: Neo4j connection instance
            batch_size: Batch size for processing
        """
        self.connection = neo4j_connection
        self.batch_size = batch_size
        self.processor = BatchProcessor(batch_size=batch_size)
    
    def assess_vendors_batch(
        self,
        vendor_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Assess vendor risk in batches.
        
        Args:
            vendor_ids: Optional list of vendor IDs to assess
            
        Returns:
            Assessment results with metrics
        """
        # Get vendors to assess
        if vendor_ids:
            vendors = self._get_vendors_by_ids(vendor_ids)
        else:
            vendors = self._get_vendors_needing_assessment()
        
        logger.info(f"Assessing {len(vendors)} vendors")
        
        # Process in batches
        results = self.processor.process_batches(
            items=vendors,
            process_func=self._assess_vendor_batch,
            parallel=False
        )
        
        total_assessed = sum(r.get("assessed", 0) for r in results if r)
        
        return {
            "total_vendors": len(vendors),
            "total_assessed": total_assessed,
            "metrics": self.processor.get_metrics()
        }
    
    def _get_vendors_needing_assessment(self) -> List[Dict[str, Any]]:
        """Get vendors that need risk assessment."""
        query = """
        MATCH (v:Vendor)
        WHERE v.last_assessment_date IS NULL
        OR v.last_assessment_date < datetime() - duration({days: 30})
        RETURN v {.id, .gstin, .legal_name} as vendor
        LIMIT 1000
        """
        
        try:
            records = self.connection.execute_query(query, {})
            return [dict(r["vendor"]) for r in records]
            
        except Exception as e:
            logger.error(f"Failed to get vendors: {e}")
            return []
    
    def _get_vendors_by_ids(
        self,
        vendor_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Get vendors by IDs."""
        query = """
        MATCH (v:Vendor)
        WHERE v.id IN $vendor_ids
        RETURN v {.id, .gstin, .legal_name} as vendor
        """
        
        try:
            records = self.connection.execute_query(
                query,
                {"vendor_ids": vendor_ids}
            )
            return [dict(r["vendor"]) for r in records]
            
        except Exception as e:
            logger.error(f"Failed to get vendors: {e}")
            return []
    
    def _assess_vendor_batch(
        self,
        vendors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess a batch of vendors."""
        assessed = 0
        
        for vendor in vendors:
            # Calculate risk score (simplified)
            risk_score = self._calculate_vendor_risk(vendor)
            
            # Update vendor
            self._update_vendor_risk(vendor["id"], risk_score)
            assessed += 1
        
        return {"assessed": assessed}
    
    def _calculate_vendor_risk(
        self,
        vendor: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate vendor risk score."""
        # Simplified risk calculation
        # In production, use the VendorRiskPredictor from ml/vendor_risk.py
        return {
            "risk_score": 50.0,
            "risk_level": "MEDIUM",
            "compliance_score": 75.0
        }
    
    def _update_vendor_risk(
        self,
        vendor_id: str,
        risk_data: Dict[str, Any]
    ) -> bool:
        """Update vendor risk data."""
        query = """
        MATCH (v:Vendor {id: $vendor_id})
        SET v.risk_score = $risk_score,
            v.risk_level = $risk_level,
            v.compliance_score = $compliance_score,
            v.last_assessment_date = datetime()
        RETURN v
        """
        
        try:
            self.connection.execute_write(
                query,
                {
                    "vendor_id": vendor_id,
                    **risk_data
                }
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to update vendor: {e}")
            return False
