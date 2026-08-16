/// <reference types="vitest/config" />
import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig, loadEnv } from 'vite'

//
// The application owns root in production after P15.  Stated here once: the
// router reads it back through import.meta.env.BASE_URL rather than repeating
// the literal; built assets therefore live at /assets/.
//
const BASE = '/'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  //
  // Development only.  The bundle never carries a backend hostname: in
  // production the app is served by the same Flask process that answers /api,
  // so a same-origin relative path is both correct and the only thing that
  // survives being deployed anywhere.
  //
  const devApiTarget = env.VITE_DEV_API_TARGET || 'http://127.0.0.1:5001'

  return {
    base: BASE,
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      proxy: {
        '/api': {
          target: devApiTarget,
          changeOrigin: true,
        },
      },
    },
    test: {
      environment: 'jsdom',
      globals: true,
      include: ['tests/**/*.spec.ts'],
      restoreMocks: true,
    },
  }
})
