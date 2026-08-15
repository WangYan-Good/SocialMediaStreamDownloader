/// <reference types="vite/client" />

interface ImportMetaEnv {
  //
  // Where the json api lives, relative to wherever the app is served from.
  // Relative on purpose - see vite.config.ts.
  //
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
