<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { configApi } from '../api/config'
import type { ThresholdConfig } from '../types'

const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)

const form = reactive<ThresholdConfig>({
  breadth_threshold: 0.6,
  depth_threshold: 0.6,
  consecutive_days: 3,
  sliding_window: 5,
  reduction_breadth_threshold: 0.6,
  reduction_consecutive_days: 3,
})

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const cfg = await configApi.get()
    Object.assign(form, cfg)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

async function save(): Promise<void> {
  saving.value = true
  error.value = null
  success.value = null
  try {
    const cfg = await configApi.patch({ ...form })
    Object.assign(form, cfg)
    success.value = '已儲存。runtime 即時生效，歷史訊號不會重算。'
    setTimeout(() => (success.value = null), 4000)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    saving.value = false
  }
}

function pct(n: number): string {
  return `${(n * 100).toFixed(0)}%`
}

onMounted(load)
</script>

<template>
  <div>
    <h1>門檻參數設定</h1>

    <div v-if="error" class="banner banner-error">{{ error }}</div>
    <div v-if="success" class="banner banner-info">{{ success }}</div>

    <div class="card" style="max-width: 640px;">
      <h2>加碼共識門檻</h2>
      <p class="muted" style="margin-top: -8px;">規格 §11.1。所有參數即時生效，不需重啟 container。</p>

      <div class="form-row">
        <label>廣度門檻：{{ pct(form.breadth_threshold) }}</label>
        <input
          type="range"
          min="0.1"
          max="0.9"
          step="0.05"
          v-model.number="form.breadth_threshold"
        />
        <span class="hint">M / N，多少比例的經理人在加碼。允許 10% – 90%</span>
      </div>

      <div class="form-row">
        <label>深度門檻：{{ pct(form.depth_threshold) }}</label>
        <input
          type="range"
          min="0.1"
          max="0.9"
          step="0.05"
          v-model.number="form.depth_threshold"
        />
        <span class="hint">Σ加碼金額 / Σ AUM，多少比例的資金在加碼</span>
      </div>

      <div class="form-row">
        <label>連續加碼天數門檻：{{ form.consecutive_days }} 日</label>
        <input
          type="range"
          min="1"
          max="10"
          step="1"
          v-model.number="form.consecutive_days"
        />
        <span class="hint">高度共識需要連續達標的最少天數，1 – 10 日</span>
      </div>

      <div class="form-row">
        <label>滑動窗口：{{ form.sliding_window }} 日</label>
        <input
          type="range"
          min="3"
          max="20"
          step="1"
          v-model.number="form.sliding_window"
        />
        <span class="hint">連續性追蹤的回看天數，3 – 20 日</span>
      </div>

      <h2 style="margin-top: 24px;">減碼風險門檻</h2>
      <p class="muted" style="margin-top: -8px;">獨立設定，僅作風險警示用（規格 §10）。</p>

      <div class="form-row">
        <label>減碼廣度門檻：{{ pct(form.reduction_breadth_threshold) }}</label>
        <input
          type="range"
          min="0.1"
          max="0.9"
          step="0.05"
          v-model.number="form.reduction_breadth_threshold"
        />
      </div>

      <div class="form-row">
        <label>減碼連續天數門檻：{{ form.reduction_consecutive_days }} 日</label>
        <input
          type="range"
          min="1"
          max="10"
          step="1"
          v-model.number="form.reduction_consecutive_days"
        />
      </div>

      <div style="margin-top: 20px;">
        <button class="btn btn-primary" @click="save" :disabled="saving">
          {{ saving ? '儲存中…' : '儲存' }}
        </button>
        <button class="btn" style="margin-left: 8px;" @click="load" :disabled="loading">
          重設為目前值
        </button>
      </div>
    </div>
  </div>
</template>
