import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

import AdminLayout from '@/layouts/AdminLayout.vue'
import UserLayout from '@/layouts/UserLayout.vue'
import AuthUnavailableView from '@/views/AuthUnavailableView.vue'
import CreatorsView from '@/views/CreatorsView.vue'
import ForbiddenView from '@/views/ForbiddenView.vue'
import LibraryView from '@/views/LibraryView.vue'
import LoginView from '@/views/LoginView.vue'
import NewDownloadView from '@/views/NewDownloadView.vue'
import SystemView from '@/views/SystemView.vue'
import TasksView from '@/views/TasksView.vue'
import UserHomeView from '@/views/UserHomeView.vue'
import UserLibraryView from '@/views/UserLibraryView.vue'
import UserTasksView from '@/views/UserTasksView.vue'

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: UserLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'user-home',
        component: UserHomeView,
      },
      {
        path: 'new',
        name: 'new-download',
        component: NewDownloadView,
      },
      {
        path: 'library',
        name: 'library',
        component: UserLibraryView,
      },
      {
        path: 'tasks',
        name: 'tasks',
        component: UserTasksView,
      },
    ],
  },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        redirect: { name: 'admin-creators' },
      },
      {
        path: 'creators',
        name: 'admin-creators',
        component: CreatorsView,
      },
      //
      // The management library, unchanged. The user route above shows a subset
      // of the same records; this one keeps every column, the person filter and
      // the collaboration tab.
      //
      {
        path: 'library',
        name: 'admin-library',
        component: LibraryView,
      },
      //
      // The management task view, unchanged. The user route above shows the
      // same tasks; this one keeps the ids, the raw metadata and the limit.
      //
      {
        path: 'tasks',
        name: 'admin-tasks',
        component: TasksView,
      },
      {
        path: 'system',
        name: 'admin-system',
        component: SystemView,
      },
    ],
  },
  //
  // Sign-in, outside both consoles.
  //
  // Deliberately not behind a console layout. The authorization guard decides
  // whether this guest route or a protected destination is appropriate.
  //
  {
    path: '/login',
    name: 'login',
    component: LoginView,
  },
  {
    path: '/forbidden',
    name: 'forbidden',
    component: ForbiddenView,
    meta: { requiresAuth: true },
  },
  {
    path: '/auth-unavailable',
    name: 'auth-unavailable',
    component: AuthUnavailableView,
  },
  {
    path: '/overview',
    name: 'overview',
    redirect: { name: 'user-home' },
  },
  {
    path: '/creators',
    name: 'creators',
    redirect: { name: 'admin-creators' },
  },
  {
    path: '/system',
    name: 'system',
    redirect: { name: 'admin-system' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    redirect: '/',
  },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
