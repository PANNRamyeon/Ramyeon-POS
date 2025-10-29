from datetime import datetime
from typing import Tuple

from app.database import db_manager
from pymongo import ReplaceOne
from app.services.POS.pos_sales_service import POSSalesService
from app.services.POS.shift_service import ShiftService


def _build_sale_payload(local_sale: dict) -> Tuple[dict, str]:
    """
    Map a local sale document to the create_sale payload and extract cashier_id.
    The cloud service will assign its own sale_id and handle stock/loyalty logic.
    """
    cashier_id = local_sale.get('cashier_id')

    # loyalty fields may be embedded or top-level
    loyalty = local_sale.get('loyalty_points') or {}
    points_used = loyalty.get('points_used') or local_sale.get('loyalty_points_used', 0) or 0
    points_discount = (
        (local_sale.get('discount_breakdown') or {}).get('points_discount')
        or local_sale.get('points_discount')
        or 0
    )

    payload = {
        'items': local_sale.get('items', []),
        'subtotal': local_sale.get('subtotal', 0),
        'tax_amount': local_sale.get('tax_amount', 0),
        'discount_amount': local_sale.get('discount_amount', 0),
        'total_amount': local_sale.get('total_amount', 0),
        'payment_method': local_sale.get('payment_method'),
        'payment_details': local_sale.get('payment_details', {}),
        'customer_id': local_sale.get('customer_id'),
        'promotion_id': local_sale.get('promotion_id'),
        'promotion_discount': local_sale.get('promotion_discount', 0),
        'loyalty_points_used': points_used,
        'loyalty_points_earned': loyalty.get('points_earned', 0),
        'points_discount': points_discount,
        # Note: shift_id will be remapped to the active cloud shift during push
        'shift_id': None,
    }

    return payload, cashier_id


def push_pending_sales(max_docs: int | None = None) -> dict:
    """
    Push local pending sales to cloud using the same service logic as the API.
    Process in (shift_id, shift_seq, created_at) order. Returns summary counts.
    """
    # Ensure cloud is reachable; db_manager.get_database() will connect to cloud by default
    cdb = db_manager.get_database()

    local_db = db_manager.get_local_database_optional()
    if local_db is None:
        return {'success': 0, 'failed': 0, 'total': 0}

    sales_coll = local_db.sales

    query = {'sync_state': 'pending'}
    sort_spec = [
        ('shift_id', 1),
        ('shift_seq', 1),
        ('created_at', 1),
    ]

    cursor = sales_coll.find(query).sort(sort_spec)
    if max_docs:
        cursor = cursor.limit(int(max_docs))

    svc = POSSalesService()
    shift_svc = ShiftService()
    success = 0
    failed = 0

    for local_sale in cursor:
        try:
            payload, cashier_id = _build_sale_payload(local_sale)
            # Remap local shift to the active cloud shift for this cashier
            cloud_shift_id = None
            if cashier_id:
                active = cdb.shifts.find_one({
                    'cashier_id': cashier_id,
                    'status': {'$in': ['open', 'active']}
                })
                if not active:
                    # Create a new shift in cloud with opening_cash=0
                    created = shift_svc.start_shift(cashier_id, 0.0)
                    cloud_shift_id = created.get('_id')
                else:
                    cloud_shift_id = active.get('_id')
            payload['shift_id'] = cloud_shift_id
            result = svc.create_sale(payload, cashier_id)
            cloud_sale = result.get('data', {}) if isinstance(result, dict) else {}
            cloud_id = cloud_sale.get('_id')

            sales_coll.update_one(
                {'_id': local_sale['_id']},
                {
                    '$set': {
                        'sync_state': 'applied',
                        'updated_at_cloud': datetime.utcnow(),
                        'cloud_sale_id': cloud_id,
                    }
                }
            )
            # After successful push, refresh affected products from cloud into local
            try:
                product_ids = [it.get('product_id') for it in (local_sale.get('items') or []) if it.get('product_id')]
                if product_ids:
                    docs = list(cdb.products.find({'_id': {'$in': product_ids}}))
                    if docs:
                        ops = [ReplaceOne({'_id': d.get('_id')}, d, upsert=True) for d in docs]
                        local_db.products.bulk_write(ops, ordered=False)
            except Exception:
                pass
            success += 1
        except Exception:
            failed += 1

    total = success + failed
    return {'success': success, 'failed': failed, 'total': total}


def warm_catalog_to_local(collections: list[str] | None = None, batch_size: int = 1000) -> dict:
    """
    Copy selected catalog collections from cloud -> local via upsert.
    Default set: products, batches, category, users, customers, promotions.
    """
    default_cols = ['products', 'batches', 'category', 'users', 'customers', 'promotions']
    cols = collections or default_cols

    cdb = db_manager.get_cloud_database_optional()
    ldb = db_manager.get_local_database_optional()
    if cdb is None or ldb is None:
        return {'updated': 0, 'collections': []}

    updated_total = 0
    processed = []

    for name in cols:
        src = cdb[name]
        dst = ldb[name]
        copied = 0
        ops = []
        for doc in src.find({}, batch_size=batch_size):
            ops.append(ReplaceOne({'_id': doc.get('_id')}, doc, upsert=True))
            if len(ops) >= batch_size:
                dst.bulk_write(ops, ordered=False)
                copied += len(ops)
                ops = []
        if ops:
            dst.bulk_write(ops, ordered=False)
            copied += len(ops)
        updated_total += copied
        processed.append({'collection': name, 'upserts': copied})

    return {'updated': updated_total, 'collections': processed}


