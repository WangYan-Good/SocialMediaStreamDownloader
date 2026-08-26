<template>
  <section class="forbidden" aria-labelledby="forbidden-title">
    <h1 id="forbidden-title">无权访问此页面</h1>
    <p>当前账户不能打开这个页面。</p>
    <RouterLink :to="{ name: 'user-home' }">返回首页</RouterLink>
  </section>
</template>

<style scoped>
.forbidden { max-width: 32rem; margin: var(--space-5) auto; padding: var(--space-5); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-2); }
.forbidden h1 { margin-top: 0; }
.forbidden p { color: var(--color-muted); }
</style>
