<script setup lang="ts">
import { RouterLink } from 'vue-router'

//
// What a share link may be. Answered here because it is the first question a
// user has and the cheapest one to answer - the alternative is finding out by
// pasting something unsupported and reading a refusal.
//
const SUPPORTED = [
  { name: '作品链接', hint: '单个视频或图文' },
  { name: '主播主页', hint: '该主播的全部作品' },
  { name: '直播链接', hint: '录制正在进行的直播' },
  { name: '分享文本', hint: '整段分享文字可以直接粘贴' },
]
</script>

<template>
  <section class="user-home" aria-labelledby="user-home-title">
    <p class="user-home__eyebrow">SocialMediaStreamDownloader</p>
    <h1 id="user-home-title">从分享链接开始下载</h1>
    <p class="user-home__description">
      粘贴分享内容，识别后即可开始下载，并随时查看下载状态。
    </p>

    <!--
      A list, not a second paste box. The download flow has one implementation
      and it lives on /new; this screen only points at it.
    -->
    <h2 class="user-home__subtitle">支持以下内容</h2>
    <ul class="user-home__supported">
      <li v-for="item in SUPPORTED" :key="item.name" class="user-home__supported-item">
        <span class="user-home__supported-name">{{ item.name }}</span>
        <span class="user-home__supported-hint">{{ item.hint }}</span>
      </li>
    </ul>

    <RouterLink class="user-home__action" :to="{ name: 'new-download' }">
      开始下载
    </RouterLink>
  </section>
</template>

<style scoped>
.user-home {
  max-width: 44rem;
  padding: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2);
}

.user-home__eyebrow {
  margin: 0 0 var(--space-2);
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--color-accent);
}

.user-home h1 {
  margin: 0;
}

.user-home__description {
  margin: var(--space-3) 0 var(--space-5);
  color: var(--color-muted);
}

.user-home__subtitle {
  margin: 0 0 var(--space-2);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-muted);
}

.user-home__supported {
  display: grid;
  gap: var(--space-2);
  margin: 0 0 var(--space-5);
  padding: 0;
  list-style: none;
}

.user-home__supported-item {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-1);
}

.user-home__supported-name {
  font-size: 0.875rem;
  font-weight: 600;
}

.user-home__supported-hint {
  color: var(--color-muted);
  font-size: 0.8125rem;
}

.user-home__action {
  display: inline-flex;
  padding: var(--space-2) var(--space-4);
  font-weight: 600;
  color: var(--color-surface);
  background: var(--color-accent);
  border-radius: var(--radius-1);
}
</style>
