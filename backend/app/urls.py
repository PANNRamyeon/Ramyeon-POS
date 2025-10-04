from django.urls import path

from .kpi_views.Backoffice.session_views import (
    SessionLogsView,
    SessionDetailView,  
    SessionDisplayView, 
    CombinedLogsView,
    ActiveSessionsView,
    UserSessionsView,
    SessionStatisticsView,
    SessionCleanupView,
    CleanupStatusView,  
    AutoCleanupControlView,  
    SessionExportView,  
    ForceLogoutView,
    BulkSessionControlView, 
    SystemStatusView
)

from .kpi_views.Backoffice.user_views import (
    HealthCheckView, 
    UserListView, 
    UserDetailView, 
    UserByEmailView, 
    UserByUsernameView,
    UserRestoreView,       
    UserHardDeleteView,     
    DeletedUsersView,       
)

from .kpi_views.Backoffice.customer_views import (
    CustomerListView,
    CustomerDetailView,
    CustomerRestoreView,
    CustomerHardDeleteView,
    CustomerSearchView,
    CustomerByEmailView,
    CustomerStatisticsView,
    CustomerLoyaltyView,
)

from .kpi_views.Backoffice.supplier_views import (
    SupplierHealthCheckView,
    SupplierListView, 
    SupplierDetailView,
    SupplierRestoreView,
    SupplierHardDeleteView,
    DeletedSuppliersView,
    PurchaseOrderListView,
    PurchaseOrderDetailView,
    PurchaseOrderRestoreView,
    PurchaseOrderHardDeleteView,
    DeletedPurchaseOrdersView
)

from .kpi_views.Backoffice.authentication_views import (
    LoginView,
    LogoutView,
    RefreshTokenView,
    CurrentUserView,
    VerifyTokenView,
)

from .kpi_views.Backoffice.product_views import (
    # Product CRUD views
    ProductListView,
    ProductDetailView,
    ProductBySkuView,
    ProductRestoreView,
    
    # Stock management views
    ProductStockUpdateView,
    BulkStockUpdateView,
    StockHistoryView,
    StockAdjustmentView,
    RestockProductView,
    
    # Product reports views
    LowStockProductsView,
    ExpiringProductsView,
    ProductsByCategoryView,
    DeletedProductsView,
    
    # Product sync views
    ProductSyncView,
    
    # Product import/export views
    ProductImportView,
    ProductExportView,
    BulkCreateProductsView,
    ImportTemplateView,
)

from .kpi_views.Backoffice.category_views import (
     CategoryKPIView,
    CategoryDetailView,
    CategorySoftDeleteView,
    CategoryHardDeleteView,
    CategoryRestoreView,                  
    CategoryDeletedListView,               
    CategoryBulkOperationsView,         
    CategoryDeleteInfoView,               
    CategorySubcategoryView,              
    UncategorizedCategoryView,              
    SubcategoryProductsView,                
    ProductSubcategoryUpdateView,
    ProductMoveToUncategorizedView,
)

# POS Operations
from .kpi_views.Backoffice.category_pos_views import (
    POSCatalogView,
    POSProductBatchView,
    POSBarcodeView,
    POSSearchView,
    POSStockCheckView,
    POSLowStockView,
    POSSubcategoryProductsView,  
)

# Display/Export Operations
from .kpi_views.Backoffice.category_display_views import (
    CategoryDataView,
    CategoryExportView,
    CategoryStatsView,
)

from .kpi_views.Backoffice.promotion_views import (
     PromotionHealthCheckView,
    PromotionListView,
    PromotionDetailView,
    PromotionByNameView,
    PromotionRestoreView,
    DeletedPromotionsView,  
    PromotionHardDeleteView,
    ActivePromotionsView,
    PromotionActivationView,
    PromotionDeactivationView,
    PromotionExpirationView,
    PromotionApplicationView,
    PromotionStatisticsView,
    PromotionAuditView,
    PromotionSearchView,
    PromotionReportView,
)

from .kpi_views.POS.pos_sales_views import (
    POSSalesCreateView,
    POSSalesDetailView,
    POSSalesListView,
    POSSalesVoidView,
    POSSalesDailySummaryView,
    POSSalesShiftSummaryView,
    POSSalesCashierPerformanceView,
    POSSalesExportView,
    POSSalesReceiptView
)

from .kpi_views.POS.cart_views import (
    CartCreateView,
    CartView,
    CartAddItemView,
    CartItemView,
    CartDiscountView,
    CartPrepareCheckoutView,
    CartClearView,
    CartItemCountView,
    CartScanProductView
)

from .views import (
    APIDocumentationView,
)

urlpatterns = [
    # ========== SYSTEM & HEALTH ==========
    path('', SystemStatusView.as_view(), name='system-status'),  # Root endpoint
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('docs/', APIDocumentationView.as_view(), name='api-documentation'),
    
    # ========== AUTHENTICATION ==========
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', RefreshTokenView.as_view(), name='refresh-token'),
    path('auth/me/', CurrentUserView.as_view(), name='current-user'),
    path('auth/verify-token/', VerifyTokenView.as_view(), name='verify-token'),
    
    # ========== USER MANAGEMENT ==========
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/deleted/', DeletedUsersView.as_view(), name='deleted-users'),
    path('users/email/<str:email>/', UserByEmailView.as_view(), name='user-by-email'),
    path('users/username/<str:username>/', UserByUsernameView.as_view(), name='user-by-username'),
    path('users/<str:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<str:user_id>/restore/', UserRestoreView.as_view(), name='user-restore'),
    path('users/<str:user_id>/hard-delete/', UserHardDeleteView.as_view(), name='user-hard-delete'),
    
    # ========== CUSTOMER MANAGEMENT ==========
    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('customers/search/', CustomerSearchView.as_view(), name='customer-search'),
    path('customers/statistics/', CustomerStatisticsView.as_view(), name='customer-statistics'),
    path('customers/email/<str:email>/', CustomerByEmailView.as_view(), name='customer-by-email'),
    path('customers/<str:customer_id>/', CustomerDetailView.as_view(), name='customer-detail'),
    path('customers/<str:customer_id>/restore/', CustomerRestoreView.as_view(), name='customer-restore'),
    path('customers/<str:customer_id>/hard-delete/', CustomerHardDeleteView.as_view(), name='customer-hard-delete'),
    path('customers/<str:customer_id>/loyalty/', CustomerLoyaltyView.as_view(), name='customer-loyalty'),
    
    # ========== SUPPLIER MANAGEMENT ==========
    path('suppliers/health/', SupplierHealthCheckView.as_view(), name='health-check'),

    # === SPECIFIC PATHS FIRST (no parameters) ===
    path('suppliers/deleted/', DeletedSuppliersView.as_view(), name='deleted-suppliers'),

    # === SUPPLIER CRUD ===
    path('suppliers/', SupplierListView.as_view(), name='supplier-list'),
    path('suppliers/<str:supplier_id>/', SupplierDetailView.as_view(), name='supplier-detail'),

    # === SUPPLIER MANAGEMENT ===
    path('suppliers/<str:supplier_id>/restore/', SupplierRestoreView.as_view(), name='supplier-restore'),
    path('suppliers/<str:supplier_id>/hard-delete/', SupplierHardDeleteView.as_view(), name='supplier-hard-delete'),

    # === PURCHASE ORDER - SPECIFIC PATHS FIRST ===
    path('suppliers/<str:supplier_id>/orders/deleted/', DeletedPurchaseOrdersView.as_view(), name='deleted-purchase-orders'),

    # === PURCHASE ORDER CRUD ===
    path('suppliers/<str:supplier_id>/orders/', PurchaseOrderListView.as_view(), name='purchase-order-list'),
    path('suppliers/<str:supplier_id>/orders/<str:order_id>/', PurchaseOrderDetailView.as_view(), name='purchase-order-detail'),

    # === PURCHASE ORDER MANAGEMENT ===
    path('suppliers/<str:supplier_id>/orders/<str:order_id>/restore/', PurchaseOrderRestoreView.as_view(), name='purchase-order-restore'),
    path('suppliers/<str:supplier_id>/orders/<str:order_id>/hard-delete/', PurchaseOrderHardDeleteView.as_view(), name='purchase-order-hard-delete'),
        
    # ========== SESSION MANAGEMENT ==========
    path('session-logs/', SessionLogsView.as_view(), name='session-logs'),
    path('session-logs/display/', SessionDisplayView.as_view(), name='session-logs-display'),  # Move this BEFORE the parameterized one
    path('session-logs/combined/', CombinedLogsView.as_view(), name='combined-logs'),
    path('session-logs/<str:session_id>/', SessionDetailView.as_view(), name='session-detail'),
    # Session management
    path('sessions/active/', ActiveSessionsView.as_view(), name='active-sessions'),
    path('sessions/user/<str:user_id>/', UserSessionsView.as_view(), name='user-sessions'),
    path('sessions/statistics/', SessionStatisticsView.as_view(), name='session-statistics'),
    # Cleanup and maintenance (Admin only)
    path('sessions/cleanup/', SessionCleanupView.as_view(), name='session-cleanup'),
    path('sessions/cleanup/status/', CleanupStatusView.as_view(), name='cleanup-status'),  
    path('sessions/cleanup/auto/', AutoCleanupControlView.as_view(), name='auto-cleanup-control'),  
    # Export functionality (Admin only)
    path('sessions/export/', SessionExportView.as_view(), name='session-export'), 
    # Admin control endpoints
    path('sessions/force-logout/<str:user_id>/', ForceLogoutView.as_view(), name='force-logout'),
    path('sessions/bulk-control/', BulkSessionControlView.as_view(), name='bulk-session-control'),  
    
    # ========== PRODUCT MANAGEMENT ==========
    # Product CRUD (static paths first)
    path('products/', ProductListView.as_view(), name='product-list'),  # GET (list), POST (create)
    path('products/sku/<str:sku>/', ProductBySkuView.as_view(), name='product-by-sku'),  # GET by SKU
    path('products/deleted/', DeletedProductsView.as_view(), name='deleted-products'),  # GET deleted products
    
    # Product import/export
    path('products/import/', ProductImportView.as_view(), name='product-import'),  # POST
    path('products/import/template/', ImportTemplateView.as_view(), name='import-template'),  # GET
    path('products/export/', ProductExportView.as_view(), name='product-export'),  # GET
    path('products/bulk-create/', BulkCreateProductsView.as_view(), name='bulk-create-products'),  # POST
    
    # Product reports
    path('products/reports/low-stock/', LowStockProductsView.as_view(), name='low-stock-products'),  # GET
    path('products/reports/expiring/', ExpiringProductsView.as_view(), name='expiring-products'),  # GET
    path('products/reports/by-category/<str:category_id>/', ProductsByCategoryView.as_view(), name='products-by-category'),  # GET
    
    # Product synchronization
    path('products/sync/', ProductSyncView.as_view(), name='product-sync'),  # POST
    
    # Bulk stock management
    path('products/stock/bulk-update/', BulkStockUpdateView.as_view(), name='bulk-stock-update'),  # POST
    
    # Product detail operations (parameterized paths last)
    path('products/<str:product_id>/', ProductDetailView.as_view(), name='product-detail'),  # GET, PUT, DELETE
    path('products/<str:product_id>/restore/', ProductRestoreView.as_view(), name='product-restore'),  # POST
    path('products/<str:product_id>/stock/', ProductStockUpdateView.as_view(), name='product-stock-update'),  # PUT/PATCH
    path('products/<str:product_id>/stock/adjust/', StockAdjustmentView.as_view(), name='stock-adjustment'),  # POST
    path('products/<str:product_id>/stock/history/', StockHistoryView.as_view(), name='stock-history'),  # GET
    path('products/<str:product_id>/restock/', RestockProductView.as_view(), name='restock-product'),  # POST

    
    # ========== CATEGORY MANAGEMENT ==========
    # Core Category Operations
    path('category/', CategoryKPIView.as_view(), name='category-operations'),
    path('category/stats/', CategoryStatsView.as_view(), name='category-stats'),
    path('category/display/', CategoryDataView.as_view(), name='category-display'),
    path('category/export/', CategoryExportView.as_view(), name='category-export'),
    path('category/bulk/', CategoryBulkOperationsView.as_view(), name='category-bulk-operations'),

    # Admin-only Category Operations
    path('category/deleted/', CategoryDeletedListView.as_view(), name='category-deleted-list'),
    path('category/uncategorized/', UncategorizedCategoryView.as_view(), name='uncategorized-category'),

    # Individual Category Operations
    path('category/<str:category_id>/', CategoryDetailView.as_view(), name='category-detail'),
    path('category/<str:category_id>/delete-info/', CategoryDeleteInfoView.as_view(), name='category-delete-info'),
    path('category/<str:category_id>/soft-delete/', CategorySoftDeleteView.as_view(), name='category-soft-delete'),
    path('category/<str:category_id>/hard-delete/', CategoryHardDeleteView.as_view(), name='category-hard-delete'),
    path('category/<str:category_id>/restore/', CategoryRestoreView.as_view(), name='category-restore'),
    path('category/<str:category_id>/subcategories/', CategorySubcategoryView.as_view(), name='category-subcategories'),
    path('category/<str:category_id>/subcategories/<str:subcategory_name>/products/', SubcategoryProductsView.as_view(), name='subcategory-products'),

    # ========== POS OPERATIONS ==========
    path('pos/catalog/', POSCatalogView.as_view(), name='pos-catalog'),
    path('pos/products/batch/', POSProductBatchView.as_view(), name='pos-product-batch'),
    path('pos/search/', POSSearchView.as_view(), name='pos-search'),
    path('pos/barcode/<str:barcode>/', POSBarcodeView.as_view(), name='pos-barcode'),
    path('pos/stock/check/', POSStockCheckView.as_view(), name='pos-stock-check'),
    path('pos/stock/low/', POSLowStockView.as_view(), name='pos-low-stock'),
    path('pos/category/<str:category_id>/subcategory/<str:subcategory_name>/products/', POSSubcategoryProductsView.as_view(), name='pos-subcategory-products'),

    # ========== PRODUCT-CATEGORY RELATIONSHIPS ==========
    path('product/subcategory/update/', ProductSubcategoryUpdateView.as_view(), name='product-subcategory-update'),
    path('product/move-uncategorized/', ProductMoveToUncategorizedView.as_view(), name='product-move-uncategorized'),  
       
    # ========== PROMOTIONS ==========
    path('promotions/', PromotionListView.as_view(), name='promotion-list'),  # GET (list), POST (create)
    path('promotions/health/', PromotionHealthCheckView.as_view(), name='promotion-health'),  # GET
    path('promotions/active/', ActivePromotionsView.as_view(), name='active-promotions'),  # GET
    path('promotions/deleted/', DeletedPromotionsView.as_view(), name='promotion-deleted-list'),  # GET - Admin only
    path('promotions/search/', PromotionSearchView.as_view(), name='promotion-search'),  # GET
    path('promotions/statistics/', PromotionStatisticsView.as_view(), name='promotion-statistics'),  # GET - Admin only
    path('promotions/apply/', PromotionApplicationView.as_view(), name='promotion-apply'),  # POST
    path('promotions/by-name/<str:promotion_name>/', PromotionByNameView.as_view(), name='promotion-by-name'),  # GET
    path('promotions/<str:promotion_id>/', PromotionDetailView.as_view(), name='promotion-detail'),  # GET, PUT, DELETE
    path('promotions/<str:promotion_id>/activate/', PromotionActivationView.as_view(), name='promotion-activate'),  # POST - Admin only
    path('promotions/<str:promotion_id>/deactivate/', PromotionDeactivationView.as_view(), name='promotion-deactivate'),  # POST - Admin only
    path('promotions/<str:promotion_id>/expire/', PromotionExpirationView.as_view(), name='promotion-expire'),  # POST - Admin only
    path('promotions/<str:promotion_id>/restore/', PromotionRestoreView.as_view(), name='promotion-restore'),  # POST - Admin only
    path('promotions/<str:promotion_id>/hard-delete/', PromotionHardDeleteView.as_view(), name='promotion-hard-delete'),  # DELETE - Admin only
    path('promotions/<str:promotion_id>/audit/', PromotionAuditView.as_view(), name='promotion-audit'),  # GET - Admin only
    path('promotions/<str:promotion_id>/report/', PromotionReportView.as_view(), name='promotion-report'),  # GET - Admin only

    # ========== POS OPERATIONS ==========
    path('pos/sales/', POSSalesListView.as_view(), name='pos-sales-list'),
    path('pos/sales/create/', POSSalesCreateView.as_view(), name='pos-sales-create'),
    path('pos/sales/daily-summary/', POSSalesDailySummaryView.as_view(), name='pos-sales-daily-summary'),
    path('pos/sales/shift-summary/<str:shift_id>/', POSSalesShiftSummaryView.as_view(), name='pos-sales-shift-summary'),
    path('pos/sales/cashier-performance/', POSSalesCashierPerformanceView.as_view(), name='pos-sales-cashier-performance'),
    path('pos/sales/export/', POSSalesExportView.as_view(), name='pos-sales-export'),
    path('pos/sales/<str:sale_id>/', POSSalesDetailView.as_view(), name='pos-sales-detail'),
    path('pos/sales/<str:sale_id>/void/', POSSalesVoidView.as_view(), name='pos-sales-void'),
    path('pos/sales/<str:sale_id>/receipt/', POSSalesReceiptView.as_view(), name='pos-sales-receipt'),

     # ================================================================
    # CART ENDPOINTS
    # ================================================================
    
    # Create and list
    path('pos/carts/', CartCreateView.as_view()),
    path('pos/carts/<str:cart_id>/clear/', CartClearView.as_view()),
    path('pos/carts/<str:cart_id>/prepare-checkout/', CartPrepareCheckoutView.as_view()),
    path('pos/carts/<str:cart_id>/item-count/', CartItemCountView.as_view()),
    path('pos/carts/<str:cart_id>/scan/', CartScanProductView.as_view()),
    path('pos/carts/<str:cart_id>/items/', CartAddItemView.as_view()),
    path('pos/carts/<str:cart_id>/items/<str:product_id>/', CartItemView.as_view()),
    path('pos/carts/<str:cart_id>/discount/', CartDiscountView.as_view()),
    path('pos/carts/<str:cart_id>/', CartView.as_view()),

  ]