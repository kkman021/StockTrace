<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { createBacktest, fetchBacktestSummary, fetchBacktests } from '@/api'
import type { BacktestRun, BacktestSummaryRow } from '@/api/types'
import EmptyState from '@/components/EmptyState.vue'

function todayMinusDays(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return d.toISOString().slice(0, 10)
}

const form = ref({
  start_date: todayMinusDays(60),
  end_date: todayMinusDays(0),
  holding_days: 5,
  breadth_threshold: 0.6,
  depth_threshold: 0.6,
  consecutive_days: 3,
  target_stocks: ''
})

const runs = ref<BacktestRun[]>([])
const selectedRun = ref<BacktestRun | null>(null)
const summary = ref<BacktestSummaryRow[]>([])
const submitting = ref(false)
const loadingSummary = ref(false)
const error = ref<string | null>(null)

async function loadRuns() {
  runs.value = await fetchBacktests()
}

async function loadSummary(run: BacktestRun) {
  selectedRun.value = run
  loadingSummary.value = true
  try {
    summary.value = await fetchBacktestSummary(run.id)
  } catch (e: any) {
    error.value = e?.message || '無法載入摘要'
  } finally {
    loadingSummary.value = false
  }
}

async function submit() {
  submitting.value = true
  error.value = null
  try {
    const payload = {
      start_date: form.value.start_date,
      end_date: form.value.end_date,
      holding_days: form.value.holding_days,
      breadth_threshold: form.value.breadth_threshold,
      depth_threshold: form.value.depth_threshold,
      consecutive_days: form.value.consecutive_days,
      target_stocks: form.value.target_stocks
        ? form.value.target_stocks
            .split(/[, ]+/)
            .map((s) => s.trim())
            .filter(Boolean)
        : undefined
    }
    const run = await createBacktest(payload)
    await loadRuns()
    await loadSummary(run)
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '回測失敗'
  } finally {
    submitting.value = false
  }
}

onMounted(loadRuns)

const sortedSummary = computed(() =>
  [...summary.value].sort((a, b) => b.avg_return - a.avg_return)
)

function fmtPct(v: number): string {
  return (v * 100).toFixed(2) + '%'
}
</script>

<template>
  <div class="space-y-6">
    <h2 class="text-xl font-semibold text-slate-800">回測沙盒</h2>

    <section class="card grid md:grid-cols-2 gap-4">
      <div class="grid grid-cols-2 gap-3">
        <label class="text-sm">
          <span class="text-slate-600 block mb-1">起始日</span>
          <input v-model="form.start_date" type="date" class="border border-slate-300 rounded px-2 py-1 w-full" />
        </label>
        <label class="text-sm">
          <span class="text-slate-600 block mb-1">結束日</span>
          <input v-model="form.end_date" type="date" class="border border-slate-300 rounded px-2 py-1 w-full" />
        </label>
        <label class="text-sm">
          <span class="text-slate-600 block mb-1">持有天數</span>
          <input v-model.number="form.holding_days" type="number" min="1" max="60" class="border border-slate-300 rounded px-2 py-1 w-full" />
        </label>
        <label class="text-sm">
          <span class="text-slate-600 block mb-1">連續達標天數</span>
          <input v-model.number="form.consecutive_days" type="number" min="1" max="10" class="border border-slate-300 rounded px-2 py-1 w-full" />
        </label>
        <label class="text-sm">
          <span class="text-slate-600 block mb-1">廣度門檻</span>
          <input v-model.number="form.breadth_threshold" type="number" step="0.05" min="0.1" max="0.9" class="border border-slate-300 rounded px-2 py-1 w-full" />
        </label>
        <label class="text-sm">
          <span class="text-slate-600 block mb-1">深度門檻</span>
          <input v-model.number="form.depth_threshold" type="number" step="0.05" min="0.1" max="0.9" class="border border-slate-300 rounded px-2 py-1 w-full" />
        </label>
      </div>
      <div class="flex flex-col gap-3">
        <label class="text-sm">
          <span class="text-slate-600 block mb-1">指定股票（選填，逗號分隔）</span>
          <input
            v-model="form.target_stocks"
            placeholder="例：2330, 2454"
            class="border border-slate-300 rounded px-2 py-1 w-full"
          />
        </label>
        <button class="btn-primary self-start" :disabled="submitting" @click="submit">
          {{ submitting ? '計算中…' : '執行回測' }}
        </button>
        <div v-if="error" class="text-sm text-rose-500">{{ error }}</div>
        <p class="text-xs text-slate-400 mt-auto">
          建立後同步執行；status=completed 即可查看摘要。
        </p>
      </div>
    </section>

    <section class="grid md:grid-cols-3 gap-6">
      <div class="md:col-span-1 card p-0 overflow-hidden">
        <header class="px-3 py-2 bg-slate-50 text-xs font-medium text-slate-600 border-b">
          歷史回測（{{ runs.length }}）
        </header>
        <EmptyState v-if="runs.length === 0" message="尚無回測紀錄" />
        <ul v-else class="divide-y divide-slate-100 max-h-96 overflow-auto">
          <li
            v-for="r in runs"
            :key="r.id"
            class="px-3 py-2 cursor-pointer hover:bg-slate-50"
            :class="{ 'bg-brand-50': selectedRun?.id === r.id }"
            @click="loadSummary(r)"
          >
            <div class="text-sm font-medium">#{{ r.id }} · {{ r.start_date }} → {{ r.end_date }}</div>
            <div class="text-xs text-slate-500">
              廣 {{ fmtPct(r.breadth_threshold) }} / 深 {{ fmtPct(r.depth_threshold) }} / 連 {{ r.consecutive_days }} / 持 {{ r.holding_days }}
            </div>
          </li>
        </ul>
      </div>

      <div class="md:col-span-2 card p-0 overflow-hidden">
        <header class="px-3 py-2 bg-slate-50 text-xs font-medium text-slate-600 border-b">
          {{ selectedRun ? `#${selectedRun.id} 統計摘要` : '選擇左側回測查看摘要' }}
        </header>
        <div v-if="loadingSummary" class="p-6 text-center text-slate-400">載入中…</div>
        <EmptyState
          v-else-if="!selectedRun || sortedSummary.length === 0"
          :message="selectedRun ? '此回測無有效訊號' : '尚未選擇'"
        />
        <table v-else class="w-full text-sm">
          <thead class="bg-slate-50 text-xs text-slate-600">
            <tr>
              <th class="px-3 py-2 text-left">股票</th>
              <th class="px-3 py-2 text-right">觸發數</th>
              <th class="px-3 py-2 text-right">勝率</th>
              <th class="px-3 py-2 text-right">平均報酬</th>
              <th class="px-3 py-2 text-right">最大</th>
              <th class="px-3 py-2 text-right">最小</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in sortedSummary" :key="r.stock_id" class="border-t border-slate-100">
              <td class="px-3 py-2">
                <div class="font-medium">{{ r.stock_name || r.stock_id }}</div>
                <div class="text-xs text-slate-400">{{ r.stock_id }}</div>
              </td>
              <td class="px-3 py-2 text-right tabular-nums">{{ r.trigger_count }}</td>
              <td class="px-3 py-2 text-right tabular-nums">{{ fmtPct(r.win_rate) }}</td>
              <td
                class="px-3 py-2 text-right tabular-nums font-medium"
                :class="r.avg_return >= 0 ? 'text-emerald-600' : 'text-rose-600'"
              >
                {{ fmtPct(r.avg_return) }}
              </td>
              <td class="px-3 py-2 text-right tabular-nums text-emerald-600">{{ fmtPct(r.max_return) }}</td>
              <td class="px-3 py-2 text-right tabular-nums text-rose-600">{{ fmtPct(r.min_return) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
