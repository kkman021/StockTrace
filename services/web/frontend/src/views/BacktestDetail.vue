<script setup lang="ts">
import { defineProps } from 'vue'

defineProps<{ runId: string }>()

// TODO: GET /api/backtest/{runId}/summary 顯示統計表
// TODO: GET /api/backtest/{runId}/chart/{stock_id} 渲染走勢圖（細線+平均粗線）
</script>

<template>
  <h1>回測結果</h1>
  <p>TODO: 統計摘要表 + 個別走勢圖（X：訊號前 10 日 + 持有天數，Y：累計報酬率）</p>
</template>
