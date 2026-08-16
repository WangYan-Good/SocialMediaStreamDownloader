import type { HistoryOwner } from '../../src/types/history'
import type { LibraryLive, LibraryPost } from '../../src/types/library'
import type { SystemStatus } from '../../src/types/system'
import type { Task } from '../../src/types/task'

//
// Shared builders, in a module of their own rather than exported from a spec:
// importing a spec re-runs its describes under the importing file's setup.
//

export function systemStatus(overrides: Partial<SystemStatus> = {}): SystemStatus {
  return {
    database: {
      enabled: true,
      state: 'ready',
      write_ready: true,
      message: '数据库架构已就绪',
    },
    settings: {
      server: { debug_mode: false },
      logging: { enabled: true, level: 'INFO', save_enabled: true },
      download: { test_mode: false, folderize: true, listening: false, user_login: false },
      history: { page_size_limit: 10 },
      douyin: {
        aweme: {
          concurrency: 3,
          html_fallback: true,
          skip_downloaded: true,
          video_quality: 'highest',
          media: { video: true, images: true, music: true, cover: true },
        },
        owner: { page_size: 18, download_concurrency: 3 },
        live_probe: { max_batch_size: 10, concurrency: 3, cache_ttl_seconds: 60 },
      },
    },
    ...overrides,
  }
}

export function task(overrides: Partial<Task> = {}): Task {
  return {
    task_id: 'T-1',
    task_type: 'post_download',
    state: 'success',
    title: '一条作品',
    message: null,
    created_at: '2026-08-16T09:30:15.250',
    started_at: null,
    finished_at: null,
    progress: { current: 1, total: 1 },
    metadata: {},
    items: [],
    ...overrides,
  }
}

export function historyOwner(overrides: Partial<HistoryOwner> = {}): HistoryOwner {
  return {
    owner_user_id: '58859666123',
    sec_user_id: 'MS4w',
    nickname: '主播',
    live_share_url: null,
    directory_name: '主播',
    user_status: '正常',
    actived_count: 12,
    score: null,
    favorite: false,
    last_live_status: 4,
    last_checked_at: '2026-08-16T09:00:00.000',
    last_room_id: null,
    ...overrides,
  }
}

export function libraryPost(overrides: Partial<LibraryPost> = {}): LibraryPost {
  return {
    platform: 'douyin',
    aweme_id: '7300000000000000001',
    owner_user_id: '58859666123',
    sec_user_id: 'MS4w',
    nickname: '主播',
    directory_name: '主播',
    person_id: null,
    person_display_name: null,
    aweme_type: 'video',
    desc: '最近下载的一条作品',
    create_time: null,
    downloaded_at: '2026-08-16T09:30:15.250',
    media_count: 3,
    saved_count: 3,
    save_dir: '/mnt/video/主播',
    source: 'api',
    ...overrides,
  }
}

export function libraryLive(overrides: Partial<LibraryLive> = {}): LibraryLive {
  return {
    observed_at: '2026-08-16T09:30:15.250',
    platform: 'douyin',
    room_id: '7123',
    owner_user_id: '58859666123',
    nickname: '主播',
    directory_name: '主播',
    person_id: null,
    person_display_name: null,
    title: '晚间直播',
    room_status: 2,
    start_time: null,
    finish_time: null,
    status_code: 0,
    ...overrides,
  }
}
