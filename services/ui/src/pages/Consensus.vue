<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { fetchConsensus } from '@/api'
import type { ConsensusRow } from '@/api/types'
import EmptyState from '@/components/EmptyState.vue'
import StatCard from '@/components/StatCard.vue'

const today = new Date().toISOString().slice(0, 10)
const date = ref(today)
const filter = ref<'all' | 'add' | 'reduce'>('all')
const rows = ref<ConsensusRow[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    rows.value = await fetchConsensus(date.value, filter.value === 'all' ? undefined : filter.value)
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
  [...rows.value].sort((a, b) => (b.breadth_score ?? 0) - (a.breadth_score ?? 0))
)

const stats = computed(() => ({
  total: rows.value.length,
  add: rows.value.filter((r) => r.signal_tag).length,
  reduce: rows.value.filter((r) => r.risk_tag).length,
  highConsensus: rows.value.filter((r) => (r.breadth_score ?? 0) >= 0.7).length
}))

function fmtPct(v: number | null): string {
  return v == null ? '—' : (v * 100).toFixed(1) + '%'
}
</script>

<template>
  <div class="space-y-6">
    <header class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-slate-800">共識榜</h2>
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
          <option value="add">加碼類</option>
          <option value="reduce">減碼類</option>
        </select>
      </div>
    </header>

    <section class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <StatCard label="當日股票數" :value="stats.total" />
      <StatCard label="加碼訊號" :value="stats.add" tone="positive" />
      <StatCard label="減碼訊號" :value="stats.reduce" tone="negative" />
      <StatCard
        label="高度共識 (廣度≥70%)"
        :value="stats.highConsensus"
        hint="breadth_score ≥ 0.7"
      />
    </section>

    <section class="card p-0 overflow-hidden">
      <div v-if="loading" class="p-6 text-center text-slate-400">載入中…</div>
      <div v-else-if="error" class="p-6 text-center text-rose-500">{{ error }}</div>
      <EmptyState
        v-else-if="sorted.length === 0"
        message="當日沒有共識資料"
        hint="可能尚未跑分析，或非交易日"
      />
      <table v-else class="w-full text-sm">
        <thead class="bg-slate-50 text-slate-600 text-xs">
          <tr>
            <th class="px-3 py-2 text-left">股票</th>
            <th class="px-3 py-2 text-right">廣度</th>
            <th class="px-3 py-2 text-right">深度</th>
            <th class="px-3 py-2 text-right">連續</th>
            <th class="px-3 py-2 text-left">加碼標籤</th>
            <th class="px-3 py-2 text-left">減碼標籤</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in sorted"
            :key="r.stock_id"
            class="border-t border-slate-100 hover:bg-slate-50"
          >
            <td class="px-3 py-2">
              <div class="font-medium text-slate-800">{{ r.stock_name || r.stock_id }}</div>
              <div class="text-xs text-slate-400">{{ r.stock_id }}</div>
            </td>
            <td class="px-3 py-2 text-right tabular-nums">{{ fmtPct(r.breadth_score) }}</td>
            <td class="px-3 py-2 text-right tabular-nums">{{ fmtPct(r.depth_score) }}</td>
            <td class="px-3 py-2 text-right tabular-nums">{{ r.consecutive_days ?? '—' }}</td>
            <td class="px-3 py-2">
              <span v-if="r.signal_tag" class="badge-add">{{ r.signal_tag }}</span>
            </td>
            <td class="px-3 py-2">
              <span v-if="r.risk_tag" class="badge-reduce">{{ r.risk_tag }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>
