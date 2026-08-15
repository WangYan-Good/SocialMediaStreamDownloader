<script setup lang="ts">
//
// Why this page shows what it shows, and why it cannot change any of it.
//
// Configuration is loaded once at startup and held per process. A control here
// that appeared to save something would report success while every worker kept
// running on the old values - which is worse than having no control at all.
//
</script>

<template>
  <section class="notice" aria-labelledby="system-notice-heading">
    <h2 id="system-notice-heading" class="notice__title">关于本页</h2>
    <ul class="notice__list">
      <li>本页面仅展示当前进程已经加载的安全配置摘要。</li>
      <li>数据库凭据、Cookie、令牌、代理与文件路径等敏感字段不会发送到浏览器。</li>
      <li>配置修改需在服务器侧完成，并重启服务后生效；本页面不提供保存、应用或重载。</li>
    </ul>
  </section>
</template>

<style scoped>
.notice { padding: var(--space-4); background: var(--color-background); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.notice__title { margin: 0 0 var(--space-2); font-size: 0.875rem; }
.notice__list { margin: 0; padding-left: var(--space-4); color: var(--color-muted); font-size: 0.8125rem; line-height: 1.8; }
</style>
