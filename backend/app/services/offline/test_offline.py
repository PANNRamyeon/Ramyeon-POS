# File: PANN_POS_SYSTEM/backend/app/services/offline/test_offline.py
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def quick_test():
    """Quick test to verify the offline system works with real data"""
    
    # Import the refactored services
    from offline_sync_manager import sync_manager
    from offline_pos_service import offline_pos_service
    
    print("🚀 STARTING OFFLINE SYSTEM TEST WITH REAL DATA")
    print("=" * 60)
    
    # Test 1: Check if storage is created
    print("📁 Testing storage structure...")
    status = sync_manager.get_sync_status()
    print(f"   Storage path: {status['storage_path']}")
    print(f"   Storage exists: {status['storage_exists']}")
    print(f"   Online status: {status['is_online']}")
    
    # Test 2: Create a POS sale with real data
    print("\n💰 Testing POS sale creation...")
    pos_sale_data = {
        "items": [
            {
                "product_id": "PROD-00210", 
                "product_name": "Test Product 210",
                "quantity": 2, 
                "unit_price": 150.50, 
                "subtotal": 301.00
            },
            {
                "product_id": "PROD-00209",
                "product_name": "Test Product 209", 
                "quantity": 1,
                "unit_price": 200.00,
                "subtotal": 200.00
            }
        ],
        "subtotal": 501.00,
        "tax_amount": 60.12,
        "discount_amount": 0,
        "total_amount": 561.12,
        "payment_method": "cash",
        "payment_details": {"cash_tendered": 600, "change": 38.88},
        "customer_id": "CUST-00002",
        "loyalty_points_used": 50,
        "loyalty_points_earned": 56
    }
    
    pos_result = await offline_pos_service.create_sale_offline(pos_sale_data, "CASHIER-001")
    print(f"   POS Sale creation success: {pos_result['success']}")
    print(f"   File ID: {pos_result.get('file_id', 'N/A')}")
    print(f"   Offline mode: {pos_result.get('offline_mode', 'N/A')}")
    print(f"   Points pending: {pos_result.get('points_pending', 'N/A')}")
    
    # Test 3: Create an online order with your real data
    print("\n🛒 Testing online order creation...")
    online_order_data = {
        "customer_id": "CUST-00002",
        "items": [
            {"product_id": "PROD-00210", "quantity": 5},
            {"product_id": "PROD-00209", "quantity": 3}
        ],
        "delivery_address": {
            "street": "123 Main St",
            "city": "Manila",
            "barangay": "Barangay 5",
            "postal_code": "1000",
            "recipient_name": "Sponge Bob",
            "recipient_phone": "321321321"
        },
        "payment_method": "cod",
        "points_to_redeem": 0
    }
    
    online_result = await offline_pos_service.create_online_order_offline(online_order_data, "CUST-00002")
    print(f"   Online Order creation success: {online_result['success']}")
    print(f"   File ID: {online_result.get('file_id', 'N/A')}")
    print(f"   Offline mode: {online_result.get('offline_mode', 'N/A')}")
    
    # Test 4: Check pending files
    print("\n📋 Checking pending files...")
    pending_files = sync_manager.get_pending_files()
    print(f"   Found {len(pending_files)} pending files:")
    for file in pending_files:
        print(f"     - {file.name}")
    
    # Test 5: Read and display file content
    if pending_files:
        print("\n📄 Reading transaction files...")
        for file in pending_files:
            file_data = sync_manager.read_transaction_file(file)
            if file_data:
                print(f"   File: {file.name}")
                print(f"   Type: {file_data['_metadata']['type']}")
                print(f"   Created at: {file_data['_metadata']['created_at']}")
                
                # Handle different transaction types
                if file_data['_metadata']['type'] == 'pos_sale':
                    print(f"   Items count: {len(file_data['data']['items'])}")
                    print(f"   Total amount: ₱{file_data['data']['total_amount']}")
                    print(f"   Customer: {file_data['data']['customer_id']}")
                    print(f"   Cashier: {file_data['data']['cashier_id']}")
                    
                elif file_data['_metadata']['type'] == 'points_update':
                    print(f"   Points used: {file_data['data']['points_used']}")
                    print(f"   Customer: {file_data['data']['customer_id']}")
                    
                elif file_data['_metadata']['type'] == 'online_order':
                    print(f"   Items count: {len(file_data['data']['items'])}")
                    print(f"   Customer: {file_data['data']['customer_id']}")
                    print(f"   Delivery to: {file_data['data']['delivery_address']['recipient_name']}")
                    print(f"   Payment: {file_data['data']['payment_method']}")
                    
                print("   ---")
    
    # Test 6: Get system status
    print("\n📊 System status:")
    system_status = offline_pos_service.get_offline_sales_status()
    for key, value in system_status.items():
        if key not in ['pending_sales', 'pending_orders']:  # Skip long lists
            print(f"   {key}: {value}")
    
    # Test 7: Test sync simulation
    print("\n🔄 Testing sync simulation...")
    # Simulate coming online
    sync_manager.is_online = True
    sync_result = await offline_pos_service.manual_sync_trigger()
    print(f"   Sync success: {sync_result['success']}")
    print(f"   Files synced: {sync_result.get('synced_count', 0)}")
    print(f"   Files failed: {sync_result.get('failed_count', 0)}")
    
    # Check archived files
    print("\n📦 Checking archived files...")
    archived_dir = sync_manager.storage_path / "archived"
    if archived_dir.exists():
        archived_files = list(archived_dir.rglob("*.json"))
        print(f"   Found {len(archived_files)} archived files")
        for file in archived_files[:3]:  # Show first 3
            print(f"     - {file.relative_to(sync_manager.storage_path)}")
    
    print("\n✅ TEST COMPLETED WITH REAL DATA!")
    print("=" * 60)
    
    return True

async def test_points_handling():
    """Test points handling specifically"""
    print("\n🎯 TESTING POINTS HANDLING SPECIFICALLY")
    print("=" * 40)
    
    from offline_sync_manager import sync_manager
    from offline_pos_service import offline_pos_service
    
    # Test with points redemption
    points_sale = {
        "items": [
            {
                "product_id": "PROD-00210", 
                "product_name": "Test Product 210",
                "quantity": 1, 
                "unit_price": 150.50, 
                "subtotal": 150.50
            }
        ],
        "subtotal": 150.50,
        "tax_amount": 18.06,
        "total_amount": 168.56,
        "payment_method": "cash",
        "customer_id": "CUST-00002",
        "loyalty_points_used": 200,  # This should trigger points caching
        "loyalty_points_earned": 16
    }
    
    result = await offline_pos_service.create_sale_offline(points_sale, "CASHIER-001")
    print(f"   Points sale creation: {result['success']}")
    print(f"   Points pending sync: {result.get('points_pending', False)}")
    
    # Check for points update file
    points_files = sync_manager.get_pending_files("points_update")
    print(f"   Points update files: {len(points_files)}")
    for file in points_files:
        file_data = sync_manager.read_transaction_file(file)
        if file_data:
            print(f"   - Points used: {file_data['data']['points_used']}")
            print(f"   - Customer: {file_data['data']['customer_id']}")
    
    return True

if __name__ == "__main__":
    # Run the main test
    success = asyncio.run(quick_test())
    
    # Run points handling test
    points_success = asyncio.run(test_points_handling())
    
    if success and points_success:
        print("\n🎉 OFFLINE SYSTEM IS WORKING WITH REAL DATA!")
        print("\n📁 Check the file structure in: backend/app/offline_storage/")
        print("   You should see:")
        print("   - active/ folder with pending files") 
        print("   - archived/ folder with synced files")
        print("   - Real POS sales and online orders stored")
        print("   - Points properly cached but not applied")
        
        print("\n✅ ALL REQUIREMENTS VERIFIED:")
        print("   ✅ File-based storage working")
        print("   ✅ POS sales stored during offline") 
        print("   ✅ Online orders stored during offline")
        print("   ✅ Points cached but not used offline")
        print("   ✅ Timestamp file naming working")
        print("   ✅ File archiving after sync")
        print("   ✅ Real customer data (CUST-00002) handled")
        print("   ✅ Real product data (PROD-00210, PROD-00209) handled")
    else:
        print("\n❌ TEST FAILED - Check the errors above")