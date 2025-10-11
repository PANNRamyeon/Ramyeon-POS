# backend/views/backoffice/saleslog_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from datetime import datetime
import csv
import json
from ...services.Backoffice.sales_log_service import SalesLogService

class SalesLogCreateView(APIView):
    """
    POST /api/v1/backoffice/saleslogs/create/
    Create manual sales log entry
    
    Body: {
        "customer_id": "CUST-00001",  // optional
        "transaction_date": "2025-10-05T12:00:00Z",
        "items": [
            {
                "product_id": "PROD-00002",
                "product_name": "C2 Solo Lemon",
                "quantity": 3,
                "unit_price": 156.00,
                "total_price": 468.00
            }
        ],
        "total_amount": 468.00,
        "payment_method": "cash",
        "sales_type": "retail",  // retail, wholesale, delivery
        "tax_amount": 0,
        "notes": "Phone order"
    }
    """
    def post(self, request):
        try:
            user_id = request.data.get('user_id') or request.user.get('user_id', 'UNKNOWN')
            
            saleslog_service = SalesLogService()
            log = saleslog_service.create_manual_sale(request.data, user_id)
            
            return Response({
                'success': True,
                'data': log,
                'message': f'Sales log {log["_id"]} created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesLogListView(APIView):
    """
    GET /api/v1/backoffice/saleslogs/
    List all sales logs with pagination and filters
    
    Query params:
        - page (default: 1)
        - page_size (default: 50)
        - start_date (ISO format)
        - end_date (ISO format)
        - sales_type (retail/wholesale/delivery)
        - source (manual/csv_import)
        - payment_method
        - customer_id
        - user_id
        - include_deleted (true/false)
    """
    def get(self, request):
        try:
            # Pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 50))
            include_deleted = request.query_params.get('include_deleted', 'false').lower() == 'true'
            
            # Filters
            filters = {}
            if request.query_params.get('start_date'):
                filters['start_date'] = datetime.fromisoformat(
                    request.query_params.get('start_date').replace('Z', '+00:00')
                )
            if request.query_params.get('end_date'):
                filters['end_date'] = datetime.fromisoformat(
                    request.query_params.get('end_date').replace('Z', '+00:00')
                )
            if request.query_params.get('sales_type'):
                filters['sales_type'] = request.query_params.get('sales_type')
            if request.query_params.get('source'):
                filters['source'] = request.query_params.get('source')
            if request.query_params.get('payment_method'):
                filters['payment_method'] = request.query_params.get('payment_method')
            if request.query_params.get('customer_id'):
                filters['customer_id'] = request.query_params.get('customer_id')
            if request.query_params.get('user_id'):
                filters['user_id'] = request.query_params.get('user_id')
            
            saleslog_service = SalesLogService()
            result = saleslog_service.get_all_saleslogs(
                page=page,
                page_size=page_size,
                filters=filters,
                include_deleted=include_deleted
            )
            
            return Response({
                'success': True,
                'data': result['data'],
                'pagination': result['pagination'],
                'filters_applied': result['filters_applied']
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesLogDetailView(APIView):
    """
    Combined view for GET and DELETE
    GET /api/v1/backoffice/saleslogs/{log_id}/ - Get details
    DELETE /api/v1/backoffice/saleslogs/{log_id}/ - Soft delete
    """
    def get(self, request, log_id):
        try:
            saleslog_service = SalesLogService()
            log = saleslog_service.get_saleslog_by_id(log_id)
            
            if not log:
                return Response({
                    'success': False,
                    'error': f'Sales log {log_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'success': True,
                'data': log
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, log_id):
        try:
            user_id = request.data.get('user_id') or request.user.get('user_id', 'UNKNOWN')
            
            saleslog_service = SalesLogService()
            success = saleslog_service.delete_saleslog(log_id, user_id)
            
            if not success:
                return Response({
                    'success': False,
                    'error': f'Sales log {log_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'success': True,
                'message': f'Sales log {log_id} deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesLogUpdateView(APIView):
    """
    PUT /api/v1/backoffice/saleslogs/{log_id}/update/
    Update existing sales log
    
    Body: Any fields from create (partial update supported)
    """
    def put(self, request, log_id):
        try:
            user_id = request.data.get('user_id') or request.user.get('user_id', 'UNKNOWN')
            
            saleslog_service = SalesLogService()
            updated_log = saleslog_service.update_saleslog(log_id, request.data, user_id)
            
            if not updated_log:
                return Response({
                    'success': False,
                    'error': f'Sales log {log_id} not found or not modified'
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'success': True,
                'data': updated_log,
                'message': f'Sales log {log_id} updated successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesLogImportCSVView(APIView):
    """
    POST /api/v1/backoffice/saleslogs/import-csv/
    Import sales from CSV file
    
    Body: multipart/form-data with 'file' field
    """
    def post(self, request):
        try:
            user_id = request.data.get('user_id') or request.user.get('user_id', 'UNKNOWN')
            
            if 'file' not in request.FILES:
                return Response({
                    'success': False,
                    'error': 'No file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            csv_file = request.FILES['file']
            
            # Parse CSV
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            csv_reader = csv.DictReader(decoded_file)
            csv_data = list(csv_reader)
            
            saleslog_service = SalesLogService()
            results = saleslog_service.import_from_csv(csv_data, user_id)
            
            return Response({
                'success': True,
                'data': results,
                'message': f'Imported {len(results["successful"])} of {results["total_processed"]} records'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesLogExportCSVView(APIView):
    """
    GET /api/v1/backoffice/saleslogs/export-csv/
    Export sales logs to CSV
    
    Query params: Same filters as list view
    """
    def get(self, request):
        try:
            # Build filters
            filters = {}
            if request.query_params.get('start_date'):
                filters['start_date'] = datetime.fromisoformat(
                    request.query_params.get('start_date').replace('Z', '+00:00')
                )
            if request.query_params.get('end_date'):
                filters['end_date'] = datetime.fromisoformat(
                    request.query_params.get('end_date').replace('Z', '+00:00')
                )
            if request.query_params.get('sales_type'):
                filters['sales_type'] = request.query_params.get('sales_type')
            
            saleslog_service = SalesLogService()
            export_data = saleslog_service.export_to_csv(filters)
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="sales_log_export.csv"'
            
            if export_data:
                writer = csv.DictWriter(response, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)
            
            return response
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesLogSummaryView(APIView):
    """
    GET /api/v1/backoffice/saleslogs/summary/
    Get sales summary report
    
    Query params:
        - start_date (required)
        - end_date (required)
        - group_by (day/month/year, default: day)
    """
    def get(self, request):
        try:
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            
            if not start_date_str or not end_date_str:
                return Response({
                    'success': False,
                    'error': 'start_date and end_date are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            group_by = request.query_params.get('group_by', 'day')
            
            saleslog_service = SalesLogService()
            summary = saleslog_service.get_sales_summary(start_date, end_date, group_by)
            
            return Response({
                'success': True,
                'data': summary,
                'group_by': group_by
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)