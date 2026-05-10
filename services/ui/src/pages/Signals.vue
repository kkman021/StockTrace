<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { fetchSignals } from '@/api'
import type { SignalRow } from '@/api/types'
import EmptyState from '@/components/EmptyState.vue'

const today = new Date().toISOString().slice(0, 10)
const date = ref(today)
const filter = ref<'all' | 'add' | 'reduce'>('all')
const rows = ref<SignalRow[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    rows.value = await fetchSignals(date.value, filter.value === 'all' ? undefined : filter.value)
  } catch (e: any) {
    error.value = e?.message || '載入失敗'
    rows.value = []
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch([date, filter], load)

const sorted = computed(() =>
  [...rows.value].sort((a, b) =>
    a.signal_type === b.signal_type
      ? (b.breadth_score ?? 0) - (a.breadth_score ?? 0)
      : a.signal_type === 'add'
        ? -1
        : 1
  )
)

function fmtPct(v: number | null): string {
  return v == null ? '—' : (v * 100).toFixed(1) + '%'
}
</script>

<template>
  <div class="space-y-6">
    <header class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-slate-800">訊號清單</h2>
      <div class="flex items-center gap-2">
        <input
          v-model="date"
          type="date"
          class="border border-slate-300 rounded px-2 py-1 text-sm"
        />
        <select
          v-model="filter"
          class="border border-slate-300 rounded px-2 py-1 text-sm"
        >
          <option value="all">全部</option>
          <option value="add">加碼</option>
          <option value="reduce">減碼</option>
        </select>
      </div>
    </header>

    <section class="card p-0 overflow-hidden">
      <div v-if="loading" class="p-6 text-center text-slate-400">載入中…</div>
      <div v-else-if="error" class="p-6 text-center text-rose-500">{{ error }}</div>
      <EmptyState
        v-else-if="sorted.length === 0"
        message="當日無訊號"
        hint="符合門檻才會在此出現"
      />
      <ul v-else class="divide-y divide-slate-100">
        <li v-for="r in sorted" :key="r.id" class="px-4 py-3 flex items-center gap-3">
          <span :class="r.signal_type === 'add' ? 'badge-add' : 'badge-reduce'">
            {{ r.signal_type === 'add' ? '加碼' : '減碼' }}
          </span>
          <div class="flex-1 min-w-0">
            <div class="font-medium text-slate-800">
              {{ r.stock_name || r.stock_id }}
              <span class="text-xs text-slate-400 font-normal ml-1">{{ r.stock_id }}</span>
            </div>
            <div class="text-xs text-slate-500 mt-0.5">
              <span class="mr-3">標籤 {{ r.signal_tag }}</span>
              <span class="mr-3">廣度 {{ fmtPct(r.breadth_score) }}</span>
              <span class="mr-3">深度 {{ fmtPct(r.depth_score) }}</span>
              <span>連續 {{ r.consecutive_days ?? 0 }} 日</span>
            </div>
          </div>
          <span class="text-xs text-slate-400 tabular-nums">{{ r.date }}</span>
        </li>
      </ul>
    </section>
  </div>
</template>
