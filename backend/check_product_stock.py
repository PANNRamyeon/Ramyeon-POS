#!/usr/bin/env python
"""Script to check product stock and verify batch calculations"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.local')
django.setup()

from app.database import db_manager
from app.services.POS.batch_service import BatchService
from datetime import datetime

def find_product(name_pattern):
    """Find product by name pattern"""
    db = db_manager.get_database()
    products = list(db.products.find({
        'product_name': {'$regex': name_pattern, '$options': 'i'},
        'isDeleted': {'$ne': True}
    }))
    return products

def check_product_stock(product_id):
    """Check product stock and batches"""
    batch_service = BatchService()
    
    # Get product
    product = batch_service.products_collection.find_one({'_id': product_id})
    if not product:
        print(f"Product {product_id} not found")
        return
    
    print(f"\n{'='*60}")
    print(f"Product: {product.get('product_name')} ({product_id})")
    print(f"Current total_stock in DB: {product.get('total_stock', 0)}")
    print(f"{'='*60}\n")
    
    # Get all batches
    all_batches = list(batch_service.batches_collection.find({
        'product_id': product_id
    }))
    
    print(f"Total batches: {len(all_batches)}\n")
    
    # Group by status
    active_batches = []
    expired_batches = []
    depleted_batches = []
    pending_batches = []
    
    for batch in all_batches:
        status = batch.get('status', 'active')
        qty = batch.get('quantity_remaining', 0)
        expiry = batch.get('expiry_date')
        is_expired = batch_service._is_batch_expired(batch)
        
        batch_info = {
            'id': batch['_id'],
            'batch_number': batch.get('batch_number', 'N/A'),
            'quantity_remaining': qty,
            'expiry_date': expiry,
            'status': status,
            'is_expired_check': is_expired
        }
        
        if status == 'expired' or is_expired:
            expired_batches.append(batch_info)
        elif status == 'depleted':
            depleted_batches.append(batch_info)
        elif status == 'pending':
            pending_batches.append(batch_info)
        else:
            active_batches.append(batch_info)
    
    # Show active batches
    print(f"ACTIVE BATCHES ({len(active_batches)}):")
    total_active = 0
    for batch in active_batches:
        expiry_str = str(batch['expiry_date']) if batch['expiry_date'] else 'No expiry'
        expired_marker = " ⚠️ EXPIRED" if batch['is_expired_check'] else ""
        print(f"  • Batch {batch['batch_number']}: {batch['quantity_remaining']} units")
        print(f"    Expiry: {expiry_str}{expired_marker}")
        if not batch['is_expired_check']:
            total_active += batch['quantity_remaining']
    print(f"  Total (non-expired): {total_active}\n")
    
    # Show expired batches
    if expired_batches:
        print(f"EXPIRED BATCHES ({len(expired_batches)}):")
        total_expired = 0
        for batch in expired_batches:
            expiry_str = str(batch['expiry_date']) if batch['expiry_date'] else 'No expiry'
            print(f"  • Batch {batch['batch_number']}: {batch['quantity_remaining']} units")
            print(f"    Expiry: {expiry_str}")
            total_expired += batch['quantity_remaining']
        print(f"  Total (expired): {total_expired}\n")
    
    # Calculate expected stock
    valid_batches = [b for b in active_batches if not b['is_expired_check']]
    expected_stock = sum(b['quantity_remaining'] for b in valid_batches)
    
    print(f"{'='*60}")
    print(f"EXPECTED STOCK (valid batches only): {expected_stock}")
    print(f"CURRENT STOCK IN DB: {product.get('total_stock', 0)}")
    print(f"DIFFERENCE: {expected_stock - product.get('total_stock', 0)}")
    print(f"{'='*60}\n")
    
    # Verify using batch service
    batch_info = batch_service.check_batch_availability(product_id, 0)
    print(f"BatchService.check_batch_availability() result:")
    print(f"  total_stock: {batch_info['total_stock']}")
    print(f"  batches_count: {batch_info['batches_count']}")
    print()

if __name__ == '__main__':
    # Search for "7 up in can"
    print("Searching for '7 up in can'...")
    products = find_product('7.*up.*can')
    
    if not products:
        print("Product not found. Searching for similar products...")
        products = find_product('7.*up')
    
    if products:
        for product in products:
            check_product_stock(product['_id'])
    else:
        print("No products found matching '7 up in can'")
        print("\nSearching all products with '7' and 'up'...")
        products = find_product('7')
        print(f"Found {len(products)} products with '7' in name")
        for p in products[:10]:  # Show first 10
            print(f"  - {p.get('product_name')} ({p['_id']})")



