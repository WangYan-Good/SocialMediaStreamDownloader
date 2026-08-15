//
// What the server is willing to say about itself.
//
// Every field here exists on the backend's explicit whitelist. There is
// deliberately no index signature and no `unknown` bag: a type that could carry
// arbitrary configuration would let a future backend field reach the browser
// without anybody deciding it should.
//

/** How the database schema guard last classified the schema. */
export type SystemDatabaseState =
  | 'ready'
  | 'unavailable'
  | 'blocked'
  | 'disabled'
  //
  // No guard installed, or one that failed unexpectedly. Reported rather than
  // guessed in either direction.
  //
  | 'unknown'

export interface SystemDatabaseStatus {
  /** Whether persistence is switched on at all - a separate question from the schema. */
  enabled: boolean
  state: SystemDatabaseState
  write_ready: boolean
  //
  // A fixed sentence chosen by the server per state. Never the guard's own
  // reason, which is internal wording that may name a host.
  //
  message: string
}

export interface SystemServerSettings {
  //
  // The bind host and port are deliberately absent: they describe where the
  // process listens, which is infrastructure rather than something this page
  // needs to show.
  //
  debug_mode: boolean | null
}

export interface SystemLoggingSettings {
  enabled: boolean | null
  level: string | null
  save_enabled: boolean | null
  //
  // There is no path here, and no log content anywhere in this contract. The
  // log holds urls, creator identities and upstream errors, and this project
  // has no redaction rule for any of it.
  //
}

export interface SystemDownloadSettings {
  test_mode: boolean | null
  folderize: boolean | null
  listening: boolean | null
  user_login: boolean | null
}

export interface SystemHistorySettings {
  page_size_limit: number | null
}

export interface SystemMediaSettings {
  video: boolean | null
  images: boolean | null
  music: boolean | null
  cover: boolean | null
}

export interface SystemAwemeSettings {
  concurrency: number | null
  html_fallback: boolean | null
  skip_downloaded: boolean | null
  video_quality: string | null
  media: SystemMediaSettings
}

export interface SystemOwnerSettings {
  page_size: number | null
  download_concurrency: number | null
}

export interface SystemLiveProbeSettings {
  max_batch_size: number | null
  concurrency: number | null
  cache_ttl_seconds: number | null
}

export interface SystemDouyinSettings {
  aweme: SystemAwemeSettings
  owner: SystemOwnerSettings
  live_probe: SystemLiveProbeSettings
}

export interface SystemSettings {
  server: SystemServerSettings
  logging: SystemLoggingSettings
  download: SystemDownloadSettings
  history: SystemHistorySettings
  douyin: SystemDouyinSettings
}

export interface SystemStatus {
  database: SystemDatabaseStatus
  settings: SystemSettings
}
