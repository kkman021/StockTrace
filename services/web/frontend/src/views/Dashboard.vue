<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { consensusApi } from '../api/consensus'
import type { ConsensusRow } from '../types'
import { SIGNAL_TAG_COLORS, SIGNAL_TAG_LABELS } from '../types'

const rows = ref<ConsensusRow[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const signalOnly = ref(false)

const latestDate = computed(() => rows.value[0]?.date ?? null)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    rows.value = await consensusApi.latest({
      signal_only: signalOnly.value,
      limit: 100,
    })
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

function fmtPct(value: string | null): string {
  if (value == null) return '-'
  return `${(parseFloat(value) * 100).toFixed(1)}%`
}

function fmtAmount(value: number | null): string {
  if (value == null) return '-'
  if (value >= 100_000_000) return `${(value / 100_000_000).toFixed(1)} 億`
  if (value >= 10_000) return `${(value / 10_000).toFixed(1)} 萬`
  return value.toLocaleString()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar">
      <h1>每日加碼共識排行</h1>
      <div style="display: flex; gap: 12px; align-items: center;">
        <span v-if="latestDate" class="muted">資料日期：{{ latestDate }}</span>
        <label class="checkbox-row" style="margin: 0;">
          <input type="checkbox" v-model="signalOnly" @change="load" />
          僅顯示有訊號
        </label>
        <button class="btn" @click="load" :disabled="loading">重新整理</button>
      </div>
    </div>

    <div v-if="error" class="banner banner-error">{{ error }}</div>

    <div v-if="!loading && rows.length === 0" class="empty">
      尚無共識資料。請先在 ETF 名單建立追蹤項目，並等待 18:30 排程執行（或透過 admin endpoint 觸發分析）。
    </div>

    <table v-else-if="rows.length > 0" class="data-table">
      <thead>
        <tr>
          <th>股票</th>
          <th class="num">廣度</th>
          <th class="num">深度</th>
          <th class="num">加碼 ETF 數</th>
          <th class="num">加碼金額</th>
          <th class="num">連續</th>
          <th>訊號</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.stock_id">
          <td>
            <strong>{{ row.stock_id }}</strong>
            <span v-if="row.stock_name" class="muted"> {{ row.stock_name }}</span>
          </td>
          <td class="num">{{ fmtPct(row.breadth_score) }}</td>
          <td class="num">{{ fmtPct(row.depth_score) }}</td>
          <td class="num">{{ row.accumulate_etf_count ?? '-' }}</td>
          <td class="num">{{ fmtAmount(row.total_amount) }}</td>
          <td class="num">{{ row.consecutive_days ?? 0 }} 日</td>
          <td>
            <span
              v-if="row.signal_tag"
              class="tag"
              :style="{ background: SIGNAL_TAG_COLORS[row.signal_tag] }"
            >
              {{ SIGNAL_TAG_LABELS[row.signal_tag] ?? row.signal_tag }}
            </span>
            <span v-else class="muted">—</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
