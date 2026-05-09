<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header>
    <nav>
      <RouterLink to="/">儀表板</RouterLink>
      <RouterLink to="/reduction">減碼警示</RouterLink>
      <RouterLink to="/etf">ETF 名單</RouterLink>
      <RouterLink to="/config">門檻設定</RouterLink>
      <RouterLink to="/backtest">回測</RouterLink>
    </nav>
  </header>
  <main>
    <RouterView />
  </main>
</template>

<style scoped>
header {
  padding: 12px 24px;
  border-bottom: 1px solid #ddd;
}
nav a {
  margin-right: 16px;
  text-decoration: none;
}
nav a.router-link-active {
  font-weight: 700;
}
main {
  padding: 24px;
}
</style>
