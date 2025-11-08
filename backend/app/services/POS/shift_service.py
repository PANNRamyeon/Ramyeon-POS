from datetime import datetime
import logging
from ...database import db_manager
from notifications.shift_summary_service import shift_summary_service

logger = logging.getLogger(__name__)

class ShiftService:
    def __init__(self):
        self.db = db_manager.get_database()
        self.shift_collection = self.db.shifts
        self.sales_collection = self.db.sales  # ✅ ADD THIS
    
    def generate_shift_id(self):
        """Generate SHIFT-#### ID"""
        pipeline = [
            {'$match': {'_id': {'$regex': '^SHIFT-'}}},
            {'$project': {'numericPart': {'$toInt': {'$substr': ['$_id', 6, -1]}}}},
            {'$sort': {'numericPart': -1}},
            {'$limit': 1}
        ]
        result = list(self.shift_collection.aggregate(pipeline))
        next_number = result[0]['numericPart'] + 1 if result else 1
        return f"SHIFT-{next_number:04d}"
    
    def start_shift(self, cashier_id, opening_cash):
        """Start a new cashier shift"""
        shift_id = self.generate_shift_id()
        
        shift_record = {
            '_id': shift_id,
            'cashier_id': cashier_id,
            'opening_cash': opening_cash,
            'start_time': datetime.utcnow(),
            'status': 'open',  # ✅ CHANGED: 'active' → 'open' for consistency
            'total_sales': 0,
            'total_transactions': 0,
            'cash_sales': 0,  # ✅ ADD: Track cash sales separately
            'payment_breakdown': {},  # ✅ ADD: Track by payment method
            'last_transaction_time': None  # ✅ ADD: Track last sale time
        }
        
        self.shift_collection.insert_one(shift_record)
        
        logger.info(f"✅ Shift started: {shift_id} by {cashier_id}")
        
        return shift_record
    
    def get_active_shift(self, cashier_id):
        """Get cashier's currently active shift"""
        return self.shift_collection.find_one({
            'cashier_id': cashier_id,
            'status': 'open'  # ✅ CHANGED: 'active' → 'open'
        })
    
    def calculate_shift_statistics(self, shift_id):
        """
        Calculate shift statistics by querying all sales for this shift
        This is a backup/verification method - normally stats are updated in real-time
        
        Args:
            shift_id: Shift ID to calculate stats for
            
        Returns:
            dict: Calculated statistics
        """
        try:
            logger.info(f"📊 Calculating statistics for shift {shift_id}")
            
            # Get all sales for this shift
            sales = list(self.sales_collection.find({
                'shift_id': shift_id,
                'status': 'completed',  # Only count completed sales
                'is_voided': {'$ne': True}  # Exclude voided sales
            }))
            
            logger.info(f"   Found {len(sales)} completed sales")
            
            # Calculate totals
            total_sales = sum(sale.get('total_amount', 0) for sale in sales)
            total_transactions = len(sales)
            
            # Calculate cash sales
            cash_sales = sum(
                sale.get('total_amount', 0) 
                for sale in sales 
                if sale.get('payment_method', '').lower() == 'cash'
            )
            
            # Calculate payment breakdown
            payment_breakdown = {}
            for sale in sales:
                method = sale.get('payment_method', 'unknown').lower()
                amount = sale.get('total_amount', 0)
                payment_breakdown[method] = payment_breakdown.get(method, 0) + amount
            
            logger.info(f"   Total Sales: ₱{total_sales:.2f}")
            logger.info(f"   Total Transactions: {total_transactions}")
            logger.info(f"   Cash Sales: ₱{cash_sales:.2f}")
            logger.info(f"   Payment Breakdown: {payment_breakdown}")
            
            return {
                'total_sales': round(total_sales, 2),
                'total_transactions': total_transactions,
                'cash_sales': round(cash_sales, 2),
                'payment_breakdown': payment_breakdown
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating shift statistics: {str(e)}")
            return {
                'total_sales': 0,
                'total_transactions': 0,
                'cash_sales': 0,
                'payment_breakdown': {}
            }
    
    def end_shift(self, shift_id, closing_cash, recalculate=True):
        """
        End a shift and finalize statistics
        
        Args:
            shift_id: Shift ID to close
            closing_cash: Cash amount at closing
            recalculate: Whether to recalculate stats from sales (default True)
            
        Returns:
            dict: Updated shift record
        """
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔒 Closing Shift: {shift_id}")
            logger.info(f"{'='*60}")
            
            # Get current shift
            shift = self.shift_collection.find_one({'_id': shift_id})
            
            if not shift:
                raise ValueError(f"Shift {shift_id} not found")
            
            if shift.get('status') == 'closed':
                raise ValueError(f"Shift {shift_id} is already closed")
            
            # ✅ Recalculate statistics from actual sales (ensures accuracy)
            if recalculate:
                logger.info("📊 Recalculating shift statistics from sales...")
                calculated_stats = self.calculate_shift_statistics(shift_id)
            else:
                # Use existing stats from shift document
                calculated_stats = {
                    'total_sales': shift.get('total_sales', 0),
                    'total_transactions': shift.get('total_transactions', 0),
                    'cash_sales': shift.get('cash_sales', 0),
                    'payment_breakdown': shift.get('payment_breakdown', {})
                }
            
            # Calculate expected cash and variance
            opening_cash = shift.get('opening_cash', 0)
            cash_sales = calculated_stats['cash_sales']
            expected_cash = opening_cash + cash_sales
            variance = closing_cash - expected_cash
            
            logger.info(f"\n💰 Cash Reconciliation:")
            logger.info(f"   Opening Cash: ₱{opening_cash:.2f}")
            logger.info(f"   Cash Sales: ₱{cash_sales:.2f}")
            logger.info(f"   Expected Cash: ₱{expected_cash:.2f}")
            logger.info(f"   Closing Cash: ₱{closing_cash:.2f}")
            logger.info(f"   Variance: {'₱' if variance >= 0 else '-₱'}{abs(variance):.2f}")
            
            if abs(variance) > 0:
                logger.warning(f"⚠️ Cash variance detected: ₱{variance:.2f}")
            
            # Update shift with final statistics
            update_data = {
                'status': 'closed',
                'end_time': datetime.utcnow(),
                'closing_cash': closing_cash,
                
                # ✅ Finalized statistics
                'total_sales': calculated_stats['total_sales'],
                'total_transactions': calculated_stats['total_transactions'],
                'cash_sales': calculated_stats['cash_sales'],
                'payment_breakdown': calculated_stats['payment_breakdown'],
                
                # ✅ Cash reconciliation
                'expected_cash': round(expected_cash, 2),
                'cash_variance': round(variance, 2),
                
                # ✅ Metadata
                'closed_at': datetime.utcnow(),
                'statistics_calculated_at': datetime.utcnow()
            }
            
            self.shift_collection.update_one(
                {'_id': shift_id},
                {'$set': update_data}
            )
            
            logger.info(f"\n✅ Shift closed successfully")
            logger.info(f"{'='*60}\n")

            # Fetch the updated shift document
            updated_shift = self.shift_collection.find_one({'_id': shift_id})

            # Trigger shift summary email for verified admins
            try:
                email_result = shift_summary_service.send_shift_summary_email(updated_shift)
                if email_result.get("success"):
                    logger.info(
                        "Shift summary email dispatched to %s verified admin(s)",
                        email_result.get("sent_count", 0)
                    )
                else:
                    logger.warning(
                        "Shift summary email dispatch reported issues: %s",
                        email_result.get("error")
                    )
            except Exception as email_exc:
                logger.error("Failed to send shift summary email: %s", email_exc, exc_info=True)

            return updated_shift
            
        except Exception as e:
            logger.error(f"❌ Error closing shift: {str(e)}")
            raise
    
    def get_shift_by_id(self, shift_id):
        """Get shift by ID"""
        return self.shift_collection.find_one({'_id': shift_id})
    
    def get_cashier_shifts(self, cashier_id, limit=10):
        """Get cashier's shift history"""
        return list(
            self.shift_collection
            .find({'cashier_id': cashier_id})
            .sort('start_time', -1)
            .limit(limit)
        )
    
    def get_all_shifts(self, status=None, limit=50):
        """Get all shifts with optional status filter"""
        query = {}
        if status:
            query['status'] = status
        
        return list(
            self.shift_collection
            .find(query)
            .sort('start_time', -1)
            .limit(limit)
        )