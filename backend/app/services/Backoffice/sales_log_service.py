from datetime import datetime
from ...database import db_manager
from .customer_service import CustomerService
from .user_service import UserService
from notifications.services import notification_service

class SalesLogService:
    """
    Back office manual sales entry and CSV imports
    Used for:
    - Historical sales data entry
    - Sales made outside POS (phone orders, deliveries)
    - Imported sales from spreadsheets
    - Reconciliation entries
    """
    
    def __init__(self):
        self.db = db_manager.get_database()
        self.sales_log_collection = self.db.sales_log
        self.customer_service = CustomerService()
        self.user_service = UserService()

    # ================================================================
    # ID GENERATION
    # ================================================================
    
    def generate_saleslog_id(self):
        """Generate sequential SLOG-###### ID"""
        try:
            pipeline = [
                {'$match': {'_id': {'$regex': '^SLOG-'}}},
                {'$project': {
                    'numericPart': {'$toInt': {'$substr': ['$_id', 5, -1]}}
                }},
                {'$sort': {'numericPart': -1}},
                {'$limit': 1}
            ]
            
            result = list(self.sales_log_collection.aggregate(pipeline))
            next_number = result[0]['numericPart'] + 1 if result else 1
            
            return f"SLOG-{next_number:06d}"
        except Exception:
            count = self.sales_log_collection.count_documents({}) + 1
            return f"SLOG-{count:06d}"

    # ================================================================
    # CORE CRUD OPERATIONS
    # ================================================================
    
    def create_manual_sale(self, sale_data, user_id):
        """
        Create manual sales log entry
        
        Args:
            sale_data: {
                'customer_id': str (optional),
                'transaction_date': datetime,
                'items': [
                    {
                        'product_id': str,
                        'product_name': str,
                        'quantity': int,
                        'unit_price': float,
                        'total_price': float
                    }
                ],
                'total_amount': float,
                'payment_method': str,
                'sales_type': str,  # 'retail', 'wholesale', 'delivery'
                'tax_amount': float,
                'notes': str
            }
            user_id: str (USER-#### who created the entry)
        """
        try:
            log_id = self.generate_saleslog_id()
            
            # Calculate totals if not provided
            if 'items' in sale_data and not sale_data.get('total_amount'):
                total = sum(item.get('total_price', 0) for item in sale_data['items'])
                sale_data['total_amount'] = total
            
            log_record = {
                '_id': log_id,
                'customer_id': sale_data.get('customer_id'),
                'user_id': user_id,
                'transaction_date': sale_data.get('transaction_date', datetime.utcnow()),
                'items': sale_data.get('items', []),
                'total_amount': sale_data['total_amount'],
                'payment_method': sale_data.get('payment_method', 'cash'),
                'sales_type': sale_data.get('sales_type', 'retail'),
                'tax_rate': sale_data.get('tax_rate', 0),
                'tax_amount': sale_data.get('tax_amount', 0),
                'is_taxable': sale_data.get('is_taxable', False),
                'notes': sale_data.get('notes', ''),
                'source': 'manual',
                'status': 'completed',
                'created_at': datetime.utcnow(),
                'created_by': user_id
            }
            
            self.sales_log_collection.insert_one(log_record)
            
            # Send notification
            self._send_notification(log_record, 'manual_entry_created')
            
            return log_record
            
        except Exception as e:
            raise Exception(f"Error creating manual sale: {str(e)}")
    
    def get_saleslog_by_id(self, log_id):
        """Get sales log by string ID"""
        try:
            log = self.sales_log_collection.find_one({'_id': log_id})
            return log
            
        except Exception as e:
            raise Exception(f"Error retrieving sales log: {str(e)}")
    
    def update_saleslog(self, log_id, update_data, user_id):
        """Update an existing sales log"""
        try:
            # Remove _id if present
            update_data.pop('_id', None)
            
            # Add update metadata
            update_data['last_updated'] = datetime.utcnow()
            update_data['last_updated_by'] = user_id
            
            result = self.sales_log_collection.update_one(
                {'_id': log_id},
                {'$set': update_data}
            )
            
            if result.modified_count > 0:
                updated_log = self.get_saleslog_by_id(log_id)
                self._send_notification(updated_log, 'manual_entry_updated')
                return updated_log
            
            return None
                
        except Exception as e:
            raise Exception(f"Error updating sales log: {str(e)}")
    
    def delete_saleslog(self, log_id, user_id):
        """
        Soft delete a sales log entry
        (Hard delete not recommended - keep for audit trail)
        """
        try:
            result = self.sales_log_collection.update_one(
                {'_id': log_id},
                {
                    '$set': {
                        'isDeleted': True,
                        'deleted_at': datetime.utcnow(),
                        'deleted_by': user_id
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            raise Exception(f"Error deleting sales log: {str(e)}")

    # ================================================================
    # QUERY OPERATIONS
    # ================================================================
    
    def get_all_saleslogs(self, page=1, page_size=50, filters=None, include_deleted=False):
        """Get sales logs with pagination and filtering"""
        try:
            skip = (page - 1) * page_size
            query = {}
            
            # Default: exclude deleted
            if not include_deleted:
                query['isDeleted'] = {'$ne': True}
            
            # Apply filters
            if filters:
                if filters.get('start_date') and filters.get('end_date'):
                    query['transaction_date'] = {
                        '$gte': filters['start_date'],
                        '$lte': filters['end_date']
                    }
                if filters.get('sales_type'):
                    query['sales_type'] = filters['sales_type']
                if filters.get('source'):
                    query['source'] = filters['source']
                if filters.get('payment_method'):
                    query['payment_method'] = filters['payment_method']
                if filters.get('customer_id'):
                    query['customer_id'] = filters['customer_id']
                if filters.get('user_id'):
                    query['user_id'] = filters['user_id']
            
            # Get logs with pagination
            logs = list(
                self.sales_log_collection
                .find(query)
                .sort('transaction_date', -1)
                .skip(skip)
                .limit(page_size)
            )
            
            total_count = self.sales_log_collection.count_documents(query)
            total_pages = (total_count + page_size - 1) // page_size
            
            return {
                'data': logs,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_records': total_count,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'filters_applied': filters or {}
            }
            
        except Exception as e:
            raise Exception(f"Error retrieving sales logs: {str(e)}")

    # ================================================================
    # CSV IMPORT OPERATIONS
    # ================================================================
    
    def import_from_csv(self, csv_data, user_id):
        """
        Import sales from CSV file
        
        Args:
            csv_data: List of dict from CSV parser
            user_id: User importing the data
        """
        try:
            results = {
                'successful': [],
                'failed': [],
                'total_processed': len(csv_data)
            }
            
            for row_num, row in enumerate(csv_data, start=1):
                try:
                    # Transform CSV row to sales log format
                    sale_data = {
                        'customer_id': row.get('customer_id'),
                        'transaction_date': self._parse_date(row.get('transaction_date')),
                        'total_amount': float(row.get('total_amount', 0)),
                        'payment_method': row.get('payment_method', 'cash'),
                        'sales_type': row.get('sales_type', 'retail'),
                        'items': self._parse_items_from_csv(row),
                        'notes': f"Imported from CSV - Row {row_num}",
                        'source': 'csv_import'
                    }
                    
                    created_log = self.create_manual_sale(sale_data, user_id)
                    results['successful'].append({
                        'row': row_num,
                        'log_id': created_log['_id']
                    })
                    
                except Exception as row_error:
                    results['failed'].append({
                        'row': row_num,
                        'error': str(row_error),
                        'data': row
                    })
            
            # Send summary notification
            self._send_import_notification(results, user_id)
            
            return results
            
        except Exception as e:
            raise Exception(f"Error importing CSV: {str(e)}")
    
    def _parse_items_from_csv(self, row):
        """Parse item list from CSV row"""
        # This depends on your CSV format
        # Could be single item per row or JSON array
        items = []
        
        if row.get('items'):
            # If items are in JSON format
            import json
            items = json.loads(row['items'])
        else:
            # Single item per row
            items = [{
                'product_id': row.get('product_id', ''),
                'product_name': row.get('product_name', ''),
                'quantity': int(row.get('quantity', 0)),
                'unit_price': float(row.get('unit_price', 0)),
                'total_price': float(row.get('total_price', 0))
            }]
        
        return items
    
    def _parse_date(self, date_str):
        """Parse date from various string formats"""
        if isinstance(date_str, datetime):
            return date_str
        
        from django.utils.dateparse import parse_datetime, parse_date
        
        parsed = parse_datetime(date_str) or parse_date(date_str)
        if parsed:
            return parsed if isinstance(parsed, datetime) else datetime.combine(parsed, datetime.min.time())
        
        return datetime.utcnow()

    # ================================================================
    # EXPORT OPERATIONS
    # ================================================================
    
    def export_to_csv(self, filters=None):
        """
        Get sales logs for CSV export
        Returns flattened data suitable for CSV
        """
        try:
            query = {}
            
            if filters:
                if filters.get('start_date') and filters.get('end_date'):
                    query['transaction_date'] = {
                        '$gte': filters['start_date'],
                        '$lte': filters['end_date']
                    }
                if filters.get('sales_type'):
                    query['sales_type'] = filters['sales_type']
            
            logs = list(self.sales_log_collection.find(query).limit(10000))
            
            # Flatten for CSV export
            export_data = []
            for log in logs:
                # If multiple items, create one row per item
                if log.get('items'):
                    for item in log['items']:
                        export_data.append({
                            'log_id': log['_id'],
                            'transaction_date': log['transaction_date'],
                            'customer_id': log.get('customer_id', ''),
                            'product_id': item.get('product_id', ''),
                            'product_name': item.get('product_name', ''),
                            'quantity': item.get('quantity', 0),
                            'unit_price': item.get('unit_price', 0),
                            'total_price': item.get('total_price', 0),
                            'payment_method': log.get('payment_method', ''),
                            'sales_type': log.get('sales_type', ''),
                            'total_amount': log.get('total_amount', 0)
                        })
                else:
                    # No items - just the header row
                    export_data.append({
                        'log_id': log['_id'],
                        'transaction_date': log['transaction_date'],
                        'customer_id': log.get('customer_id', ''),
                        'total_amount': log.get('total_amount', 0),
                        'payment_method': log.get('payment_method', ''),
                        'sales_type': log.get('sales_type', '')
                    })
            
            return export_data
            
        except Exception as e:
            raise Exception(f"Error exporting to CSV: {str(e)}")

    # ================================================================
    # REPORTING AND ANALYTICS
    # ================================================================
    
    def get_sales_summary(self, start_date, end_date, group_by='day'):
        """Get sales summary for reporting"""
        try:
            query = {
                'transaction_date': {
                    '$gte': start_date,
                    '$lte': end_date
                },
                'isDeleted': {'$ne': True}
            }
            
            # Group by configuration
            group_format = {
                'day': '%Y-%m-%d',
                'month': '%Y-%m',
                'year': '%Y'
            }
            
            pipeline = [
                {'$match': query},
                {'$group': {
                    '_id': {
                        '$dateToString': {
                            'format': group_format.get(group_by, '%Y-%m-%d'),
                            'date': '$transaction_date'
                        }
                    },
                    'total_sales': {'$sum': '$total_amount'},
                    'transaction_count': {'$sum': 1},
                    'avg_sale': {'$avg': '$total_amount'}
                }},
                {'$sort': {'_id': 1}}
            ]
            
            results = list(self.sales_log_collection.aggregate(pipeline))
            return results
            
        except Exception as e:
            raise Exception(f"Error getting sales summary: {str(e)}")

    # ================================================================
    # HELPER METHODS
    # ================================================================
    
    def _send_notification(self, log_record, action_type):
        """Send notification for sales log actions"""
        try:
            titles = {
                'manual_entry_created': 'Manual Sale Logged',
                'manual_entry_updated': 'Sales Log Updated',
                'csv_import_completed': 'CSV Import Completed'
            }
            
            notification_service.create_notification(
                title=titles.get(action_type, 'Sales Log Action'),
                message=f"Sales log {log_record['_id']} - ₱{log_record['total_amount']}",
                priority='low',
                notification_type='sales',
                metadata={
                    'log_id': log_record['_id'],
                    'total_amount': log_record['total_amount'],
                    'source': log_record.get('source', 'manual')
                }
            )
            
        except Exception as e:
            print(f"Failed to send notification: {e}")
    
    def _send_import_notification(self, results, user_id):
        """Send notification after CSV import"""
        try:
            successful = len(results['successful'])
            failed = len(results['failed'])
            total = results['total_processed']
            
            notification_service.create_notification(
                title='CSV Import Completed',
                message=f'Imported {successful} of {total} sales ({failed} failed)',
                priority='medium' if failed > 0 else 'low',
                notification_type='system',
                metadata={
                    'successful': successful,
                    'failed': failed,
                    'total': total,
                    'imported_by': user_id
                }
            )
            
        except Exception as e:
            print(f"Failed to send import notification: {e}")