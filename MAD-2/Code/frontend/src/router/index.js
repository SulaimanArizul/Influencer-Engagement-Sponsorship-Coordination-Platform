import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: LoginView
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView
    },
    {
      path: '/profile/:id',
      name: 'profile',
      component: () => import('../views/influencer/ProfileView.vue')
    },

    {
      path: '/admin',
      children: [
        {
          path: '',
          name: 'admin',
          component: () => import('@/views/admin/DashboardView.vue')
        },
        {
          path: 'users/:tableName',
          name: 'users',
          component: () => import('@/views/admin/UsersView.vue')
        }
      ]
    },

    {
      path: '/sponsor',
      children: [
        {
          path: '',
          name: 'sponsor',
          component: () => import('../views/sponsor/HomeView.vue')
        },

        {
          path: 'ad-requests/:id',
          name: 's-ad-requests',
          component: () => import('../views/sponsor/Ad-RequestsView.vue')
        }
      ]
    },

    {
      path: '/influencer',
      children: [
        {
          path: '',
          name: 'influencer',
          component: () => import('../views/influencer/HomeView.vue')
        },
        {
          path: 'ad-requests/:id',
          name: 'i-ad-requests',
          component: () => import('../views/influencer/Ad-RequestsView.vue')
        }
      ]
    }
  ]
})

export default router
