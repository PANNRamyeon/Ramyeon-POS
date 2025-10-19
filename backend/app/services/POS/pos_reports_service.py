from datetime import datetime, timedelta
from ...database import db_manager
from ..Backoffice.category_service import CategoryService
from ..POS.pos_sales_service import POSSalesService
from typing import List, Dict, Any
from ...database import db_manager
import logging

logger = logging.getLogger(__name__)

class POSReportsService:
    def __init__(self):
        self.db = db_manager.get_database()
        self.sales_collection = self.db.sales
        self.products_collection = self.db.products
        self.category_collection = self.db.category
        self.sales_service = POSSalesService()
        self.category_service = CategoryService()

    # ================================================================
    # 1. DAILY TOP PRODUCTS
    # ================================================================

    def get_daily_top_products(self, target_date: datetime = None, limit: int = 10) -> Dict[str, Any]:
        """Fetch daily top products with price per unit, orders, and total revenue"""
        try:
            if target_date is None:
                target_date = datetime.utcnow().date()
            else:
                target_date = target_date.date()

            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())

            # Aggregation pipeline for daily top products - UPDATED to include cost_price
            pipeline = [
                {
                    '$match': {
                        'transaction_date': {
                            '$gte': start_datetime,
                            '$lte': end_datetime
                        },
                        'status': 'completed',
                        'is_voided': False,
                        'source': 'pos'
                    }
                },
                {'$unwind': '$items'},
                {
                    '$lookup': {
                        'from': 'products',  # Join with products collection
                        'localField': 'items.product_id',
                        'foreignField': '_id',
                        'as': 'product_details'
                    }
                },
                {'$unwind': '$product_details'},
                {
                    '$group': {
                        '_id': {
                            'product_id': '$items.product_id',
                            'product_name': '$items.product_name',
                            'sku': '$items.sku'
                        },
                        'total_quantity': {'$sum': '$items.quantity'},
                        'total_revenue': {'$sum': '$items.subtotal'},
                        'unit_price': {'$avg': '$items.unit_price'},
                        'cost_price': {'$first': '$product_details.cost_price'},  # ADD THIS
                        'selling_price': {'$first': '$product_details.selling_price'},  # Optional: include selling price too
                        'order_count': {'$sum': 1}
                    }
                },
                {
                    '$project': {
                        'product_id': '$_id.product_id',
                        'product_name': '$_id.product_name',
                        'sku': '$_id.sku',
                        'unit_price': {'$round': ['$unit_price', 2]},
                        'cost_price': {'$round': ['$cost_price', 2]},  # ADD THIS
                        'selling_price': {'$round': ['$selling_price', 2]},  # Optional
                        'total_quantity': 1,
                        'total_revenue': {'$round': ['$total_revenue', 2]},
                        'order_count': 1
                    }
                },
                {'$sort': {'total_revenue': -1}},
                {'$limit': limit}
            ]

            top_products = list(self.sales_collection.aggregate(pipeline))

            # Rest of your existing summary calculation code remains the same...
            summary_pipeline = [
                {
                    '$match': {
                        'transaction_date': {
                            '$gte': start_datetime,
                            '$lte': end_datetime
                        },
                        'status': 'completed',
                        'is_voided': False,
                        'source': 'pos'
                    }
                },
                {'$unwind': '$items'},
                {
                    '$group': {
                        '_id': None,
                        'total_products_sold': {'$sum': '$items.quantity'},
                        'total_revenue': {'$sum': '$items.subtotal'},
                        'total_orders': {'$addToSet': '$_id'}
                    }
                },
                {
                    '$project': {
                        'total_products_sold': 1,
                        'total_revenue': {'$round': ['$total_revenue', 2]},
                        'total_orders': {'$size': '$total_orders'}
                    }
                }
            ]

            summary_result = list(self.sales_collection.aggregate(summary_pipeline))
            
            if summary_result:
                summary = summary_result[0]
                summary['average_order_value'] = round(
                    summary['total_revenue'] / summary['total_orders'] if summary['total_orders'] > 0 else 0, 
                    2
                )
            else:
                summary = {
                    'total_products_sold': 0,
                    'total_revenue': 0,
                    'total_orders': 0,
                    'average_order_value': 0
                }

            return {
                'date': target_date.isoformat(),
                'top_products': top_products,
                'summary': summary
            }

        except Exception as e:
            logger.error(f"Error getting daily top products: {str(e)}")
            raise Exception(f"Error getting daily top products: {str(e)}")

    # ================================================================
    # 2. TOTAL ORDERS AND REVENUE
    # ================================================================

    def get_total_orders_revenue(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """
        Get total orders and revenue for a date range
        
        Args:
            start_date: Start date (defaults to beginning of current day)
            end_date: End date (defaults to end of current day)
            
        Returns:
            {
                'period': {
                    'start': '2025-10-17T00:00:00',
                    'end': '2025-10-17T23:59:59'
                },
                'total_orders': 25,
                'total_revenue': 3250.50,
                'average_order_value': 130.02,
                'successful_transactions': 25,
                'voided_transactions': 2
            }
        """
        try:
            if start_date is None:
                start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            if end_date is None:
                end_date = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)

            pipeline = [
                {
                    '$match': {
                        'transaction_date': {
                            '$gte': start_date,
                            '$lte': end_date
                        },
                        'source': 'pos'
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'total_orders': {'$sum': 1},
                        'total_revenue': {'$sum': '$total_amount'},
                        'successful_transactions': {
                            '$sum': {
                                '$cond': [
                                    {'$and': [
                                        {'$eq': ['$status', 'completed']},
                                        {'$eq': ['$is_voided', False]}
                                    ]},
                                    1, 0
                                ]
                            }
                        },
                        'voided_transactions': {
                            '$sum': {
                                '$cond': [
                                    {'$eq': ['$is_voided', True]},
                                    1, 0
                                ]
                            }
                        },
                        'successful_revenue': {
                            '$sum': {
                                '$cond': [
                                    {'$and': [
                                        {'$eq': ['$status', 'completed']},
                                        {'$eq': ['$is_voided', False]}
                                    ]},
                                    '$total_amount', 0
                                ]
                            }
                        }
                    }
                },
                {
                    '$project': {
                        'total_orders': 1,
                        'total_revenue': {'$round': ['$total_revenue', 2]},
                        'successful_transactions': 1,
                        'voided_transactions': 1,
                        'successful_revenue': {'$round': ['$successful_revenue', 2]},
                        'average_order_value': {
                            '$cond': [
                                {'$gt': ['$successful_transactions', 0]},
                                {'$round': [
                                    {'$divide': ['$successful_revenue', '$successful_transactions']},
                                    2
                                ]},
                                0
                            ]
                        }
                    }
                }
            ]

            result = list(self.sales_collection.aggregate(pipeline))
            
            if result:
                data = result[0]
            else:
                data = {
                    'total_orders': 0,
                    'total_revenue': 0,
                    'successful_transactions': 0,
                    'voided_transactions': 0,
                    'successful_revenue': 0,
                    'average_order_value': 0
                }

            data['period'] = {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }

            return data

        except Exception as e:
            logger.error(f"Error getting total orders and revenue: {str(e)}")
            raise Exception(f"Error getting total orders and revenue: {str(e)}")

    # ================================================================
    # 3. OVERALL STATISTICS BY CATEGORY
    # ================================================================

    def get_category_statistics(self, period: str = 'week') -> Dict[str, Any]:
        """
        Get revenue statistics by category for different periods
        
        Args:
            period: 'week', 'month', or 'year'
            
        Returns:
            {
                'period': 'week',
                'date_range': {
                    'start': '2025-10-14',
                    'end': '2025-10-20'
                },
                'categories': [
                    {
                        'category_id': 'CTGY-006',
                        'category_name': 'Drinks',
                        'total_revenue': 1500.00,
                        'total_quantity': 45,
                        'product_count': 3,
                        'percentage': 60.0
                    }
                ],
                'summary': {
                    'total_revenue': 2500.00,
                    'total_categories': 5,
                    'top_category': 'Drinks'
                }
            }
        """
        try:
            # Calculate date range based on period
            end_date = datetime.utcnow()
            if period == 'week':
                start_date = end_date - timedelta(days=7)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=7)  # Default to week

            # Start of day for start_date, end of day for end_date
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

            # Get all active categories first
            categories = list(self.category_collection.find({
                'isDeleted': {'$ne': True},
                'status': 'active'
            }))

            # Aggregation pipeline for category revenue
            pipeline = [
                {
                    '$match': {
                        'transaction_date': {
                            '$gte': start_date,
                            '$lte': end_date
                        },
                        'status': 'completed',
                        'is_voided': False,
                        'source': 'pos'
                    }
                },
                {'$unwind': '$items'},
                {
                    '$lookup': {
                        'from': 'products',
                        'localField': 'items.product_id',
                        'foreignField': '_id',
                        'as': 'product_info'
                    }
                },
                {'$unwind': '$product_info'},
                {
                    '$group': {
                        '_id': '$product_info.category_id',
                        'total_revenue': {'$sum': '$items.subtotal'},
                        'total_quantity': {'$sum': '$items.quantity'},
                        'product_count': {'$addToSet': '$items.product_id'},
                        'category_data': {'$first': '$product_info.category_id'}
                    }
                },
                {
                    '$project': {
                        'category_id': '$_id',
                        'total_revenue': {'$round': ['$total_revenue', 2]},
                        'total_quantity': 1,
                        'product_count': {'$size': '$product_count'}
                    }
                },
                {'$sort': {'total_revenue': -1}}
            ]

            category_stats = list(self.sales_collection.aggregate(pipeline))

            # Enrich with category names and calculate percentages
            enriched_categories = []
            total_revenue = sum(cat['total_revenue'] for cat in category_stats)

            for cat_stat in category_stats:
                category_id = cat_stat['category_id']
                
                # Find category details
                category_details = next(
                    (cat for cat in categories if cat['_id'] == category_id), 
                    None
                )
                
                if category_details:
                    category_name = category_details.get('category_name', 'Unknown')
                else:
                    category_name = 'Uncategorized'

                percentage = round(
                    (cat_stat['total_revenue'] / total_revenue * 100) if total_revenue > 0 else 0, 
                    2
                )

                enriched_categories.append({
                    'category_id': category_id,
                    'category_name': category_name,
                    'total_revenue': cat_stat['total_revenue'],
                    'total_quantity': cat_stat['total_quantity'],
                    'product_count': cat_stat['product_count'],
                    'percentage': percentage
                })

            # Summary
            summary = {
                'total_revenue': round(total_revenue, 2),
                'total_categories': len(enriched_categories),
                'top_category': enriched_categories[0]['category_name'] if enriched_categories else 'None'
            }

            return {
                'period': period,
                'date_range': {
                    'start': start_date.date().isoformat(),
                    'end': end_date.date().isoformat()
                },
                'categories': enriched_categories,
                'summary': summary
            }

        except Exception as e:
            logger.error(f"Error getting category statistics: {str(e)}")
            raise Exception(f"Error getting category statistics: {str(e)}")

    # ================================================================
    # 4. COMPREHENSIVE DASHBOARD DATA
    # ================================================================

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data including all three components
        
        Returns:
            Combined data for daily top products, total orders/revenue, and category statistics
        """
        try:
            # Get today's date for consistent reporting
            today = datetime.utcnow()
            
            # Parallel execution for performance
            daily_top_products = self.get_daily_top_products(today)
            total_orders_revenue = self.get_total_orders_revenue()
            category_stats_week = self.get_category_statistics('week')
            category_stats_month = self.get_category_statistics('month')

            return {
                'daily_analysis': daily_top_products,
                'revenue_analysis': total_orders_revenue,
                'category_analysis': {
                    'weekly': category_stats_week,
                    'monthly': category_stats_month
                },
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            raise Exception(f"Error getting dashboard data: {str(e)}")

    # ================================================================
    # 5. CUSTOM DATE RANGE ANALYTICS
    # ================================================================

    def get_custom_range_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get analytics for a custom date range
        
        Args:
            start_date: Start datetime
            end_date: End datetime
            
        Returns:
            Comprehensive analytics for the custom period
        """
        try:
            # Ensure proper datetime range
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

            # Get top products for the period
            pipeline_products = [
                {
                    '$match': {
                        'transaction_date': {
                            '$gte': start_date,
                            '$lte': end_date
                        },
                        'status': 'completed',
                        'is_voided': False,
                        'source': 'pos'
                    }
                },
                {'$unwind': '$items'},
                {
                    '$group': {
                        '_id': {
                            'product_id': '$items.product_id',
                            'product_name': '$items.product_name'
                        },
                        'total_quantity': {'$sum': '$items.quantity'},
                        'total_revenue': {'$sum': '$items.subtotal'},
                        'unit_price': {'$avg': '$items.unit_price'}
                    }
                },
                {
                    '$project': {
                        'product_id': '$_id.product_id',
                        'product_name': '$_id.product_name',
                        'total_quantity': 1,
                        'total_revenue': {'$round': ['$total_revenue', 2]},
                        'unit_price': {'$round': ['$unit_price', 2]}
                    }
                },
                {'$sort': {'total_revenue': -1}},
                {'$limit': 20}
            ]

            top_products = list(self.sales_collection.aggregate(pipeline_products))

            # Get category breakdown
            pipeline_categories = [
                {
                    '$match': {
                        'transaction_date': {
                            '$gte': start_date,
                            '$lte': end_date
                        },
                        'status': 'completed',
                        'is_voided': False,
                        'source': 'pos'
                    }
                },
                {'$unwind': '$items'},
                {
                    '$lookup': {
                        'from': 'products',
                        'localField': 'items.product_id',
                        'foreignField': '_id',
                        'as': 'product_info'
                    }
                },
                {'$unwind': '$product_info'},
                {
                    '$group': {
                        '_id': '$product_info.category_id',
                        'total_revenue': {'$sum': '$items.subtotal'},
                        'total_quantity': {'$sum': '$items.quantity'}
                    }
                },
                {
                    '$lookup': {
                        'from': 'category',
                        'localField': '_id',
                        'foreignField': '_id',
                        'as': 'category_info'
                    }
                },
                {'$unwind': '$category_info'},
                {
                    '$project': {
                        'category_id': '$_id',
                        'category_name': '$category_info.category_name',
                        'total_revenue': {'$round': ['$total_revenue', 2]},
                        'total_quantity': 1
                    }
                },
                {'$sort': {'total_revenue': -1}}
            ]

            category_breakdown = list(self.sales_collection.aggregate(pipeline_categories))

            # Get overall summary
            pipeline_summary = [
                {
                    '$match': {
                        'transaction_date': {
                            '$gte': start_date,
                            '$lte': end_date
                        },
                        'source': 'pos'
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'total_transactions': {'$sum': 1},
                        'total_revenue': {'$sum': '$total_amount'},
                        'successful_transactions': {
                            '$sum': {
                                '$cond': [
                                    {'$and': [
                                        {'$eq': ['$status', 'completed']},
                                        {'$eq': ['$is_voided', False]}
                                    ]},
                                    1, 0
                                ]
                            }
                        },
                        'total_items_sold': {
                            '$sum': {
                                '$size': '$items'
                            }
                        }
                    }
                }
            ]

            summary_result = list(self.sales_collection.aggregate(pipeline_summary))
            summary = summary_result[0] if summary_result else {
                'total_transactions': 0,
                'total_revenue': 0,
                'successful_transactions': 0,
                'total_items_sold': 0
            }

            return {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'top_products': top_products,
                'category_breakdown': category_breakdown,
                'summary': {
                    'total_transactions': summary['total_transactions'],
                    'successful_transactions': summary['successful_transactions'],
                    'total_revenue': round(summary.get('total_revenue', 0), 2),
                    'total_items_sold': summary.get('total_items_sold', 0),
                    'success_rate': round(
                        (summary['successful_transactions'] / summary['total_transactions'] * 100) 
                        if summary['total_transactions'] > 0 else 0, 
                        2
                    )
                }
            }

        except Exception as e:
            logger.error(f"Error getting custom range analytics: {str(e)}")
            raise Exception(f"Error getting custom range analytics: {str(e)}")