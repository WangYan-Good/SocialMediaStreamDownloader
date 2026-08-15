import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * Shell state, and nothing else.
 *
 * Deliberately not a domain store.  A `taskStore` or a `downloadStore` written
 * now would be written against screens that do not exist yet, and would have to
 * be rewritten by the stage that finally needs it - so each arrives with the
 * feature that gives it a shape.
 */
export const useAppStore = defineStore('app', () => {
  const sidebarOpen = ref(false)

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }

  function closeSidebar() {
    sidebarOpen.value = false
  }

  return { sidebarOpen, toggleSidebar, closeSidebar }
})
