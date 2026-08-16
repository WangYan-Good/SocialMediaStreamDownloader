import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

import CreatorsView from '@/views/CreatorsView.vue'
import LibraryView from '@/views/LibraryView.vue'
import NewDownloadView from '@/views/NewDownloadView.vue'
import OverviewView from '@/views/OverviewView.vue'
import SystemView from '@/views/SystemView.vue'
import TasksView from '@/views/TasksView.vue'

//
// The information architecture the migration is heading towards, not the one
// the legacy interface has.  The old sections - History, Posts, Person, Log,
// Settings - are grouped by which page happened to exist; these are grouped by
// what the user is trying to do, and each is filled in by a later stage.
//
export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: { name: 'overview' },
  },
  {
    path: '/overview',
    name: 'overview',
    component: OverviewView,
  },
  {
    path: '/new',
    name: 'new-download',
    component: NewDownloadView,
  },
  {
    path: '/creators',
    name: 'creators',
    component: CreatorsView,
  },
  {
    path: '/library',
    name: 'library',
    component: LibraryView,
  },
  {
    path: '/tasks',
    name: 'tasks',
    component: TasksView,
  },
  {
    path: '/system',
    name: 'system',
    component: SystemView,
  },
  {
    //
    // Anything else lands on the overview rather than on a dead end.  The
    // server already hands the shell back for every non-reserved root path, so
    // an unknown one reaches the router; deciding what it means is the router's
    // job, and "start at the beginning" is the honest answer while most of the
    // application is still to come.
    //
    path: '/:pathMatch(.*)*',
    redirect: { name: 'overview' },
  },
]

export const router = createRouter({
  //
  // Read from the build rather than written twice.  Vite is configured with
  // its root base, and hard-coding the same literal here is how the two drift
  // apart the first time either one moves.
  //
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
