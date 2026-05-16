# CLAUDE.md — PANN POS System

**Last Updated:** 2026-05-14
**Repository:** PANN_POS_SYSTEM

---

## 0. Terminology

| Term | Meaning |
|---|---|
| **v4** | Legacy code — the current MongoDB-based system (pre-migration) |
| **v5** | Target version — DynamoDB-based system, aligned with PANN_BACK_OFFICE conventions |

When the user says "refactor to v5", it means:
- Replace PyMongo with PynamoDB (DynamoDB ORM)
- Replace Options API components with `<script setup>` Composition API
- Replace service-layer API files (`services/api*.js`) with composables (`composables/api/use*.js`)
- Align with the single-table DynamoDB design used in PANN_BACK_OFFICE
- Use Lucide icons, `useModal` composable, Teleport for modals
- Use theme CSS variables (`var(--color-*)`) instead of hardcoded colors

---

## 1. Project Overview

**PANN POS System** is the customer-facing Point-of-Sale terminal for Ramyeon Corner. It is the counterpart to PANN_BACK_OFFICE — where the back office manages inventory and administration, this system handles:

- **Sales Transactions**: Order creation, cart management, and checkout
- **Shift Management**: Cashier clock-in/out, shift summaries, and handover
- **Payment Processing**: Maya Business API direct integration (Maya, cash); GCash pending
- **Online Orders**: Receiving and fulfilling online orders
- **Customer Loyalty**: Loyalty point lookup and redemption at checkout
- **Promotions**: Applying active discounts and BOGO deals at POS
- **Dashboard**: Real-time KPI cards (sales today, active shifts, low stock alerts)
- **Offline Mode**: Request queueing for network interruptions, syncs on reconnect

**Current State (v4):**
- Fully functional MongoDB-based backend
- Frontend uses a mix of Options API and Composition API
- Service-layer files (`services/api*.js`) handle all API calls
- Windows .exe installer exists for on-premises deployment
- Maya Business API in sandbox mode — switch `VITE_MAYA_MODE=live` for production

**Migration Target (v5):**
- Backend: Replace PyMongo with PynamoDB, align models with PANN_BACK_OFFICE single-table design
- Frontend: All components to `<script setup>`, service files replaced by composables
- Share the same DynamoDB table (`RamyeonCornerDB`) as the back office

---

## 2. Tech Stack

### **Backend**
- **Framework**: Django 5.2.1 + Django REST Framework 3.16.0
- **Language**: Python 3.9+
- **Database (v4)**: MongoDB Atlas via PyMongo 4.13.0 + Motor 3.7.1 (async)
  - Cloud: MongoDB Atlas (`pos_system` database)
  - Local fallback: `localhost:27017` (`pos_system_local`)
- **Database (v5 target)**: AWS DynamoDB via PynamoDB 6.0.0+
  - Same table as back office: `RamyeonCornerDB`
  - Region: ap-southeast-1 (Singapore)
- **Authentication**: JWT via python-jose 3.5.0
- **Password Hashing**: bcrypt 4.3.0, passlib 1.7.4
- **Email**: SendGrid 6.11.0
- **Payment**: Maya Business API (direct HTTP, no pip package)
- **Production Server**: Gunicorn 21.2.0 + WhiteNoise 6.6.0
- **Packaging**: PyInstaller 6.16.0 (Windows .exe installer)

### **Frontend**
- **Framework**: Vue 3.5.13
- **Build Tool**: Vite 6.2.4
- **Router**: Vue Router 4.5.0
- **State Management**: Pinia 3.0.1
- **HTTP Client**: Axios 1.9.0
- **UI Framework**: Bootstrap 5.3.7
- **Charts**: Chart.js 4.5.0 + vue-chartjs
- **Date Picker**: @vuepic/vue-datepicker 11.0.2
- **Icons**: Lucide Vue Next 0.519.0
- **Testing**: Vitest 3.1.1 + @vue/test-utils

### **Infrastructure**
- **Cloud DB**: MongoDB Atlas (v4) → AWS DynamoDB (v5)
- **Frontend Hosting**: Netlify
- **Backend Hosting**: Render (cloud) or Windows .exe (on-premises)
- **Payments**: Maya Business API (direct) — sandbox: `pg-sandbox.maya.ph`, live: `pg.maya.ph`
- **Email**: SendGrid

---

## 3. Architecture

### **Overall Pattern**

```
PANN_POS_SYSTEM/
├── backend/                  # Django REST API
│   ├── posbackend/           # Django project settings
│   ├── app/                  # Main Django application
│   │   ├── kpi_views/        # API views, organized by domain
│   │   │   ├── Backoffice/   # Admin-facing POS views
│   │   │   └── POS/          # Cashier-facing POS views
│   │   ├── services/         # Business logic layer
│   │   ├── models.py         # Data classes (plain Python, not Django ORM)
│   │   ├── database.py       # MongoDB connection manager (v4)
│   │   ├── middleware.py     # JWT auth, logging, error handling
│   │   └── offline/          # Offline queue handling
│   ├── notifications/        # Shift summaries, email alerts
│   └── kpi/                  # Analytics module
└── frontend/                 # Vue 3 SPA
    └── src/
        ├── pages/            # Route views
        ├── components/       # Reusable UI components
        ├── composables/      # Vue composables (target for v5 API calls)
        ├── services/         # Axios API wrappers (v4, to be replaced)
        ├── stores/           # Pinia stores
        └── router/           # Vue Router
```

### **Backend Architecture (v4 — current)**

1. **API Layer** (`app/kpi_views/`)
   - `Backoffice/` — admin-side views (products, users, categories, etc.)
   - `POS/` — cashier-side views (sales, cart, shifts, promotions, online orders)
   - Views are Django class-based (APIView from DRF)

2. **Service Layer** (`app/services/`)
   - `mongodb_manager.py` — central DB connection
   - `sync_service.py` — cloud/local sync logic

3. **Model Layer** (`app/models.py`)
   - Plain Python dataclasses with `.to_dict()` methods
   - No Django ORM — PyMongo queries directly in views/services

4. **Database Layer** (`app/database.py`)
   - `DatabaseManager` class with dual connections (cloud Atlas + local)
   - `FORCE_LOCAL_DB` env var to force local MongoDB

### **Backend Architecture (v5 — target)**

Align with PANN_BACK_OFFICE conventions:
1. **API Layer** — keep view structure, update to use DynamoDB service layer
2. **Service Layer** — replace PyMongo queries with PynamoDB model methods
3. **Model Layer** — PynamoDB models with `PK`/`SK` keys, GSIs, `version` field for optimistic locking
4. **No DatabaseManager** — PynamoDB handles connection via env vars

### **Frontend Architecture (v4 — current)**

- **Services**: `src/services/api*.js` — axios wrappers per domain, called directly from components
- **Components**: Mix of Options API (`data()`, `methods()`, `mounted()`) and Composition API
- **Stores**: Pinia with Composition API (`cartStores.js` is the main one)
- **Offline**: `offlineManager.js` + `App.vue` online/offline event listeners

### **Frontend Architecture (v5 — target)**

- **Composables**: Replace all `services/api*.js` with `composables/api/use*.js` (pattern from back office)
- **Components**: All converted to `<script setup>` Composition API
- **No direct service imports in components** — always use composables
- **Modals**: Use `useModal` composable + Teleport

---

## 4. Folder Structure

```
PANN_POS_SYSTEM/
├── backend/
│   ├── posbackend/               # Django project config
│   │   ├── settings.py
│   │   ├── urls.py               # Root URL routing
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── app/                      # Core POS application
│   │   ├── kpi_views/            # API views
│   │   │   ├── Backoffice/       # Admin-side
│   │   │   │   ├── authentication_views.py
│   │   │   │   ├── user_views.py
│   │   │   │   ├── customer_views.py
│   │   │   │   ├── product_views.py
│   │   │   │   ├── category_views.py
│   │   │   │   ├── category_pos_views.py
│   │   │   │   ├── category_display_views.py
│   │   │   │   ├── supplier_views.py
│   │   │   │   ├── promotion_views.py
│   │   │   │   ├── session_views.py
│   │   │   │   └── sales_log_views.py
│   │   │   └── POS/              # Cashier-side
│   │   │       ├── pos_sales_views.py
│   │   │       ├── cart_views.py
│   │   │       ├── shift_views.py
│   │   │       ├── promotion_pos_views.py
│   │   │       ├── online_transaction_views.py
│   │   │       └── pos_reports_views.py
│   │   ├── services/             # Business logic
│   │   │   ├── mongodb_manager.py    # v4 — replace with PynamoDB services
│   │   │   └── sync_service.py       # v4 — cloud/local sync (may not apply in v5)
│   │   ├── models.py             # v4 plain Python data classes
│   │   ├── database.py           # v4 MongoDB dual-connection manager
│   │   ├── middleware.py         # JWT auth, logging, error handling
│   │   ├── serializers.py        # DRF serializers
│   │   ├── decorators/           # Auth decorators
│   │   ├── offline/              # Offline queue handling
│   │   └── utils/
│   │       └── date_time_helper.py
│   ├── notifications/            # Notification module
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── services.py
│   │   ├── shift_summary_service.py
│   │   └── email_service.py      # SendGrid integration
│   ├── kpi/                      # KPI/analytics module
│   ├── api/                      # Minimal secondary API app
│   ├── manage.py
│   ├── requirements.txt
│   └── .env                      # Not committed
│
├── frontend/
│   └── src/
│       ├── pages/                # Route views (one file per page)
│       │   ├── Login.vue
│       │   ├── Home.vue              # Dashboard (KPI cards, charts)
│       │   ├── NewOrder.vue          # POS order creation (main cashier view)
│       │   ├── Checkout.vue          # Payment & checkout
│       │   ├── History.vue           # Order/sales history
│       │   ├── OnlineOrders.vue      # Online order management
│       │   ├── Shift.vue             # Shift clock-in/out
│       │   ├── ShiftSummary.vue      # Shift closing summary
│       │   ├── Settings.vue
│       │   └── notifications/
│       ├── components/           # Reusable UI components
│       │   ├── common/           # TableTemplate, CardTemplate, PaginationControls, etc.
│       │   ├── icons/
│       │   └── *.vue             # BarChart, CheckoutCard, KPICard, PaymentProcessingModal,
│       │                         # SyncStatusIndicator, NotificationBell, etc.
│       ├── composables/          # Vue composables (expand for v5)
│       │   ├── api/              # API composables (target for v5 migration)
│       │   │   ├── useProducts.js
│       │   │   ├── useCustomers.js
│       │   │   ├── useReports.js
│       │   │   └── usePaymaya.js     # Maya Business Checkout API (replaces usePaymongo)
│       │   ├── business/
│       │   │   └── useInventory.js   # Currently empty — needs implementation
│       │   ├── data/
│       │   │   ├── useCache.js
│       │   │   ├── useLocalStorage.js
│       │   │   ├── useStockCache.js
│       │   │   └── usePagination.js
│       │   ├── forms/
│       │   │   ├── useCustomerForm.js
│       │   │   ├── useProductForm.js
│       │   │   └── useFormValidation.js  # Currently empty
│       │   └── ui/
│       │       ├── useModal.js
│       │       ├── useTheme.js
│       │       └── useBarcode.js
│       ├── services/             # v4 axios wrappers — replace with composables in v5
│       │   ├── api.js            # Base axios instance (JWT interceptors, offline queueing)
│       │   ├── apiCart.js
│       │   ├── apiCategory.js
│       │   ├── apiDashboard.js
│       │   ├── apiHistory.js
│       │   ├── apiOnlineOrder.js
│       │   ├── apiOrder.js
│       │   ├── apiPayment.js
│       │   ├── apiProducts.js
│       │   ├── apiSales.js
│       │   ├── apiSettings.js
│       │   ├── apiSync.js
│       │   └── offlineManager.js
│       ├── stores/
│       │   ├── cartStores.js     # Cart state (Pinia, Composition API)
│       │   └── counter.js
│       ├── router/
│       │   └── index.js          # Routes + auth guards
│       ├── assets/
│       │   └── styles/           # global.css, colors.css, buttons.css, badge.css, theme_utilities.css
│       ├── layouts/
│       │   └── MainLayout.vue
│       └── main.js
│
├── mongoDB/                      # v4 legacy MongoDB scripts
├── staticfiles/                  # Collected Django static files
├── installer_output/             # Windows .exe build artifacts
└── db.sqlite3                    # Unused (DynamoDB in v5)
```

---

## 5. Coding Conventions

### **Backend (Python/Django)**

**Naming:**
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Model IDs**: Same as back office — `PREFIX-#####` (e.g., `SALE-000001`, `SHIFT-00001`)

**v5 Patterns (align with PANN_BACK_OFFICE):**
- **PynamoDB Models**: `PK` + `SK` in single table `RamyeonCornerDB`
- **Service Layer**: Domain services in `app/services/` (e.g., `SalesService`, `ShiftService`)
- **Optimistic Locking**: `version` field on models that need concurrent write protection
- **Soft Deletes**: `isDeleted` boolean, never hard-delete sales or shift records
- **Atomic Counters**: Use `counter_service.get_next_id()` for all ID generation
- **Pagination**: All list endpoints return `(items, next_page_token)` tuples
- **Logging**: `logger = logging.getLogger(__name__)` — no bare `print()`

**v4 Patterns to eliminate:**
- `DatabaseManager` / `mongodb_manager.py` — remove entirely
- Direct PyMongo queries in views — move to service layer using PynamoDB
- Plain Python data classes in `models.py` — replace with PynamoDB model classes

### **Frontend (Vue 3 / JavaScript)**

**Naming:**
- **Components**: `PascalCase.vue`
- **Composables**: `use` prefix + PascalCase (e.g., `useSales.js`, `useShifts.js`)
- **Service files** (`services/api*.js`): v4 pattern — do not add new ones in v5
- **Functions**: `camelCase`
- **Constants**: `UPPER_SNAKE_CASE`

**v5 Component Structure:**
```vue
<template>
  <!-- HTML markup -->
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSales } from '@/composables/api/useSales'

const { sales, fetchSales } = useSales()
const isLoading = ref(false)

const handleAction = () => { /* ... */ }

onMounted(() => fetchSales())
</script>

<style scoped>
/* Component-specific styles using CSS variables */
</style>
```

**v4 Patterns to eliminate:**
- Options API (`data()`, `methods()`, `computed: {}`, `mounted()`) — convert to `<script setup>`
- Direct service imports in components (`import { apiSales } from '@/services/apiSales'`) — use composables instead
- Hardcoded colors — use `var(--color-*)` CSS variables

**API Composable Pattern (v5):**
```js
// composables/api/useSales.js
import { ref } from 'vue'
import axios from 'axios'

export function useSales() {
  const sales = ref([])
  const loading = ref(false)
  const error = ref(null)

  const fetchSales = async (params = {}) => {
    loading.value = true
    try {
      const res = await axios.get('/api/v1/pos/sales/', { params })
      sales.value = res.data
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
  }

  return { sales, loading, error, fetchSales }
}
```

**State Management:**
- `cartStores.js` — keep Pinia for cart (global state that spans components)
- Prefer composables for everything else (avoid Pinia for per-page state)

---

## 6. Key Domain Rules

### **Sales**
- **ID Format**: `SALE-######` (6-digit, zero-padded)
- A sale belongs to an active shift — cannot create a sale with no open shift
- Batch deduction is FIFO/FEFO — use `BatchManager.get_batch_for_fulfillment()`
- All line items must reference a valid `product_id` and deduct from the correct batch
- Sales are immutable after completion — no editing, only refunds/voids as separate records
- `total_amount` = sum of line items after promotion application

### **Cart**
- Cart is ephemeral — not persisted to DB, lives in `cartStores.js` (Pinia)
- On checkout completion, cart is cleared and a `Sale` record is created
- Promotions are evaluated at checkout time, not when items are added

### **Shifts**
- **ID Format**: `SHIFT-#####` (5-digit)
- Only one shift can be active per cashier at a time
- Shift stores: `cashier_id`, `start_time`, `opening_cash`, `end_time`, `closing_cash`, `total_sales`, `status`
- **Status**: `"open"` → `"closed"`
- Cannot create a sale if no shift is open for that cashier
- `ShiftSummary` page generates per-shift reports (total sales, cash vs non-cash, voids)

### **Online Orders**
- Received from external channel (website/app), displayed in `OnlineOrders.vue`
- Must be explicitly accepted or rejected by cashier
- On acceptance, converted to a sale record (same batch deduction flow)
- **Status**: `"pending"` → `"accepted"` / `"rejected"` → `"fulfilled"`

### **Payments**
- Supported methods: cash, Maya (direct via Maya Business API)
- GCash is currently unavailable — was previously routed through PayMongo which is no longer used
- Cash payments: change calculation handled on frontend, no external API call
- Maya is in sandbox mode (`VITE_MAYA_MODE=sandbox`) — set to `live` for production
- Maya keys stored in frontend `.env` — never hardcode
- **Payment flow (Maya)**: `Checkout.vue` → `usePaymaya.createCheckout()` → redirect to `checkout.redirectUrl` → customer pays on Maya → redirect back to `/pos/payment-callback?status=success` → `PaymentCallback.vue` creates sale record
- **Idempotency**: `PaymentCallback.vue` uses `checkout_id` from `sessionStorage.pendingEWalletPayment` as the idempotency key to prevent duplicate sale creation on page refresh
- **Maya API reference**: Sandbox `https://pg-sandbox.maya.ph` · Live `https://pg.maya.ph` · Auth: Basic auth with secret key (`btoa(secretKey + ':')`)

### **Promotions**
- Promotions are fetched from back office (shared data source in v5)
- Applied at checkout — not when items are added to cart
- Types: percentage discount, fixed amount off, BOGO
- Only `"active"` promotions apply

### **Customers**
- Looked up by loyalty card or phone number at checkout
- Points accrued per sale, redeemable for discounts
- Customer auth is separate from staff auth (different JWT claims)

### **Products / Inventory**
- POS system reads product data — does not own it (back office owns it)
- In v5, both systems share the same `RamyeonCornerDB` table
- POS reads stock levels but batch deductions are the source of truth
- Barcode scanning maps to `barcode` field on Product

### **Offline Mode**
- Current v4 implementation queues requests in `offlineManager.js`
- Sync happens on reconnect via `sync_service.py`
- In v5: evaluate whether offline queueing is still needed or if connectivity can be assumed

### **ID Generation**
- All IDs generated via `counter_service.get_next_id()` (same as back office)
- Never reuse IDs
- Format: `{PREFIX}-{NUMBER}` with zero-padding

---

## 7. What To Never Do

### **Backend**

1. **NEVER deduct batch stock directly from a Sale view**
   - Always go through the batch service / `BatchManager`
   - Stock deduction must use optimistic locking to avoid race conditions

2. **NEVER create a sale record without a valid open shift**
   - Validate `shift_id` exists and `status === "open"` before committing a sale

3. **NEVER expose Maya secret keys in responses or logs**
   - `VITE_MAYA_SECRET_KEY` is used only inside `usePaymaya.js` for API auth headers — never log or return it

4. **NEVER hard-delete sale or shift records**
   - Use soft deletes (`isDeleted` flag) — sales are financial records

5. **NEVER skip JWT verification on POS endpoints**
   - All `/api/v1/pos/` endpoints require a valid cashier token

6. **NEVER query DynamoDB without pagination**
   - POS sales lists can grow very large — always paginate

7. **NEVER mix v4 PyMongo calls with v5 PynamoDB calls**
   - During migration, a service is either fully v4 or fully v5 — no hybrids

### **Frontend**

1. **NEVER import from `services/api*.js` in new v5 components**
   - Use composables from `composables/api/` only
   - The `services/` directory is v4 — it will be deleted after full migration

2. **NEVER add items to cart without checking product stock**
   - Prevent overselling at the UI level before the backend rejects it

3. **NEVER store Maya keys in frontend code or localStorage**
   - Keys live in `.env` only: `VITE_MAYA_PUBLIC_KEY`, `VITE_MAYA_SECRET_KEY`
   - `usePaymaya.js` exposes a redacted config object (`secretKey: '***'`) — never the raw key

4. **NEVER mutate cart state directly outside `cartStores.js`**
   - All cart mutations go through Pinia actions

5. **NEVER hardcode API URLs**
   - Use `import.meta.env.VITE_API_URL`

6. **NEVER complete a sale without confirming payment success**
   - Maya redirects to `/pos/payment-callback?status=success` only after the customer completes payment — the sale record is created there, not before the redirect

---

## 8. How To Run

### **Backend**

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

**`.env` file (backend/):**
```env
# v4 (current)
MONGODB_URI=mongodb+srv://...
MONGODB_DATABASE=pos_system
MONGODB_LOCAL_URI=mongodb://localhost:27017
MONGODB_LOCAL_DATABASE=pos_system_local
FORCE_LOCAL_DB=False

# v5 (target — add these during migration)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION_NAME=ap-southeast-1
DYNAMO_TABLE_NAME=RamyeonCornerDB

# Shared
DEBUG=True
SECRET_KEY=your-secret-key
SENDGRID_API_KEY=SG....
```

### **Frontend**

```bash
cd frontend
npm install
npm run dev
```

**`.env` file (frontend/):**
```env
VITE_API_URL=http://localhost:8000/api/v1

# Maya Business API — get keys from Maya Business Dashboard > Developer > API Keys
VITE_MAYA_PUBLIC_KEY=pk-sandbox-...
VITE_MAYA_SECRET_KEY=sk-sandbox-...
VITE_MAYA_MODE=sandbox   # change to 'live' for production
```

### **Common Commands**

```bash
# Frontend
npm run dev          # Dev server (localhost:5173)
npm run build        # Production build
npm run test:unit    # Run Vitest tests
npm run lint         # ESLint

# Backend
python manage.py runserver
python manage.py createsuperuser
```

---

## 9. V4 → V5 Migration Scope

### **Backend — What Changes**

| Area | v4 (current) | v5 (target) |
|---|---|---|
| Database | PyMongo → MongoDB Atlas | PynamoDB → DynamoDB `RamyeonCornerDB` |
| Models | Plain Python classes in `models.py` | PynamoDB model classes in `models/` |
| DB Connection | `DatabaseManager` (dual MongoDB) | PynamoDB env-based config |
| Service Layer | `mongodb_manager.py` queries | Domain service classes (e.g., `SalesService`) |
| ID Generation | Manual/MongoDB ObjectId | `counter_service.get_next_id()` |
| Offline Sync | `sync_service.py` (cloud↔local MongoDB) | Re-evaluate — may simplify with DynamoDB |

### **Frontend — What Changes**

| Area | v4 (current) | v5 (target) |
|---|---|---|
| API calls | `services/api*.js` imported in components | `composables/api/use*.js` |
| Component API | Options API (`data()`, `methods()`) | `<script setup>` Composition API |
| Modals | Various patterns | `useModal` composable + Teleport |
| Icons | Various | Lucide Vue Next exclusively |

### **What Stays the Same**
- Vue Router structure and auth guards
- Pinia `cartStores.js` (already Composition API)
- CSS theme system (`colors.css`, CSS variables)
- Maya payment integration logic (`usePaymaya.js`)
- Bootstrap 5 layout
- Existing page structure (`pages/`)

### **Migration Priority Order (recommended)**
1. `pos_sales_views.py` + `SalesService` — core domain, needed first
2. `shift_views.py` + `ShiftService` — required before sales can be recorded
3. `cart_views.py` — ties into sales flow
4. `online_transaction_views.py` — lower priority, separate flow
5. `pos_reports_views.py` — last, depends on sales data existing

---

## 10. Current Gaps / TODOs

1. **`composables/business/useInventory.js`** — file exists but is empty
2. **`composables/forms/useFormValidation.js`** — file exists but is empty
3. **Maya live keys** — system is in sandbox mode; set `VITE_MAYA_MODE=live` and replace keys for production
4. **GCash payment** — removed when PayMongo was dropped; needs a direct GCash API solution (Maya Pay does not process GCash)
5. **Offline mode in v5** — `offlineManager.js` is MongoDB-era; decide if DynamoDB changes the offline strategy
6. **Shift auto-close** — no automated shift closure on inactivity
7. **Refund/void flow** — no dedicated refund endpoint or UI found
8. **Barcode scanner** — `useBarcode.js` exists but integration completeness unknown
9. **`settings/` directory** — mentioned in docs but may not be fully implemented

---

## Summary

PANN POS System is the **cashier-facing terminal** for Ramyeon Corner. It is tightly coupled to PANN_BACK_OFFICE — both share the same products, batches, customers, and promotions data. In v5, they share the same DynamoDB table.

The current v4 codebase is functional and feature-complete. Migration to v5 is primarily a **database swap** (MongoDB → DynamoDB) on the backend and a **component API swap** (Options API → `<script setup>`) on the frontend. Business logic and domain rules remain the same.

**Primary reference for shared conventions** (DynamoDB models, ID formats, batch rules, counter system): see `PANN_BACK_OFFICE/CLAUDE.md`.

---

**End of CLAUDE.md**
