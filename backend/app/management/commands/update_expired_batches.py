# app/management/commands/update_expired_batches.py
import logging
from django.core.management.base import BaseCommand
from app.services.POS.batch_service import BatchService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Mark expired batches and update product stock'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-id',
            type=str,
            help='Update specific product ID only',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information',
        )

    def handle(self, *args, **options):
        product_id = options.get('product_id')
        verbose = options.get('verbose', False)
        
        batch_service = BatchService()
        
        self.stdout.write(self.style.SUCCESS(
            "\n" + "="*60 + "\n"
            "MARKING EXPIRED BATCHES AND UPDATING PRODUCT STOCK\n"
            "="*60 + "\n"
        ))
        
        # Get products to process
        if product_id:
            product = batch_service.products_collection.find_one({'_id': product_id})
            if not product:
                self.stdout.write(self.style.ERROR(f"Product {product_id} not found"))
                return
            products = [product]
        else:
            products = list(batch_service.products_collection.find({'isDeleted': {'$ne': True}}))
        
        updated_count = 0
        expired_count = 0
        total_products = len(products)
        
        self.stdout.write(f"Processing {total_products} products...\n")
        
        for product in products:
            product_id = product['_id']
            product_name = product.get('product_name', 'Unknown')
            
            # Get active batches
            batches = list(batch_service.batches_collection.find({
                'product_id': product_id,
                'status': 'active',
                'quantity_remaining': {'$gt': 0}
            }))
            
            # Mark expired batches
            product_expired_count = 0
            for batch in batches:
                if batch_service._is_batch_expired(batch):
                    batch_service.batches_collection.update_one(
                        {'_id': batch['_id']},
                        {'$set': {'status': 'expired'}}
                    )
                    product_expired_count += 1
                    expired_count += 1
            
            # Update product stock
            old_stock = product.get('total_stock', 0)
            batch_service.update_product_total_stock(product_id, verbose=verbose)
            
            # Check if stock changed
            updated_product = batch_service.products_collection.find_one({'_id': product_id})
            new_stock = updated_product.get('total_stock', 0)
            
            if old_stock != new_stock or product_expired_count > 0:
                if verbose or old_stock != new_stock:
                    self.stdout.write(
                        f"  {product_name}: Stock {old_stock} → {new_stock}"
                    )
                    if product_expired_count > 0:
                        self.stdout.write(
                            f"    (Marked {product_expired_count} expired batch{'es' if product_expired_count > 1 else ''})"
                        )
                updated_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"\n" + "="*60 + "\n"
            f"✓ Updated {updated_count} products\n"
            f"✓ Marked {expired_count} expired batches\n"
            "="*60 + "\n"
        ))


