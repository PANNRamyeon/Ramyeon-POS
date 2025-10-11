from datetime import datetime, timedelta
from ...database import db_manager
import logging

logger = logging.getLogger(__name__)


class BatchService:
    """
    Lightweight service for POS batch operations
    Handles FIFO stock deduction and batch availability checks
    """
    
    def __init__(self):
        self.db = db_manager.get_database()
        self.batches_collection = self.db.batches
        self.products_collection = self.db.products
    
    # ================================================================
    # FIFO STOCK DEDUCTION (Main POS Function)
    # ================================================================
    
    def deduct_stock_fifo(self, product_id, quantity_needed, transaction_date=None):
        """
        Deduct stock from batches using FIFO (First In, First Out)
        
        Args:
            product_id: Product ID (e.g., 'PROD-00009')
            quantity_needed: Number of units to deduct
            transaction_date: Transaction timestamp (default: now)
        
        Returns:
            List of batch deductions: [
                {
                    'batch_id': 'BATCH-00009-001',
                    'batch_number': 'INITIAL-20251010',
                    'quantity_deducted': 10,
                    'expiry_date': datetime,
                    'cost_price': 10
                }
            ]
        
        Raises:
            ValueError: If insufficient stock or no active batches
        """
        try:
            if transaction_date is None:
                transaction_date = datetime.utcnow()
            
            print(f"   🔄 FIFO deduction for {product_id}: {quantity_needed} units needed")
            
            # ✅ Get all active batches for this product, sorted by date (FIFO)
            batches = list(self.batches_collection.find({
                'product_id': product_id,
                'status': 'active',
                'quantity_remaining': {'$gt': 0}
            }).sort([
                ('date_received', 1),  # Oldest first (FIFO)
                ('created_at', 1)      # Secondary sort
            ]))
            
            if not batches:
                raise ValueError(f"No active batches found for product {product_id}")
            
            # Calculate total available stock across all batches
            total_available = sum(batch.get('quantity_remaining', 0) for batch in batches)
            
            print(f"   📊 Available across {len(batches)} batches: {total_available} units")
            
            if total_available < quantity_needed:
                raise ValueError(
                    f"Insufficient stock for {product_id}. "
                    f"Available: {total_available}, Requested: {quantity_needed}"
                )
            
            # ✅ Deduct from batches in FIFO order
            batch_deductions = []
            remaining_to_deduct = quantity_needed
            
            for batch in batches:
                if remaining_to_deduct <= 0:
                    break
                
                batch_id = batch['_id']
                batch_available = batch.get('quantity_remaining', 0)
                
                # Determine how much to deduct from this batch
                deduct_amount = min(batch_available, remaining_to_deduct)
                
                new_remaining = batch_available - deduct_amount
                
                print(f"   📦 {batch_id}: Deducting {deduct_amount} (Remaining: {batch_available} → {new_remaining})")
                
                # ✅ Update batch quantity
                update_data = {
                    'quantity_remaining': new_remaining,
                    'updated_at': transaction_date
                }
                
                # Mark batch as depleted if empty
                if new_remaining == 0:
                    update_data['status'] = 'depleted'
                    print(f"   ⚠️ {batch_id}: DEPLETED")
                
                self.batches_collection.update_one(
                    {'_id': batch_id},
                    {'$set': update_data}
                )
                
                # Track batch deduction for sale record
                batch_deductions.append({
                    'batch_id': batch_id,
                    'batch_number': batch.get('batch_number'),
                    'quantity_deducted': deduct_amount,
                    'expiry_date': batch.get('expiry_date'),
                    'cost_price': batch.get('cost_price', 0)
                })
                
                remaining_to_deduct -= deduct_amount
            
            print(f"   ✅ FIFO deduction complete: {len(batch_deductions)} batches used")
            
            return batch_deductions
            
        except Exception as e:
            logger.error(f"❌ FIFO deduction failed: {str(e)}")
            raise
    
    # ================================================================
    # STOCK VALIDATION (Check before checkout)
    # ================================================================
    
    def check_batch_availability(self, product_id, quantity_needed):
        """
        Check if enough batch stock is available (without deducting)
        
        Args:
            product_id: Product ID
            quantity_needed: Number of units needed
        
        Returns:
            {
                'available': bool,
                'total_stock': int,
                'batches_count': int,
                'oldest_batch': dict or None,
                'near_expiry': bool (within 30 days)
            }
        """
        try:
            batches = list(self.batches_collection.find({
                'product_id': product_id,
                'status': 'active',
                'quantity_remaining': {'$gt': 0}
            }).sort('date_received', 1))
            
            if not batches:
                return {
                    'available': False,
                    'total_stock': 0,
                    'batches_count': 0,
                    'oldest_batch': None,
                    'near_expiry': False
                }
            
            total_stock = sum(b.get('quantity_remaining', 0) for b in batches)
            oldest_batch = batches[0]
            
            # Check if oldest batch is near expiry
            days_until_expiry = None
            near_expiry = False
            
            if oldest_batch.get('expiry_date'):
                days_until_expiry = (oldest_batch['expiry_date'] - datetime.utcnow()).days
                near_expiry = days_until_expiry <= 30
            
            return {
                'available': total_stock >= quantity_needed,
                'total_stock': total_stock,
                'batches_count': len(batches),
                'oldest_batch': {
                    'batch_id': oldest_batch['_id'],
                    'batch_number': oldest_batch.get('batch_number'),
                    'quantity_remaining': oldest_batch.get('quantity_remaining'),
                    'expiry_date': oldest_batch.get('expiry_date'),
                    'days_until_expiry': days_until_expiry
                },
                'near_expiry': near_expiry
            }
            
        except Exception as e:
            logger.error(f"❌ Batch availability check failed: {str(e)}")
            return {
                'available': False,
                'total_stock': 0,
                'batches_count': 0,
                'oldest_batch': None,
                'near_expiry': False,
                'error': str(e)
            }
    
    # ================================================================
    # BATCH RESTORE (For voided sales)
    # ================================================================
    
    def restore_stock_to_batches(self, batch_deductions, transaction_date=None):
        """
        Restore stock back to batches (when sale is voided)
        
        Args:
            batch_deductions: List from sale record's batches_used field
            transaction_date: Void timestamp
        
        Returns:
            Number of batches restored
        """
        try:
            if transaction_date is None:
                transaction_date = datetime.utcnow()
            
            print(f"🔄 Restoring stock to {len(batch_deductions)} batches")
            
            restored_count = 0
            
            for deduction in batch_deductions:
                batch_id = deduction['batch_id']
                quantity_to_restore = deduction['quantity_deducted']
                
                # Get current batch
                batch = self.batches_collection.find_one({'_id': batch_id})
                
                if not batch:
                    logger.warning(f"⚠️ Batch {batch_id} not found for restoration")
                    continue
                
                new_remaining = batch.get('quantity_remaining', 0) + quantity_to_restore
                
                # Update batch
                update_data = {
                    'quantity_remaining': new_remaining,
                    'updated_at': transaction_date
                }
                
                # Reactivate if it was depleted
                if batch.get('status') == 'depleted':
                    update_data['status'] = 'active'
                    print(f"   ✅ {batch_id}: REACTIVATED")
                
                self.batches_collection.update_one(
                    {'_id': batch_id},
                    {'$set': update_data}
                )
                
                print(f"   📦 {batch_id}: Restored {quantity_to_restore} units (Now: {new_remaining})")
                
                restored_count += 1
            
            print(f"✅ Stock restored to {restored_count} batches")
            
            return restored_count
            
        except Exception as e:
            logger.error(f"❌ Stock restoration failed: {str(e)}")
            raise
    
    # ================================================================
    # BATCH INFO (Quick lookups)
    # ================================================================
    
    def get_product_batches(self, product_id):
        """
        Get all active batches for a product
        
        Returns:
            List of batch documents sorted by FIFO
        """
        try:
            batches = list(self.batches_collection.find({
                'product_id': product_id,
                'status': 'active',
                'quantity_remaining': {'$gt': 0}
            }).sort('date_received', 1))
            
            return batches
            
        except Exception as e:
            logger.error(f"❌ Get batches failed: {str(e)}")
            return []
    
    def get_near_expiry_batches(self, days_threshold=30):
        """
        Get all batches expiring within the threshold
        
        Args:
            days_threshold: Number of days (default: 30)
        
        Returns:
            List of batches near expiry
        """
        try:
            threshold_date = datetime.utcnow() + timedelta(days=days_threshold)
            
            batches = list(self.batches_collection.find({
                'status': 'active',
                'quantity_remaining': {'$gt': 0},
                'expiry_date': {'$lte': threshold_date}
            }).sort('expiry_date', 1))
            
            return batches
            
        except Exception as e:
            logger.error(f"❌ Get near-expiry batches failed: {str(e)}")
            return []