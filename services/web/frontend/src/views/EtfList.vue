<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { etfApi } from '../api/etf'
import type { Etf, EtfCreate } from '../types'

const items = ref<Etf[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

interface FormState {
  mode: 'create' | 'edit'
  visible: boolean
  data: EtfCreate
}

const form = reactive<FormState>({
  mode: 'create',
  visible: false,
  data: emptyForm(),
})

function emptyForm(): EtfCreate {
  return {
    etf_id: '',
    etf_name: '',
    issuer: '',
    disclosure_url: '',
    aum_url: null,
    aum_source: 'inline',
    crawler_mode: 'light',
    is_active: true,
    notes: null,
  }
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    items.value = await etfApi.list()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

function openCreate(): void {
  form.mode = 'create'
  form.data = emptyForm()
  form.visible = true
}

function openEdit(etf: Etf): void {
  form.mode = 'edit'
  form.data = {
    etf_id: etf.etf_id,
    etf_name: etf.etf_name,
    issuer: etf.issuer,
    disclosure_url: etf.disclosure_url,
    aum_url: etf.aum_url,
    aum_source: etf.aum_source,
    crawler_mode: etf.crawler_mode,
    is_active: etf.is_active,
    notes: etf.notes,
  }
  form.visible = true
}

async function submit(): Promise<void> {
  error.value = null
  try {
    if (form.mode === 'create') {
      await etfApi.create(form.data)
    } else {
      const { etf_id, ...patch } = form.data
      await etfApi.update(etf_id, patch)
    }
    form.visible = false
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

async function resetCrawler(etf: Etf): Promise<void> {
  if (!window.confirm(`確認將 ${etf.etf_id} 的爬蟲模式重設為 light、計數器歸零？`)) return
  try {
    await etfApi.resetCrawler(etf.etf_id)
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

async function overrideAum(etf: Etf): Promise<void> {
  const input = window.prompt(
    `輸入 ${etf.etf_id} 的 AUM（元，最後手動備援）：`,
    etf.last_known_aum?.toString() ?? '',
  )
  if (!input) return
  const aum = Number(input.replace(/[^0-9]/g, ''))
  if (!Number.isFinite(aum) || aum <= 0) return
  try {
    await etfApi.overrideAum(etf.etf_id, aum)
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar">
      <h1>ETF 名單管理</h1>
      <button class="btn btn-primary" @click="openCreate">新增 ETF</button>
    </div>

    <div v-if="error" class="banner banner-error">{{ error }}</div>

    <div v-if="!loading && items.length === 0" class="empty">
      尚無追蹤 ETF。點上方「新增 ETF」開始建立名單。
    </div>

    <table v-else-if="items.length > 0" class="data-table">
      <thead>
        <tr>
          <th>代號</th>
          <th>名稱</th>
          <th>投信</th>
          <th>狀態</th>
          <th>爬蟲</th>
          <th>連續失敗</th>
          <th>最後成功</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="etf in items" :key="etf.etf_id">
          <td><strong>{{ etf.etf_id }}</strong></td>
          <td>{{ etf.etf_name }}</td>
          <td>{{ etf.issuer }}</td>
          <td>
            <span class="tag" :style="{ background: etf.is_active ? '#16a34a' : '#6b7280' }">
              {{ etf.is_active ? '啟用' : '停用' }}
            </span>
          </td>
          <td>
            <span class="muted">{{ etf.crawler_mode }}</span>
          </td>
          <td class="num">{{ etf.fallback_count }}</td>
          <td class="muted">{{ etf.last_success_date ?? '—' }}</td>
          <td>
            <button class="btn btn-sm" @click="openEdit(etf)">編輯</button>
            <button class="btn btn-sm" @click="resetCrawler(etf)">重設爬蟲</button>
            <button class="btn btn-sm" @click="overrideAum(etf)">覆寫 AUM</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="form.visible" class="modal-backdrop" @click.self="form.visible = false">
      <div class="modal">
        <h2>{{ form.mode === 'create' ? '新增追蹤 ETF' : `編輯 ${form.data.etf_id}` }}</h2>

        <div class="form-row">
          <label>ETF 代號</label>
          <input
            type="text"
            v-model="form.data.etf_id"
            :disabled="form.mode === 'edit'"
            placeholder="00982A"
          />
          <span class="hint">建立後不可修改</span>
        </div>

        <div class="form-row">
          <label>ETF 名稱</label>
          <input type="text" v-model="form.data.etf_name" placeholder="群益台灣ESG主動式" />
        </div>

        <div class="form-row">
          <label>投信公司</label>
          <input type="text" v-model="form.data.issuer" placeholder="群益投信" />
        </div>

        <div class="form-row">
          <label>持股公告 URL</label>
          <input type="url" v-model="form.data.disclosure_url" />
        </div>

        <div class="form-row">
          <label>AUM 獨立 URL（選填）</label>
          <input type="url" v-model="form.data.aum_url" />
          <span class="hint">若 AUM 與持股在同頁，留空並選 inline</span>
        </div>

        <div class="form-row">
          <label>AUM 資料位置</label>
          <select v-model="form.data.aum_source">
            <option value="inline">inline（與持股同頁）</option>
            <option value="separate">separate（獨立頁面）</option>
          </select>
        </div>

        <div class="form-row">
          <label>爬蟲模式</label>
          <select v-model="form.data.crawler_mode">
            <option value="light">light（httpx）</option>
            <option value="playwright">playwright（無頭瀏覽器）</option>
          </select>
        </div>

        <div class="checkbox-row">
          <input type="checkbox" id="is_active" v-model="form.data.is_active" />
          <label for="is_active">啟用追蹤</label>
        </div>

        <div class="form-row">
          <label>備註</label>
          <textarea v-model="form.data.notes" rows="2"></textarea>
        </div>

        <div class="modal-actions">
          <button class="btn" @click="form.visible = false">取消</button>
          <button class="btn btn-primary" @click="submit">
            {{ form.mode === 'create' ? '建立' : '儲存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.btn-sm + .btn-sm {
  margin-left: 4px;
}
</style>
