# PayMongo Test to Live Mode Switch Guide

## Overview
This guide covers all the changes needed when switching from PayMongo test mode to live mode.

## 1. Frontend .env File (Required)

**Location:** `frontend/.env`

Update the following variables:

```env
# PayMongo API Keys
VITE_PAYMONGO_PUBLIC_KEY=pk_live_tt5RUZLi6HjgdUWqyukWEJOX
VITE_PAYMONGO_SECRET_KEY=sk_live_sh4iaoAgg4HzugztgC6fyxHD
VITE_PAYMONGO_MODE=live
```

**Important:** 
- Replace `pk_test_...` with `pk_live_...` (from your PayMongo dashboard)
- Replace `sk_test_...` with `sk_live_...` (from your PayMongo dashboard)
- Change `VITE_PAYMONGO_MODE` from `test` to `live`

## 2. Rebuild Frontend (Required)

After updating the `.env` file, you **must** rebuild the frontend for changes to take effect:

```bash
cd frontend
npm run build
```

The environment variables are embedded at build time, so the production build needs to be regenerated.

## 3. Rebuild Installer (If Using Standalone Executable)

If you're using the standalone `.exe` installer, rebuild it after updating the frontend:

```bash
# From project root
cd backend
.\venv\Scripts\python.exe -m PyInstaller build_exe.spec --clean --noconfirm

cd ..
backend\venv\Scripts\python.exe create_setup_exe.py
```

## 4. PayMongo Webhook Configuration (If Using Webhooks)

If your application uses PayMongo webhooks for payment notifications:

1. **Go to PayMongo Dashboard** → Developers → Webhooks
2. **Create/Update Webhook for Live Mode:**
   - Endpoint URL: Your production URL (e.g., `https://yourdomain.com/api/webhooks/paymongo`)
   - Events to listen for: `payment.paid`, `payment.failed`, etc.
3. **Note:** Test and Live webhooks are separate - you need to configure both if testing both modes

**Current Status:** The codebase has webhook references but they appear to be placeholder code. If you're not actively using webhooks, you can skip this step.

## 5. Payment Callback URLs (No Changes Needed)

The callback URLs are dynamically generated using `window.location.origin`, so they automatically adapt to your deployment:

```javascript
successUrl: `${window.location.origin}/pos/payment-callback?status=success`
failedUrl: `${window.location.origin}/pos/payment-callback?status=failed`
```

These will work for both test and live modes without any code changes.

## 6. Backend .env (Not Required for PayMongo)

**Note:** PayMongo API keys are **frontend-only** in this implementation. The frontend directly calls PayMongo's API, so there are no PayMongo keys in the backend `.env` file.

## 7. Testing Checklist

After switching to live mode:

- [ ] Updated `frontend/.env` with live keys
- [ ] Changed `VITE_PAYMONGO_MODE=live`
- [ ] Rebuilt frontend (`npm run build`)
- [ ] Rebuilt installer (if applicable)
- [ ] Tested a small transaction first (recommended)
- [ ] Verified payment callbacks work correctly
- [ ] Checked PayMongo dashboard for live transactions

## 8. Important Notes

### Security:
- **Never commit** `.env` files with live keys to version control
- Keep live secret keys secure - they can charge real money
- Use test mode for development/staging environments

### Testing:
- Always test with a small amount first when switching to live
- Verify transactions appear in your PayMongo dashboard
- Monitor for any errors or unexpected behavior

### Rollback:
- If you need to switch back to test mode, simply:
  1. Change `.env` back to test keys
  2. Change `VITE_PAYMONGO_MODE=test`
  3. Rebuild frontend
  4. Rebuild installer (if applicable)

## Summary

**Minimum Required Changes:**
1. ✅ Update `frontend/.env` with live keys
2. ✅ Change `VITE_PAYMONGO_MODE=live`
3. ✅ Rebuild frontend
4. ✅ Rebuild installer (if using standalone)

**Optional Changes:**
- Configure live webhooks (if using webhooks)

**No Changes Needed:**
- Backend `.env` (PayMongo is frontend-only)
- Callback URLs (they're dynamic)
- Code changes (everything is environment-driven)

