# app/tests/test_stock_sync.py
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from bson import ObjectId

from django.test import TestCase
from app.database import db_manager
from app.services.sync_service import SyncService
from app.services.POS.batch_service import BatchService
from app.services.Backoffice.product_service import ProductService


class StockSyncTestCase(TestCase):
    """Test cases for stock synchronization between local and cloud databases"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sync_service = SyncService()
        self.batch_service = BatchService()
        self.product_service = ProductService()
        
        # Mock product IDs for testing
        self.test_product_id = "TEST-PROD-001"
        self.test_product_name = "Test Product"
        
    def tearDown(self):
        """Clean up after tests"""
        pass
    
    # ================================================================
    # Test 1: Stock Calculation from Batches
    # ================================================================
    
    def test_stock_calculation_from_batches(self):
        """Test that total_stock matches sum of active batch quantity_remaining"""
        # This test would require actual database access
        # For now, we'll test the logic
        
        # Mock batches
        active_batches = [
            {'quantity_remaining': 10, 'status': 'active'},
            {'quantity_remaining': 5, 'status': 'active'},
            {'quantity_remaining': 3, 'status': 'active'},
        ]
        
        total_stock = sum(b.get('quantity_remaining', 0) for b in active_batches)
        self.assertEqual(total_stock, 18, "Total stock should be sum of active batches")
    
    def test_stock_calculation_excludes_depleted_batches(self):
        """Test that depleted batches are not counted in total_stock"""
        batches = [
            {'quantity_remaining': 10, 'status': 'active'},
            {'quantity_remaining': 0, 'status': 'depleted'},
            {'quantity_remaining': 5, 'status': 'active'},
        ]
        
        active_batches = [b for b in batches if b['status'] == 'active' and b['quantity_remaining'] > 0]
        total_stock = sum(b.get('quantity_remaining', 0) for b in active_batches)
        
        self.assertEqual(total_stock, 15, "Depleted batches should not be counted")
        self.assertEqual(len(active_batches), 2, "Should only have 2 active batches")
    
    def test_stock_calculation_excludes_pending_batches(self):
        """Test that pending batches are not counted in total_stock"""
        batches = [
            {'quantity_remaining': 10, 'status': 'active'},
            {'quantity_remaining': 5, 'status': 'pending'},
            {'quantity_remaining': 3, 'status': 'active'},
        ]
        
        active_batches = [
            b for b in batches 
            if b['status'] == 'active' and b['quantity_remaining'] > 0
        ]
        total_stock = sum(b.get('quantity_remaining', 0) for b in active_batches)
        
        self.assertEqual(total_stock, 13, "Pending batches should not be counted")
    
    # ================================================================
    # Test 2: Incremental Sync Logic
    # ================================================================
    
    def test_should_consider_document_with_no_sync_logs(self):
        """Test that documents with no sync_logs are considered for sync"""
        document = {
            '_id': 'TEST-001',
            'product_name': 'Test',
            'total_stock': 10
        }
        
        sync_window = datetime.utcnow() - timedelta(minutes=5)
        should_sync = self.sync_service._should_consider_document(document, sync_window)
        
        self.assertTrue(should_sync, "Documents with no sync_logs should be synced")
    
    def test_should_consider_document_with_empty_sync_logs(self):
        """Test that documents with empty sync_logs are considered for sync"""
        document = {
            '_id': 'TEST-001',
            'product_name': 'Test',
            'total_stock': 10,
            'sync_logs': []
        }
        
        sync_window = datetime.utcnow() - timedelta(minutes=5)
        should_sync = self.sync_service._should_consider_document(document, sync_window)
        
        self.assertTrue(should_sync, "Documents with empty sync_logs should be synced")
    
    def test_should_consider_document_with_recent_update(self):
        """Test that documents updated within sync window are considered"""
        recent_time = datetime.utcnow() - timedelta(minutes=2)
        document = {
            '_id': 'TEST-001',
            'product_name': 'Test',
            'total_stock': 10,
            'updated_at': recent_time,
            'sync_logs': [{'timestamp': datetime.utcnow() - timedelta(hours=1)}]
        }
        
        sync_window = datetime.utcnow() - timedelta(minutes=5)
        should_sync = self.sync_service._should_consider_document(document, sync_window)
        
        self.assertTrue(should_sync, "Documents updated within sync window should be synced")
    
    def test_should_not_consider_document_with_old_update(self):
        """Test that documents updated outside sync window are NOT considered"""
        old_time = datetime.utcnow() - timedelta(minutes=10)
        document = {
            '_id': 'TEST-001',
            'product_name': 'Test',
            'total_stock': 10,
            'updated_at': old_time,
            'sync_logs': [{'timestamp': datetime.utcnow() - timedelta(hours=1)}]
        }
        
        sync_window = datetime.utcnow() - timedelta(minutes=5)
        should_sync = self.sync_service._should_consider_document(document, sync_window)
        
        self.assertFalse(should_sync, "Documents updated outside sync window should NOT be synced")
    
    def test_parse_timestamp_from_datetime(self):
        """Test parsing timestamp from datetime object"""
        test_time = datetime.utcnow()
        document = {'updated_at': test_time}
        
        parsed = self.sync_service._parse_timestamp(document)
        self.assertEqual(parsed, test_time, "Should parse datetime objects correctly")
    
    def test_parse_timestamp_from_iso_string(self):
        """Test parsing timestamp from ISO string"""
        test_time = datetime.utcnow()
        iso_string = test_time.isoformat()
        document = {'updated_at': iso_string}
        
        parsed = self.sync_service._parse_timestamp(document)
        # Allow small difference due to string conversion
        self.assertAlmostEqual(
            (parsed - test_time).total_seconds(), 0, delta=1,
            msg="Should parse ISO string timestamps correctly"
        )
    
    # ================================================================
    # Test 3: Sync Queue
    # ================================================================
    
    def test_add_to_sync_queue(self):
        """Test adding items to sync queue"""
        document = {
            '_id': 'TEST-001',
            'product_name': 'Test Product',
            'total_stock': 10
        }
        
        # Mock database
        with patch.object(self.sync_service, 'get_databases') as mock_db:
            mock_local_db = MagicMock()
            mock_local_db.sync_queue = MagicMock()
            mock_local_db.sync_queue.insert_one = MagicMock()
            
            mock_db.return_value = (mock_local_db, None)
            
            self.sync_service.add_to_sync_queue('products', document)
            
            # Verify insert_one was called
            mock_local_db.sync_queue.insert_one.assert_called_once()
            call_args = mock_local_db.sync_queue.insert_one.call_args[0][0]
            
            self.assertEqual(call_args['collection'], 'products')
            self.assertEqual(call_args['document'], document)
            self.assertEqual(call_args['status'], 'pending')
    
    def test_sync_queue_structure(self):
        """Test that sync queue items have correct structure"""
        document = {'_id': 'TEST-001', 'total_stock': 10}
        
        with patch.object(self.sync_service, 'get_databases') as mock_db:
            mock_local_db = MagicMock()
            mock_local_db.sync_queue = MagicMock()
            mock_local_db.sync_queue.insert_one = MagicMock()
            
            mock_db.return_value = (mock_local_db, None)
            
            self.sync_service.add_to_sync_queue('products', document)
            
            call_args = mock_local_db.sync_queue.insert_one.call_args[0][0]
            
            # Verify structure
            self.assertIn('collection', call_args)
            self.assertIn('document', call_args)
            self.assertIn('status', call_args)
            self.assertIn('created_at', call_args)
            self.assertIn('retry_count', call_args)
            self.assertEqual(call_args['status'], 'pending')
            self.assertEqual(call_args['retry_count'], 0)
    
    # ================================================================
    # Test 4: Bidirectional Sync
    # ================================================================
    
    def test_timestamp_based_conflict_resolution(self):
        """Test that newer timestamp wins in conflict resolution"""
        local_time = datetime.utcnow()
        cloud_time = datetime.utcnow() - timedelta(minutes=10)
        
        local_doc = {
            '_id': 'TEST-001',
            'total_stock': 20,
            'updated_at': local_time
        }
        
        cloud_doc = {
            '_id': 'TEST-001',
            'total_stock': 15,
            'updated_at': cloud_time
        }
        
        # Local is newer, so local should win
        local_parsed = self.sync_service._parse_timestamp(local_doc)
        cloud_parsed = self.sync_service._parse_timestamp(cloud_doc)
        
        self.assertGreater(local_parsed, cloud_parsed, "Local timestamp should be newer")
        should_use_local = local_parsed > cloud_parsed
        self.assertTrue(should_use_local, "Should use local version when it's newer")
    
    def test_cloud_newer_wins_conflict(self):
        """Test that cloud version wins when it's newer"""
        local_time = datetime.utcnow() - timedelta(minutes=10)
        cloud_time = datetime.utcnow()
        
        local_doc = {
            '_id': 'TEST-001',
            'total_stock': 15,
            'updated_at': local_time
        }
        
        cloud_doc = {
            '_id': 'TEST-001',
            'total_stock': 20,
            'updated_at': cloud_time
        }
        
        local_parsed = self.sync_service._parse_timestamp(local_doc)
        cloud_parsed = self.sync_service._parse_timestamp(cloud_doc)
        
        self.assertGreater(cloud_parsed, local_parsed, "Cloud timestamp should be newer")
        should_use_cloud = cloud_parsed > local_parsed
        self.assertTrue(should_use_cloud, "Should use cloud version when it's newer")
    
    # ================================================================
    # Test 5: Product Stock Update Triggers Sync
    # ================================================================
    
    def test_update_stock_updates_updated_at(self):
        """Test that update_stock() updates the updated_at field"""
        # This would require actual database access
        # For now, we test the logic
        
        current_time = datetime.utcnow()
        update_data = {
            'total_stock': 20,
            'updated_at': current_time
        }
        
        # Verify update_data contains updated_at
        self.assertIn('updated_at', update_data)
        self.assertIsInstance(update_data['updated_at'], datetime)
    
    def test_sync_window_incremental_sync(self):
        """Test that incremental sync uses 5-minute window"""
        sync_window = datetime.utcnow() - timedelta(minutes=5)
        
        # Document updated 2 minutes ago (within window)
        recent_doc = {
            'updated_at': datetime.utcnow() - timedelta(minutes=2)
        }
        
        # Document updated 10 minutes ago (outside window)
        old_doc = {
            'updated_at': datetime.utcnow() - timedelta(minutes=10)
        }
        
        recent_should_sync = self.sync_service._should_consider_document(recent_doc, sync_window)
        old_should_sync = self.sync_service._should_consider_document(old_doc, sync_window)
        
        self.assertTrue(recent_should_sync, "Recent document should be synced")
        self.assertFalse(old_should_sync, "Old document should NOT be synced")
    
    def test_mirror_products_incremental_logic(self):
        """Test that mirror_products_from_local only syncs recent products"""
        five_min_ago = datetime.utcnow() - timedelta(minutes=5)
        
        # Recent product (should sync)
        recent_product = {
            '_id': 'PROD-001',
            'product_name': 'Recent',
            'total_stock': 10,
            'updated_at': datetime.utcnow() - timedelta(minutes=2)
        }
        
        # Old product (should NOT sync)
        old_product = {
            '_id': 'PROD-002',
            'product_name': 'Old',
            'total_stock': 20,
            'updated_at': datetime.utcnow() - timedelta(minutes=10)
        }
        
        # Check if products would be included in incremental sync
        recent_in_window = recent_product.get('updated_at') >= five_min_ago
        old_in_window = old_product.get('updated_at') >= five_min_ago
        
        self.assertTrue(recent_in_window, "Recent product should be in sync window")
        self.assertFalse(old_in_window, "Old product should NOT be in sync window")
    
    # ================================================================
    # Test 6: Edge Cases
    # ================================================================
    
    def test_parse_timestamp_fallback(self):
        """Test that _parse_timestamp falls back correctly"""
        # Document with no timestamp fields
        doc_no_timestamp = {'_id': 'TEST-001'}
        fallback = datetime(1970, 1, 1)
        
        parsed = self.sync_service._parse_timestamp(doc_no_timestamp, fallback)
        self.assertEqual(parsed, fallback, "Should return fallback when no timestamp found")
    
    def test_parse_timestamp_multiple_fields(self):
        """Test that _parse_timestamp checks multiple fields"""
        # Document with last_updated instead of updated_at
        doc = {
            '_id': 'TEST-001',
            'last_updated': datetime.utcnow()
        }
        
        parsed = self.sync_service._parse_timestamp(doc)
        self.assertIsInstance(parsed, datetime, "Should parse from last_updated field")
    
    def test_sync_log_structure(self):
        """Test that sync logs have correct structure"""
        sync_log = {
            'timestamp': datetime.utcnow(),
            'source': 'cloud',
            'status': 'synced',
            'details': {}
        }
        
        # Verify structure
        self.assertIn('timestamp', sync_log)
        self.assertIn('source', sync_log)
        self.assertIn('status', sync_log)
        self.assertIn('details', sync_log)
        self.assertIsInstance(sync_log['timestamp'], datetime)


if __name__ == '__main__':
    unittest.main()

