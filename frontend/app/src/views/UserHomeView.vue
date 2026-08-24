<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <section class="user-home" aria-labelledby="user-home-title">
    <p class="user-home__eyebrow">SocialMediaStreamDownloader</p>
    <h1 id="user-home-title">从分享链接开始下载</h1>
    <p class="user-home__description">
      粘贴分享链接，即可识别并下载作品、主播内容或直播。
    </p>
    <RouterLink class="user-home__action" :to="{ name: 'new-download' }">
      新建下载
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

.user-home__action {
  display: inline-flex;
  padding: var(--space-2) var(--space-4);
  font-weight: 600;
  color: var(--color-surface);
  background: var(--color-accent);
  border-radius: var(--radius-1);
}
</style>
