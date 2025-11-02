# 🔌 Offline Mode Testing Guide

## Current Implementation Status

### ✅ Implemented Features

1. **Dual-Mode Database**
   - Local MongoDB (required)
   - Cloud MongoDB Atlas (optional, if online)
   - Automatic failover when offline
   - Periodic connectivity checks every 10 seconds

2. **Immediate Synchronization**
   - All sales transactions sync to cloud immediately when online
   - Product stock updates sync to cloud immediately when online
   - Batch `total_stock` updates sync to cloud immediately when online
   - Failed syncs are queued for later

3. **Background Sync Worker**
   - **NOW AUTO-STARTED** on app launch
   - Runs every 30 seconds when online
   - Processes queued items
   - Pulls product updates from cloud
   - Bidirectional sync for customers, categories, promotions

4. **Offline Request Queuing**
   - Frontend queues requests when offline
   - Automatic sync when connection restored
   - Retry mechanism for failed requests

5. **Stock Management**
   - Uses `total_stock` exclusively (derived from batch `quantity_remaining`)
   - Real-time updates during sales
   - Automatic synchronization

---

## 🧪 Testing Scenarios

### **Test 1: Online Mode - Normal Operation**
✅ **Expected**: Everything works normally with cloud sync

1. Ensure both local and cloud MongoDB are running and connected
2. Create a sale
3. Update product stock
4. **Verify**: Check cloud database has the same data as local

**How to verify**:
```bash
# Check local DB
python backend/manage.py dbshell_local  # If you have this command

# Check cloud DB
python backend/manage.py dbshell  # Standard MongoDB shell
```

**Backend Logs to Watch**:
- `✅ Synced sale to cloud immediately: SALE-xxxxxx`
- `✅ Synced stock update to cloud for PROD-xxxxx`
- `✅ Synced product total_stock to cloud: XX`

---

### **Test 2: Offline Mode - Sales Queue**
📴 **Expected**: Sales are queued and synced when online

1. Disconnect internet OR stop cloud MongoDB
2. Create a sale in the system
3. **Verify**: Sale is saved to localDB only
4. Reconnect internet / Start cloud MongoDB
5. Wait 30 seconds (for background worker)
6. **Verify**: Queued sale is synced to cloud

**Backend Logs to Watch**:
- During offline: `📴 Offline: Queuing sales transaction`
- When syncing: `✅ Synced queued sales: SALE-xxxxxx`

**How to verify in database**:
```javascript
// Check localDB sync_queue collection
db.sync_queue.find({collection: 'sales', status: 'pending'})
```

---

### **Test 3: Offline Mode - Stock Updates**
📴 **Expected**: Stock updates are queued and synced when online

1. Disconnect internet
2. Make a sale (which updates product stock)
3. **Verify**: Stock is updated in localDB only
4. Reconnect internet
5. Wait 30 seconds
6. **Verify**: Stock changes are synced to cloud

**Backend Logs to Watch**:
- `📴 Offline: Queuing products transaction`
- `✅ Processed queued items`

---

### **Test 4: Background Sync Worker**
🔄 **Expected**: Worker processes queue every 30 seconds

**Auto-Started Worker**:
1. Start Django server: `python backend/manage.py runserver`
2. Look for logs: `🔄 Background sync worker thread started`
3. Monitor logs every 30 seconds for sync activity

**Manual Worker** (for detailed monitoring):
```bash
# In a separate terminal
python backend/manage.py run_sync_worker
```

**Logs to Watch**:
- `🔄 Starting background sync...`
- `✅ Processing outgoing sync queue...`
- `⬇️ Pulling product updates from cloud...`

---

### **Test 5: Online → Offline Transition**
🌐→📴 **Expected**: System continues working with localDB

1. Start with internet connected
2. Make a few sales (verify they sync to cloud)
3. Disconnect internet
4. Make more sales
5. **Verify**: Sales continue working, saved to localDB
6. Check dashboard shows "Offline" status
7. Reconnect internet
8. Wait for background worker cycle
9. **Verify**: All queued sales sync to cloud

**Frontend Indicators**:
- Look for sync status indicator in sidebar
- Should show "Offline" when disconnected
- Should show "Online" when connected

---

### **Test 6: Historical Data Backfill**
📦 **Expected**: Past unsynced data is pushed to cloud

1. Ensure you have local data that never synced to cloud
2. Run backfill command:
```bash
python backend/manage.py backfill_sales
```

**Expected Output**:
```
Found XX documents in local sales
Backfill for sales completed. Synced: XX, Failed: 0, Skipped: 0
```

**Verify**:
- Check cloud database has same document count as local

---

### **Test 7: Stock Accuracy Verification**
📊 **Expected**: `total_stock` always matches sum of batch quantities

1. Create a product with batches
2. Make a sale
3. Check product `total_stock` field
4. Sum all batch `quantity_remaining` values
5. **Verify**: They match

**Database Query**:
```javascript
// Find a product
var prod = db.products.findOne({product_name: "Some Product"})

// Sum batches
var batches = db.batches.find({product_id: prod._id})
var sum = 0
batches.forEach(b => sum += b.quantity_remaining)

// Compare
print("Product total_stock:", prod.total_stock)
print("Sum of batches:", sum)
```

---

## 🔍 Debugging Commands

### Check Database Connection Status
```python
python backend/manage.py shell

>>> from app.database import db_manager
>>> db_manager.get_connection_status()
```

### Check Sync Queue
```python
python backend/manage.py shell

>>> from app.database import db_manager
>>> db = db_manager.get_local_database()
>>> list(db.sync_queue.find({'status': 'pending'}))
```

### Check Sync Logs for a Product
```python
python backend/manage.py shell

>>> from app.services.Backoffice.product_service import ProductService
>>> ps = ProductService()
>>> product = ps.get_product_by_id('PROD-xxxxx')
>>> product.get('sync_logs', [])
```

### Manual Sync Trigger
```python
python backend/manage.py shell

>>> from app.services.sync_service import sync_service
>>> sync_service.sync_background()
```

---

## 🐛 Common Issues & Solutions

### Issue: Background worker not running
**Solution**: The worker now starts automatically with Django. Check logs for:
- `🔄 Background sync worker thread started`

### Issue: Sales not syncing to cloud
**Check**:
1. Is `is_online` true? `db_manager.is_online`
2. Are there any error logs?
3. Check `sync_queue` for pending items

### Issue: Stock discrepancy between local and cloud
**Solution**: Run manual sync:
```bash
python backend/manage.py sync_product_stock
```

### Issue: Frontend shows "Offline" but backend is online
**Solution**: Check browser console for network errors. The frontend uses `navigator.onLine` which may not always be accurate.

---

## 📝 Next Steps

### Recommendations for Production:

1. **Monitoring**
   - Add dashboard to show sync queue size
   - Alert when queue grows too large
   - Monitor sync success/failure rates

2. **Optimization**
   - Adjust sync interval based on traffic
   - Implement batch syncing for large queues
   - Add exponential backoff for failed syncs

3. **Testing**
   - Add automated tests for offline scenarios
   - Load testing with 1000+ queued transactions
   - Test failure recovery mechanisms

4. **Documentation**
   - Document backup/restore procedures
   - Create disaster recovery plan
   - Document manual sync procedures

---

## ✅ Testing Checklist

- [ ] Online mode sales sync immediately
- [ ] Offline mode sales are queued
- [ ] Queued sales sync when online
- [ ] Stock updates sync in both modes
- [ ] Background worker runs every 30s
- [ ] Online → Offline transition works
- [ ] Offline → Online transition works
- [ ] Historical backfill works
- [ ] `total_stock` matches batch sum
- [ ] Frontend shows correct sync status
- [ ] No data loss during transitions

---

**Last Updated**: 2025-01-XX
**Version**: 1.0

