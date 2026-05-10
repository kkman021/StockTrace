<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { consensusApi } from '../api/consensus'
import type { ReductionRow } from '../types'
import { SIGNAL_TAG_COLORS, SIGNAL_TAG_LABELS } from '../types'

const rows = ref<ReductionRow[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const riskOnly = ref(false)

const latestDate = computed(() => rows.value[0]?.date ?? null)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    rows.value = await consensusApi.reduction({
      risk_only: riskOnly.value,
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

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar">
      <h1>減碼風險警示</h1>
      <div style="display: flex; gap: 12px; align-items: center;">
        <span v-if="latestDate" class="muted">資料日期：{{ latestDate }}</span>
        <label class="checkbox-row" style="margin: 0;">
          <input type="checkbox" v-model="riskOnly" @change="load" />
          僅顯示風險警示
        </label>
        <button class="btn" @click="load" :disabled="loading">重新整理</button>
      </div>
    </div>

    <div class="banner banner-info">
      減碼共識僅作風險警示用途，不應作為放空依據（規格 §10.1）。
    </div>

    <div v-if="error" class="banner banner-error">{{ error }}</div>

    <div v-if="!loading && rows.length === 0" class="empty">
      目前沒有減碼活動需要關注。
    </div>

    <table v-else-if="rows.length > 0" class="data-table">
      <thead>
        <tr>
          <th>股票</th>
          <th class="num">減碼廣度</th>
          <th class="num">減碼 ETF 數</th>
          <th class="num">連續</th>
          <th>警示等級</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.stock_id">
          <td>
            <strong>{{ row.stock_id }}</strong>
            <span v-if="row.stock_name" class="muted"> {{ row.stock_name }}</span>
          </td>
          <td class="num">{{ fmtPct(row.reduction_breadth) }}</td>
          <td class="num">{{ row.reduction_etf_count ?? '-' }}</td>
          <td class="num">{{ row.reduction_consec ?? 0 }} 日</td>
          <td>
            <span
              v-if="row.risk_tag"
              class="tag"
              :style="{ background: SIGNAL_TAG_COLORS[row.risk_tag] }"
            >
              {{ SIGNAL_TAG_LABELS[row.risk_tag] ?? row.risk_tag }}
            </span>
            <span v-else class="muted">—</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
