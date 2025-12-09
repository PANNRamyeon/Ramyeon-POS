# PANN POS SYSTEM NOTES

## Key Features & Capabilities

**Works Online & Offline:** The system can work with or without internet. When online, it syncs with cloud database. When offline, it saves everything locally and syncs automatically when connection is restored. No data is ever lost.

**Smart Notifications:** System sends alerts for important events - when someone logs in/out, when stock is low, when orders change status, and when bulk operations complete. Admins get email summaries after each shift closes.

**Session Tracking:** Every login is recorded with a unique session ID. The system tracks who logged in, when, and for how long. This helps with security, auditing, and understanding system usage.

**Shift Management:** Cashiers must start a shift with opening cash amount. System tracks all sales and payments in real-time. When closing shift, cashier enters closing cash and system calculates if there's any difference (variance). Summary email sent to all admins.

**Smart Inventory (FIFO):** Products are organized by batches with expiration dates. When selling, system automatically uses oldest products first to reduce waste and ensure proper cost tracking.

**Barcode Scanning:** Products can be scanned using barcode or searched by SKU. System instantly finds product details and current stock levels.

**Bulk Import/Export:** Can import products and sales data from CSV/Excel files. System validates data, shows progress, handles errors, and sends completion notifications. Can also export filtered data.

**System Health Checks:** Built-in health check endpoint shows if system is running properly, if database is connected, and if all services are working.

**Automatic Sync:** System automatically syncs data between local and cloud databases every 30 seconds when online. Keeps everything in sync without manual intervention.

---

## How the System Works

### Backend (Server-Side)

**Database Management:** System connects to two databases - local (always available) and cloud (when internet is available). If cloud connection fails, system automatically uses local database. All settings stored in configuration file, easy to change for different environments.

**Service-Based Architecture:** Business logic is organized into services (like ProductService, OrderService, ShiftService). This makes code reusable - same logic used for POS sales and online orders ensures consistency. Views just validate input and call the right service.

**User Authentication:** When user logs in, system creates two tokens - short-lived access token and longer refresh token. If access token expires, system automatically gets new one using refresh token. When user logs out, tokens are blacklisted so they can't be reused.

**Shift Workflow:** Cashier starts shift by entering opening cash. System generates unique shift ID and tracks all sales. When closing, cashier enters closing cash. System calculates: closing cash minus opening cash minus cash sales = variance. If variance exists, admins are notified via email.

**Online Orders:** Orders go through stages: pending → confirmed → processing → ready → completed. System automatically cancels orders that sit too long without payment (default 30 minutes), restores inventory, and notifies staff. Supports multiple payment methods: cash on delivery, GCash, bank transfer.

**Point of Sale:** Each sale starts with creating a cart. Products added by scanning barcode or manual selection. System automatically deducts from oldest inventory batch. Supports multiple payment methods, all tracked for reporting.

**Logging & Monitoring:** All important actions are logged with details (who, what, when). Health check endpoint shows system status. System actively notifies users about important events.

### Frontend (User Interface)

**API Communication:** Single connection point handles all server communication. Automatically adds authentication tokens to requests. If token expires, automatically refreshes it and retries the request - user doesn't notice any interruption.

**State Management:** Shared data (like product list, customer list) stored in reusable modules. Multiple pages can use same data without duplicating code. Validates data before sending to server, shows helpful error messages.

**Offline Support:** When internet is unavailable, system queues all requests. Visual indicator shows sync status and how many requests are waiting. When connection restored, automatically syncs everything in order with progress updates.

**User Experience:** Toast notifications show success/error messages for all operations. Loading indicators show when system is processing. Theme (dark/light) preference saved and remembered. Browser tab shows current page name.

**Barcode Integration:** When barcode is scanned, system looks up product, shows details, and automatically adds to active cart. Visual feedback confirms successful scan.

---

## Data Organization

**References Between Data:** Products link to categories and suppliers by storing their IDs. Orders link to customers by storing customer ID. This way, if category name changes, we only update it in one place and all products automatically reflect the change.

**Embedded History:** Order documents store their own history (status changes, payment attempts) inside the order. This makes it fast to see "what happened to this order" without searching multiple tables. Sales records store item details at time of sale, so even if product price changes later, we know what was actually sold.

**Categorization:** Products organized by categories and subcategories for easy filtering and reporting. Suppliers linked to branches for location-specific inventory tracking. Promotions linked to specific products for targeted discounts.

**Time-Based Tracking:** Session logs track when users log in and out. Inventory batches track when products were received and used. Customer loyalty points track when points were earned or redeemed. All this enables time-based analysis and reporting.

**ID System:** System uses two types of IDs - internal database IDs (for efficiency) and human-readable IDs like "SESS-00042" or "ORDER-2024-0001" (for easy reference in reports, support calls, and audits).

---

## Design Approach

**Separation of Concerns:** Business logic separated from user interface. Services handle all data operations, views just handle user input/output. This makes system easier to maintain and test.

**Code Reuse:** Services work together rather than duplicating code. For example, online order service uses product service and inventory service, ensuring same rules apply everywhere.

**Abstraction:** Complex operations hidden behind simple interfaces. Database connection details hidden from business logic. Sync operations hidden from order processing. Notification delivery hidden from business operations.

---

## Common Questions & Answers

### Backend Questions

**"How does the system connect to the database?"**
- System reads connection settings from configuration file. Tries to connect to cloud database first. If that fails (wrong password, no internet), automatically uses local database. Checks connection status every 10 seconds.

**"Why organize code into services instead of putting everything in views?"**
- Services allow code reuse. For example, inventory deduction logic is used by both in-store sales and online orders, ensuring consistency. Views just validate user input and call the appropriate service.

**"What happens when a user logs in?"**
- System validates email and password. Creates two tokens - one for immediate use, one for refreshing. Records session with unique ID. Closes any previous active sessions for that user. Returns tokens to frontend.

**"How does cash reconciliation work?"**
- Cashier starts shift with opening cash amount. System tracks all cash sales throughout shift. When closing, cashier counts actual cash and enters amount. System calculates: actual cash minus opening cash minus cash sales = variance. If there's a difference, admins get email notification.

**"How does the system ensure products are sold in correct order (oldest first)?"**
- Products organized into batches by expiration date. When selling, system automatically finds oldest batch and deducts from there first. Records which batch was used for proper cost accounting.

**"When are online orders automatically cancelled?"**
- System checks every few minutes for orders that have been pending or confirmed for too long (default 30 minutes). Cancels them, puts inventory back, records why it was cancelled, and notifies staff.

**"How does offline mode work?"**
- When offline, all operations save to local database. Failed requests are queued in browser storage. When connection restored, background process automatically syncs queued requests and updates both local and cloud databases.

### Frontend Questions

**"How do you prevent unauthorized users from accessing the system?"**
- Router checks if user has valid login token stored. If not, redirects to login page. Token is checked on every server request. If token expired, system tries to refresh it automatically.

**"Why use composables for shared data?"**
- Composables allow multiple pages to share same data without passing it around. For example, product list and product search both use same product data and filters, keeping them in sync.

**"What happens if user's session expires while they're using the system?"**
- System automatically detects expired token, gets new token using refresh token, and retries the original request. User doesn't see any interruption or error message.

**"How does the system handle requests when internet is down?"**
- Failed requests are saved in browser storage with all details. Visual indicator shows how many requests are waiting. When internet comes back, system automatically processes all queued requests in order and shows progress.

**"How does barcode scanning work?"**
- When barcode is scanned, system sends barcode to server. Server finds product, checks current stock levels, and returns product details. System automatically adds product to active cart and shows confirmation.

### Data Questions

**"How are products linked to categories?"**
- Products store category ID as reference. To find all products in a category, system searches products by category ID. Categories stored separately, so updating category name doesn't require updating all products.

**"Why store order history inside the order document instead of separate table?"**
- Storing history with order makes it fast to see what happened - no need to search multiple tables. All related information stays together. If stored separately, would need to join tables every time, making queries slower.

**"How do you ensure inventory follows first-in-first-out?"**
- System sorts batches by expiration date (oldest first). When deducting stock, takes from oldest batch until quantity needed is met. Records which batch was used in usage history for tracking.

**"Why use both database IDs and readable IDs like SESS-00042?"**
- Database IDs are efficient for the system. Readable IDs are easy for humans - useful in reports, when talking to customers, during audits, and for support staff. System uses both to satisfy both needs.

### Operations Questions

**"How do you check if system is working before a demo?"**
- Hit the health check endpoint. It returns whether database is connected, if all services are running, and overall system status.

**"What's a quick test after deploying new code?"**
- 1) Check health endpoint, 2) Try logging in, 3) Create a test product, 4) Start a shift and process a test sale, 5) Check if offline mode indicator works.

**"If frontend can't connect to backend, where do you check?"**
- Check CORS settings in configuration files. These control which websites are allowed to connect. Development mode allows all connections for easier testing.

**"How do you find out why data isn't syncing?"**
- Check sync logs in database for errors and timestamps. Health check shows if databases are connected. Frontend shows how many requests are waiting to sync.

**"How does system handle importing thousands of products?"**
- Processes in batches (100 at a time) to avoid overwhelming system. Shows progress bar. Validates data before processing. Sends notification when complete with summary of successes and failures.
