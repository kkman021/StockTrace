<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { useSignalNotifications } from './composables/useNotifications'

const { start } = useSignalNotifications()

onMounted(() => {
  start()
})
</script>

<template>
  <div class="app">
    <header class="topbar">
      <div class="brand">
        <span class="logo">📡</span>
        <span class="title">ETF 雷達</span>
        <span class="subtitle muted">主動式 ETF 偵測</span>
      </div>
      <nav class="nav">
        <RouterLink to="/">儀表板</RouterLink>
        <RouterLink to="/reduction">減碼警示</RouterLink>
        <RouterLink to="/etf">ETF 名單</RouterLink>
        <RouterLink to="/config">門檻設定</RouterLink>
        <RouterLink to="/backtest">回測</RouterLink>
      </nav>
    </header>
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 32px;
  background: white;
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 50;
}

.brand {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.brand .logo {
  font-size: 18px;
}

.brand .title {
  font-weight: 700;
  font-size: 16px;
}

.brand .subtitle {
  font-size: 12px;
}

.nav {
  display: flex;
  gap: 4px;
}

.nav a {
  padding: 6px 12px;
  border-radius: var(--radius);
  text-decoration: none;
  color: var(--color-text);
  font-size: 13px;
  font-weight: 500;
}

.nav a:hover {
  background: #f3f4f6;
}

.nav a.router-link-active {
  background: var(--color-primary);
  color: white;
}

.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 32px;
}
</style>
