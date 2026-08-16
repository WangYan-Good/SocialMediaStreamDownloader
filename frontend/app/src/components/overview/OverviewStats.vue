<script setup lang="ts">
defineProps<{
  creatorTotal: number | null
  creatorsError: string | null
  postTotal: number | null
  postsError: string | null
  liveTotal: number | null
  livesError: string | null
  taskTotal: number | null
  tasksError: string | null
}>()

//
// A count that could not be read is not a count of zero. "暂不可用" says the
// second thing; a 0 would state the first while meaning it.
//
function statText(total: number | null, error: string | null): string {
  if (error !== null && total === null) {
    return '暂不可用'
  }
  return total === null ? '—' : String(total)
}

//
// Why it is unavailable, in place of what it usually means. A tile that only
// said "暂不可用" would leave the reader guessing between an empty database and
// an unreachable one - which is exactly the distinction this page exists to
// make visible.
//
function statHint(hint: string, error: string | null): string {
  return error === null ? hint : error
}
</script>

<template>
  <section class="stats" aria-label="内容统计">
    <div class="stat">
      <p class="stat__value">{{ statText(creatorTotal, creatorsError) }}</p>
      <!--
        Local database fact, said as one. Not "全平台创作者" and not "活跃主播":
        this is how many accounts this installation has seen before.
      -->
      <p class="stat__label">已知账号</p>
      <p class="stat__hint">{{ statHint('数据库已记录的账号数', creatorsError) }}</p>
    </div>
    <div class="stat">
      <p class="stat__value">{{ statText(postTotal, postsError) }}</p>
      <p class="stat__label">已下载作品</p>
      <!--
        Records, not files. Nothing in this application has checked the disk.
      -->
      <p class="stat__hint">{{ statHint('数据库中的下载记录数', postsError) }}</p>
    </div>
    <div class="stat">
      <p class="stat__value">{{ statText(liveTotal, livesError) }}</p>
      <p class="stat__label">直播记录</p>
      <p class="stat__hint">{{ statHint('数据库中的直播观察记录数', livesError) }}</p>
    </div>
    <div class="stat">
      <p class="stat__value">{{ statText(taskTotal, tasksError) }}</p>
      <p class="stat__label">任务记录</p>
      <!--
        The task store lives in this process and is subject to retention, so
        this is not a lifetime total and must not be labelled as one.
      -->
      <p class="stat__hint">{{ statHint('当前进程的任务记录数', tasksError) }}</p>
    </div>
  </section>
</template>

<style scoped>
.stats { display: grid; gap: var(--space-3); grid-template-columns: 1fr; }
@media (min-width: 40rem) { .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (min-width: 70rem) { .stats { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
.stat { padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.stat__value { margin: 0; font-size: 1.75rem; font-weight: 600; }
.stat__label { margin: var(--space-1) 0 0; font-size: 0.875rem; }
.stat__hint { margin: 2px 0 0; color: var(--color-muted); font-size: 0.75rem; }
</style>
