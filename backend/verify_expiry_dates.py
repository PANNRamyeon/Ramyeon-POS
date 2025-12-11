#!/usr/bin/env python
"""Verify expiry date detection for 7 up in can"""
import os
import sys
import django
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.local')
django.setup()

from app.database import db_manager
from app.services.POS.batch_service import BatchService

product_id = "PROD-00225"  # 7 up in can
batch_service = BatchService()

# Get all batches
batches = list(batch_service.batches_collection.find({
    'product_id': product_id
}))

print(f"\n{'='*60}")
print(f"Detailed Batch Analysis for '7 up in can' (PROD-00225)")
print(f"{'='*60}\n")

now = datetime.utcnow()
print(f"Current date (UTC): {now.date()}\n")

total_valid = 0
total_expired = 0

for batch in batches:
    batch_id = batch['_id']
    batch_num = batch.get('batch_number', 'N/A')
    qty = batch.get('quantity_remaining', 0)
    status = batch.get('status', 'active')
    expiry_date = batch.get('expiry_date')
    
    # Check expiry using the service method
    is_expired = batch_service._is_batch_expired(batch)
    
    print(f"Batch: {batch_num} ({batch_id})")
    print(f"  Status: {status}")
    print(f"  Quantity Remaining: {qty}")
    print(f"  Expiry Date: {expiry_date}")
    
    if expiry_date:
        if isinstance(expiry_date, str):
            try:
                expiry_date = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
            except:
                pass
        
        if hasattr(expiry_date, 'date'):
            expiry_date_only = expiry_date.date()
        else:
            expiry_date_only = expiry_date
        
        if isinstance(expiry_date_only, datetime):
            expiry_date_only = expiry_date_only.date()
        
        print(f"  Expiry Date (parsed): {expiry_date_only}")
        print(f"  Current Date: {now.date()}")
        print(f"  Is Expired (date check): {expiry_date_only < now.date()}")
    
    print(f"  Is Expired (service check): {is_expired}")
    
    if is_expired or status == 'expired':
        print(f"  ⚠️  EXCLUDED FROM STOCK")
        total_expired += qty
    else:
        print(f"  ✓ INCLUDED IN STOCK")
        total_valid += qty
    
    print()

print(f"{'='*60}")
print(f"SUMMARY:")
print(f"  Valid stock (should be counted): {total_valid}")
print(f"  Expired stock (excluded): {total_expired}")
print(f"  Total batches: {len(batches)}")
print(f"{'='*60}\n")

# Check what the product shows
product = batch_service.products_collection.find_one({'_id': product_id})
print(f"Product total_stock in DB: {product.get('total_stock', 0) if product else 'N/A'}")
print(f"Expected stock (valid batches): {total_valid}")
print(f"Difference: {total_valid - (product.get('total_stock', 0) if product else 0)}")



