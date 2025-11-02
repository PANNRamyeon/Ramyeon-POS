import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

// Import authentication and layout components
import Login from '../pages/Login.vue'
import MainLayout from '../layouts/MainLayout.vue'
import Dashboard from '../pages/Home.vue'
import OnlineOrder from '@/pages/OnlineOrders.vue'
import NewOrder from '@/pages/NewOrder.vue'
import Settings from '@/pages/Settings.vue'
import History from '@/pages/History.vue'
import Checkout from '@/pages/Checkout.vue'
import Shift from '@/pages/Shift.vue'
import ShiftSummary from '@/pages/ShiftSummary.vue'
import PaymentCallback from '@/components/PaymentCallback.vue'

// Auth guard function
function requireAuth(to, from, next) {
  const token = localStorage.getItem('authToken')
  if (token) {
    next() // User is authenticated, proceed
  } else {
    next('/login') // Redirect to login
  }
}

// Guest guard function (redirect authenticated users away from login)
function requireGuest(to, from, next) {
  const token = localStorage.getItem('authToken')
  if (!token) {
    next() // User is not authenticated, proceed to login
  } else {
    next('/dashboard') // Redirect to dashboard if already logged in
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login' // Make Login the default page
    },
    {
      path: '/login',
      name: 'Login',
      component: Login,
      beforeEnter: requireGuest // Only allow access if not logged in
    },
    // Protected routes that use the main layout
    {
      path: '/',
      component: MainLayout,
      beforeEnter: requireAuth,
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: Dashboard
        },
        {
          path: 'online-order',
          name: 'OnlineOrder',
          component: OnlineOrder
        },
        {
          path: 'new-order',
          name: 'NewOrder',
          component: NewOrder
        },
        {
          path: 'settings',
          name: 'Settings',
          component: Settings
        },
        {
          path: 'history',
          name: 'History',
          component: History
        },
        {
          path: 'shift',
          name: 'Shift',
          component: Shift
        },
        {
          path: 'checkout',
          name: 'Checkout',
          component: Checkout,
          meta: { requiresAuth: true }
        },
        {
          path: 'shift-summary/:shiftId',
          name: 'ShiftSummary',
          component: ShiftSummary
        }
      ]
    },
    // Payment callback route (outside MainLayout for cleaner UI)
    {
      path: '/pos/payment-callback',
      name: 'PaymentCallback',
      component: PaymentCallback,
      beforeEnter: requireAuth,
      meta: { requiresAuth: true }
    },
    // Catch all route - redirect to login
    {
      path: '/:pathMatch(.*)*',
      redirect: '/login'
    }
  ],
})

// Global navigation guard
router.beforeEach((to, from, next) => {
  next()
})

export default router