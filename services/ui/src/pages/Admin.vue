<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  fetchConfig,
  fetchCrawlStatus,
  fetchEtfs,
  resetCrawler,
  triggerAnalyze,
  triggerCrawl,
  triggerDetect,
  triggerSingleCrawl,
  updateConfig
} from '@/api'
import type { CrawlStatusResponse, EtfRow, SystemConfigEntry } from '@/api/types'
import EmptyState from '@/components/EmptyState.vue'
import StatCard from '@/components/StatCard.vue'

const today = new Date().toISOString().slice(0, 10)
const date = ref(today)

const status = ref<CrawlStatusResponse | null>(null)
const etfs = ref<EtfRow[]>([])
const configs = ref<SystemConfigEntry[]>([])
const loadingStatus = ref(false)
const triggering = ref<string | null>(null)
const message = ref<string | null>(null)
const error = ref<string | null>(null)

async function loadStatus() {
  loadingStatus.value = true
  try {
    status.value = await fetchCrawlStatus(date.value)
  } catch (e: any) {
    error.value = e?.message || '監控載入失敗'
  } finally {
    loadingStatus.value = false
  }
}

async function loadEtfs() {
  etfs.value = await fetchEtfs()
}

async function loadConfig() {
  configs.value = await fetchConfig()
}

async function withFlash(action: string, fn: () => Promise<unknown>) {
  triggering.value = action
  message.value = null
  error.value = null
  try {
    await fn()
    message.value = `${action} 完成`
    await loadStatus()
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || `${action} 失敗`
  } finally {
    triggering.value = null
  }
}

async function saveConfig(c: SystemConfigEntry) {
  await updateConfig(c.key, c.value)
  message.value = `已更新 ${c.key}`
}

async function reset(etfId: string) {
  await resetCrawler(etfId)
  message.value = `已重置 ${etfId} 的 crawler 狀態`
  await Promise.all([loadStatus(), loadEtfs()])
}

onMounted(async () => {
  await Promise.all([loadStatus(), loadEtfs(), loadConfig()])
})

watch(date, loadStatus)

const statusBadge = (s: 'success' | 'failed' | undefined | null) => {
  if (s === 'success') return 'badge-success'
  if (s === 'failed') return 'badge-failed'
  return 'badge'
}
</script>

<template>
  <div class="space-y-6">
    <header class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-slate-800">管理 / 監控</h2>
      <input
        v-model="date"
        type="date"
        class="border border-slate-300 rounded px-2 py-1 text-sm"
      />
    </header>

    <div v-if="message" class="rounded bg-emerald-50 border border-emerald-200 text-emerald-700 px-3 py-2 text-sm">
      {{ message }}
    </div>
    <div v-if="error" class="rounded bg-rose-50 border border-rose-200 text-rose-700 px-3 py-2 text-sm">
      {{ error }}
    </div>

    <section class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <StatCard label="ETF 總數" :value="status?.total ?? '—'" />
      <StatCard
        label="當日成功"
        :value="status?.success_today ?? '—'"
        tone="positive"
      />
      <StatCard
        label="當日失敗"
        :value="status ? status.total - status.success_today : '—'"
        tone="negative"
      />
      <StatCard
        label="待補抓"
        :value="status ? status.items.filter((x) => !x.today_log).length : '—'"
        hint="尚未跑出 crawl_log"
      />
    </section>

    <section class="card flex flex-wrap gap-2 items-center">
      <span class="text-sm text-slate-600 mr-2">手動觸發：</span>
      <button class="btn-primary" :disabled="!!triggering" @click="withFlash('全量爬取', () => triggerCrawl(date))">
        全量爬取
      </button>
      <button class="btn-ghost" :disabled="!!triggering" @click="withFlash('補抓缺漏', () => triggerCrawl(date, true))">
        補抓缺漏
      </button>
      <button class="btn-ghost" :disabled="!!triggering" @click="withFlash('跑分析', () => triggerAnalyze(date))">
        跑分析
      </button>
      <button class="btn-ghost" :disabled="!!triggering" @click="withFlash('偵測訊號', () => triggerDetect(date))">
        偵測訊號
      </button>
    </section>

    <section class="card p-0 overflow-hidden">
      <header class="px-3 py-2 bg-slate-50 text-xs font-medium text-slate-600 border-b">
        ETF 爬蟲狀態（{{ status?.items.length ?? 0 }}）
      </header>
      <div v-if="loadingStatus" class="p-6 text-center text-slate-400">載入中…</div>
      <EmptyState v-else-if="!status || status.items.length === 0" message="無資料" />
      <table v-else class="w-full text-sm">
        <thead class="bg-slate-50 text-xs text-slate-600">
          <tr>
            <th class="px-3 py-2 text-left">ETF</th>
            <th class="px-3 py-2 text-left">模式</th>
            <th class="px-3 py-2 text-right">Fallback</th>
            <th class="px-3 py-2 text-left">當日狀態</th>
            <th class="px-3 py-2 text-right">筆數</th>
            <th class="px-3 py-2 text-right">耗時(ms)</th>
            <th class="px-3 py-2 text-left">最後成功</th>
            <th class="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in status.items"
            :key="item.etf_id"
            class="border-t border-slate-100 hover:bg-slate-50"
          >
            <td class="px-3 py-2">
              <div class="font-medium">{{ item.etf_name }}</div>
              <div class="text-xs text-slate-400">{{ item.etf_id }}</div>
            </td>
            <td class="px-3 py-2">
              <span :class="item.crawler_mode === 'light' ? 'badge-light' : 'badge-playwright'">
                {{ item.crawler_mode }}
              </span>
            </td>
            <td class="px-3 py-2 text-right tabular-nums">{{ item.fallback_count }}</td>
            <td class="px-3 py-2">
              <span v-if="item.today_log" :class="statusBadge(item.today_log.status)">
                {{ item.today_log.status }}
              </span>
              <span v-else class="text-xs text-slate-400">未爬</span>
            </td>
            <td class="px-3 py-2 text-right tabular-nums">
              {{ item.today_log?.records_count ?? '—' }}
            </td>
            <td class="px-3 py-2 text-right tabular-nums">
              {{ item.today_log?.duration_ms ?? '—' }}
            </td>
            <td class="px-3 py-2 text-xs text-slate-500">
              {{ item.last_success_date || '—' }}
            </td>
            <td class="px-3 py-2 text-right">
              <button class="btn-ghost mr-1 text-xs" @click="withFlash(`重爬 ${item.etf_id}`, () => triggerSingleCrawl(item.etf_id, date))">
                重爬
              </button>
              <button v-if="item.crawler_mode === 'playwright'" class="btn-ghost text-xs" @click="reset(item.etf_id)">
                重置
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="card p-0 overflow-hidden">
      <header class="px-3 py-2 bg-slate-50 text-xs font-medium text-slate-600 border-b">
        系統參數
      </header>
      <table class="w-full text-sm">
        <thead class="bg-slate-50 text-xs text-slate-600">
          <tr>
            <th class="px-3 py-2 text-left">key</th>
            <th class="px-3 py-2 text-left">value</th>
            <th class="px-3 py-2 text-left">說明</th>
            <th class="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in configs" :key="c.key" class="border-t border-slate-100">
            <td class="px-3 py-2 font-mono text-xs">{{ c.key }}</td>
            <td class="px-3 py-2">
              <input
                v-model="c.value"
                class="border border-slate-300 rounded px-2 py-1 text-sm w-32"
              />
            </td>
            <td class="px-3 py-2 text-xs text-slate-500">{{ c.description || '—' }}</td>
            <td class="px-3 py-2 text-right">
              <button class="btn-ghost text-xs" @click="saveConfig(c)">儲存</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>
