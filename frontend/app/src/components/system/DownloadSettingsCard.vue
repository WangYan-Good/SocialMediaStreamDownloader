<script setup lang="ts">
import {
  enabledLabel,
  numberLabel,
  switchLabel,
  textLabel,
} from '@/components/system/systemPresentation'
import type { SystemDouyinSettings, SystemDownloadSettings } from '@/types/system'

defineProps<{ download: SystemDownloadSettings; douyin: SystemDouyinSettings }>()
</script>

<template>
  <section class="card" aria-labelledby="system-download-heading">
    <h2 id="system-download-heading" class="card__title">下载设置</h2>

    <!--
      Read only, all of it. There is no endpoint behind this page that writes,
      so there is nothing here to submit.
    -->
    <dl class="facts">
      <div class="facts__row"><dt>测试模式</dt><dd>{{ switchLabel(download.test_mode) }}</dd></div>
      <div class="facts__row"><dt>按作者建目录</dt><dd>{{ switchLabel(download.folderize) }}</dd></div>
      <div class="facts__row"><dt>监听模式</dt><dd>{{ switchLabel(download.listening) }}</dd></div>
      <div class="facts__row"><dt>使用登录态</dt><dd>{{ switchLabel(download.user_login) }}</dd></div>
    </dl>

    <!--
      Says the behaviour differs, and stops there. Claiming "nothing will be
      written" would be a guarantee this page cannot check.
    -->
    <p v-if="download.test_mode === true" class="card__warning" role="status">
      当前为测试模式，下载行为可能与正常模式不同。
    </p>

    <h3 class="card__subtitle">作品下载</h3>
    <dl class="facts">
      <div class="facts__row"><dt>并发</dt><dd>{{ numberLabel(douyin.aweme.concurrency) }}</dd></div>
      <div class="facts__row"><dt>HTML 兜底</dt><dd>{{ enabledLabel(douyin.aweme.html_fallback) }}</dd></div>
      <div class="facts__row"><dt>跳过已下载</dt><dd>{{ enabledLabel(douyin.aweme.skip_downloaded) }}</dd></div>
      <div class="facts__row"><dt>视频质量</dt><dd>{{ textLabel(douyin.aweme.video_quality) }}</dd></div>
      <div class="facts__row">
        <dt>媒体类型</dt>
        <dd>
          视频 {{ switchLabel(douyin.aweme.media.video) }} ·
          图片 {{ switchLabel(douyin.aweme.media.images) }} ·
          音乐 {{ switchLabel(douyin.aweme.media.music) }} ·
          封面 {{ switchLabel(douyin.aweme.media.cover) }}
        </dd>
      </div>
    </dl>

    <h3 class="card__subtitle">主播批量</h3>
    <dl class="facts">
      <div class="facts__row"><dt>每页数量</dt><dd>{{ numberLabel(douyin.owner.page_size) }}</dd></div>
      <div class="facts__row"><dt>下载并发</dt><dd>{{ numberLabel(douyin.owner.download_concurrency) }}</dd></div>
    </dl>

    <h3 class="card__subtitle">直播检查</h3>
    <dl class="facts">
      <div class="facts__row"><dt>单批上限</dt><dd>{{ numberLabel(douyin.live_probe.max_batch_size) }}</dd></div>
      <div class="facts__row"><dt>并发</dt><dd>{{ numberLabel(douyin.live_probe.concurrency) }}</dd></div>
      <div class="facts__row"><dt>缓存有效期（秒）</dt><dd>{{ numberLabel(douyin.live_probe.cache_ttl_seconds) }}</dd></div>
    </dl>
  </section>
</template>

<style scoped>
.card { padding: var(--space-4); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.card__title { margin: 0 0 var(--space-3); font-size: 1rem; }
.card__subtitle { margin: var(--space-4) 0 var(--space-2); font-size: 0.875rem; color: var(--color-muted); }
.card__warning { margin: var(--space-3) 0 0; padding: var(--space-2) var(--space-3); background: var(--color-background); border: 1px solid #e6a9a9; border-radius: var(--radius-1); color: #a12a2a; font-size: 0.8125rem; line-height: 1.6; }
.facts { margin: 0; display: grid; gap: var(--space-2); }
.facts__row { display: grid; grid-template-columns: 9rem 1fr; gap: var(--space-3); align-items: baseline; }
.facts__row dt { color: var(--color-muted); font-size: 0.8125rem; }
.facts__row dd { margin: 0; font-size: 0.875rem; overflow-wrap: anywhere; }
</style>
