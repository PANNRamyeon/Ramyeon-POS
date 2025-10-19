from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from ...services.POS.pos_reports_service import POSReportsService
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DailyTopProductsView(APIView):
    """GET /api/analytics/daily-top-products/ - Get daily top products"""
    
    def get(self, request):
        try:
            analytics_service = POSReportsService()
            
            # Get query parameters
            date_str = request.query_params.get('date')
            limit = int(request.query_params.get('limit', 10))
            
            target_date = None
            if date_str:
                try:
                    target_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except ValueError:
                    return Response({
                        'success': False,
                        'error': 'Invalid date format. Use ISO format (YYYY-MM-DD)'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            result = analytics_service.get_daily_top_products(target_date, limit)
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Failed to get daily top products: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TotalOrdersRevenueView(APIView):
    """GET /api/analytics/total-orders-revenue/ - Get total orders and revenue"""
    
    def get(self, request):
        try:
            analytics_service = POSReportsService()
            
            # Get query parameters
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            
            start_date = None
            end_date = None
            
            if start_date_str:
                try:
                    start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                except ValueError:
                    return Response({
                        'success': False,
                        'error': 'Invalid start_date format. Use ISO format'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            if end_date_str:
                try:
                    end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                except ValueError:
                    return Response({
                        'success': False,
                        'error': 'Invalid end_date format. Use ISO format'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            result = analytics_service.get_total_orders_revenue(start_date, end_date)
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Failed to get total orders and revenue: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CategoryStatisticsView(APIView):
    """GET /api/analytics/category-statistics/ - Get category statistics"""
    
    def get(self, request):
        try:
            analytics_service = POSReportsService()
            
            # Get period parameter (week, month, year)
            period = request.query_params.get('period', 'week')
            
            if period not in ['week', 'month', 'year']:
                return Response({
                    'success': False,
                    'error': 'Invalid period. Must be: week, month, or year'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = analytics_service.get_category_statistics(period)
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Failed to get category statistics: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DashboardDataView(APIView):
    """GET /api/analytics/dashboard/ - Get comprehensive dashboard data"""
    
    def get(self, request):
        try:
            analytics_service = POSReportsService()
            
            print(f"\n{'='*50}")
            print(f"📊 DASHBOARD DATA REQUEST")
            print(f"{'='*50}")
            print(f"User: {getattr(request.user, 'username', 'Anonymous')}")
            print(f"Timestamp: {datetime.utcnow().isoformat()}")
            
            result = analytics_service.get_dashboard_data()
            
            print(f"✅ Dashboard data retrieved successfully")
            print(f"   Daily Analysis: {len(result.get('daily_analysis', {}).get('top_products', []))} products")
            print(f"   Category Analysis: {len(result.get('category_analysis', {}).get('weekly', {}).get('categories', []))} categories")
            print(f"{'='*50}\n")
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ Dashboard error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Failed to get dashboard data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomRangeAnalyticsView(APIView):
    """GET /api/analytics/custom-range/ - Get analytics for custom date range"""
    
    def get(self, request):
        try:
            analytics_service = POSReportsService()
            
            # Get required query parameters
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            
            if not start_date_str or not end_date_str:
                return Response({
                    'success': False,
                    'error': 'Both start_date and end_date are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate date range
            if start_date > end_date:
                return Response({
                    'success': False,
                    'error': 'start_date cannot be after end_date'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"\n{'='*50}")
            print(f"📈 CUSTOM RANGE ANALYTICS REQUEST")
            print(f"{'='*50}")
            print(f"Start Date: {start_date.isoformat()}")
            print(f"End Date: {end_date.isoformat()}")
            
            result = analytics_service.get_custom_range_analytics(start_date, end_date)
            
            print(f"✅ Custom range analytics retrieved")
            print(f"   Top Products: {len(result.get('top_products', []))}")
            print(f"   Categories: {len(result.get('category_breakdown', []))}")
            print(f"   Total Revenue: {result.get('summary', {}).get('total_revenue', 0)}")
            print(f"{'='*50}\n")
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ Custom range analytics error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Failed to get custom range analytics: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RealTimeSalesDataView(APIView):
    """GET /api/analytics/real-time-sales/ - Get real-time sales data for today"""
    
    def get(self, request):
        try:
            analytics_service = POSReportsService()
            
            # Get today's data
            today = datetime.utcnow()
            start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            print(f"\n{'='*50}")
            print(f"🔄 REAL-TIME SALES DATA REQUEST")
            print(f"{'='*50}")
            print(f"Today: {today.date().isoformat()}")
            
            # Get today's top products (limit to 5 for real-time view)
            daily_data = analytics_service.get_daily_top_products(today, 5)
            
            # Get today's total orders and revenue
            revenue_data = analytics_service.get_total_orders_revenue(start_of_day, end_of_day)
            
            # Get hourly breakdown for today
            hourly_data = self._get_hourly_sales_data(start_of_day, end_of_day)
            
            result = {
                'date': today.date().isoformat(),
                'timestamp': datetime.utcnow().isoformat(),
                'top_products': daily_data.get('top_products', []),
                'revenue_summary': revenue_data,
                'hourly_breakdown': hourly_data,
                'summary': daily_data.get('summary', {})
            }
            
            print(f"✅ Real-time data retrieved")
            print(f"   Current Hour: {today.hour}:00")
            print(f"   Today's Revenue: {revenue_data.get('successful_revenue', 0)}")
            print(f"   Today's Orders: {revenue_data.get('successful_transactions', 0)}")
            print(f"{'='*50}\n")
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ Real-time sales data error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Failed to get real-time sales data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_hourly_sales_data(self, start_date, end_date):
        """Get hourly sales breakdown for the day"""
        try:
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
                {
                    '$group': {
                        '_id': {
                            'hour': {'$hour': '$transaction_date'}
                        },
                        'total_revenue': {'$sum': '$total_amount'},
                        'transaction_count': {'$sum': 1}
                    }
                },
                {
                    '$project': {
                        'hour': '$_id.hour',
                        'total_revenue': {'$round': ['$total_revenue', 2]},
                        'transaction_count': 1
                    }
                },
                {'$sort': {'hour': 1}}
            ]
            
            from ...database import db_manager
            db = db_manager.get_database()
            sales_collection = db.sales
            
            hourly_data = list(sales_collection.aggregate(pipeline))
            
            # Fill in missing hours with zero values
            complete_hourly_data = []
            for hour in range(24):
                hour_data = next((h for h in hourly_data if h['hour'] == hour), None)
                if hour_data:
                    complete_hourly_data.append(hour_data)
                else:
                    complete_hourly_data.append({
                        'hour': hour,
                        'total_revenue': 0,
                        'transaction_count': 0
                    })
            
            return complete_hourly_data
            
        except Exception as e:
            logger.error(f"Error getting hourly sales data: {str(e)}")
            return []

class ProductPerformanceView(APIView):
    """GET /api/analytics/product-performance/ - Get detailed product performance"""
    
    def get(self, request):
        try:
            analytics_service = POSReportsService()
            
            # Get query parameters
            product_id = request.query_params.get('product_id')
            days_back = int(request.query_params.get('days', 30))
            
            if not product_id:
                return Response({
                    'success': False,
                    'error': 'product_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            print(f"\n{'='*50}")
            print(f"📊 PRODUCT PERFORMANCE REQUEST")
            print(f"{'='*50}")
            print(f"Product ID: {product_id}")
            print(f"Period: {days_back} days")
            
            result = self._get_product_performance(product_id, start_date, end_date)
            
            print(f"✅ Product performance data retrieved")
            print(f"   Total Sales: {result.get('total_sales', 0)}")
            print(f"   Total Revenue: {result.get('total_revenue', 0)}")
            print(f"{'='*50}\n")
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ Product performance error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Failed to get product performance: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_product_performance(self, product_id, start_date, end_date):
        """Get detailed performance data for a specific product"""
        try:
            from ...database import db_manager
            db = db_manager.get_database()
            sales_collection = db.sales
            
            pipeline = [
                {
                    '$match': {
                        'transaction_date': {
                            '$gte': start_date,
                            '$lte': end_date
                        },
                        'status': 'completed',
                        'is_voided': False,
                        'source': 'pos',
                        'items.product_id': product_id
                    }
                },
                {'$unwind': '$items'},
                {
                    '$match': {
                        'items.product_id': product_id
                    }
                },
                {
                    '$group': {
                        '_id': '$items.product_id',
                        'total_quantity': {'$sum': '$items.quantity'},
                        'total_revenue': {'$sum': '$items.subtotal'},
                        'average_price': {'$avg': '$items.unit_price'},
                        'transaction_count': {'$sum': 1},
                        'daily_breakdown': {
                            '$push': {
                                'date': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$transaction_date'}},
                                'quantity': '$items.quantity',
                                'revenue': '$items.subtotal'
                            }
                        }
                    }
                },
                {
                    '$project': {
                        'product_id': '$_id',
                        'total_quantity': 1,
                        'total_revenue': {'$round': ['$total_revenue', 2]},
                        'average_price': {'$round': ['$average_price', 2]},
                        'transaction_count': 1,
                        'daily_breakdown': 1
                    }
                }
            ]
            
            result = list(sales_collection.aggregate(pipeline))
            
            if result:
                return result[0]
            else:
                return {
                    'product_id': product_id,
                    'total_quantity': 0,
                    'total_revenue': 0,
                    'average_price': 0,
                    'transaction_count': 0,
                    'daily_breakdown': []
                }
                
        except Exception as e:
            logger.error(f"Error getting product performance: {str(e)}")
            return {
                'product_id': product_id,
                'total_quantity': 0,
                'total_revenue': 0,
                'average_price': 0,
                'transaction_count': 0,
                'daily_breakdown': []
            }