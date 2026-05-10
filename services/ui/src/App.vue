<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'

const navItems = [
  { to: '/consensus', label: '共識榜' },
  { to: '/signals', label: '訊號清單' },
  { to: '/backtest', label: '回測' },
  { to: '/admin', label: '管理' }
]
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <header class="bg-white border-b border-slate-200 sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 py-3 flex items-center gap-6">
        <h1 class="text-lg font-bold text-brand-700">StockTrace</h1>
        <nav class="flex gap-1">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="px-3 py-1.5 rounded text-sm font-medium text-slate-600 hover:bg-slate-100"
            active-class="bg-brand-50 text-brand-700"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
        <div class="flex-1" />
        <span class="text-xs text-slate-400">ETF 共識雷達</span>
      </div>
    </header>

    <main class="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
      <RouterView />
    </main>

    <footer class="text-center text-xs text-slate-400 py-3">
      共識分數僅供研究參考，非投資建議
    </footer>
  </div>
</template>
