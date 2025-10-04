from datetime import datetime
from ...database import db_manager

class ShiftService:
    def __init__(self):
        self.db = db_manager.get_database()
        self.shift_collection = self.db.shifts
    
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
            'status': 'active',
            'total_sales': 0,
            'total_transactions': 0
        }
        
        self.shift_collection.insert_one(shift_record)
        return shift_record
    
    def get_active_shift(self, cashier_id):
        """Get cashier's currently active shift"""
        return self.shift_collection.find_one({
            'cashier_id': cashier_id,
            'status': 'active'
        })
    
    def end_shift(self, shift_id, closing_cash):
        """End a shift"""
        self.shift_collection.update_one(
            {'_id': shift_id},
            {'$set': {
                'status': 'closed',
                'end_time': datetime.utcnow(),
                'closing_cash': closing_cash
            }}
        )