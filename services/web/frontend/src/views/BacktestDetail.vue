<script setup lang="ts">
defineProps<{ runId: string }>()
// TODO: GET /api/backtest/{runId}/summary 顯示統計表
// TODO: GET /api/backtest/{runId}/chart/{stock_id} 渲染走勢圖
</script>

<template>
  <div>
    <h1>回測結果 #{{ runId }}</h1>
    <div class="banner banner-info">
      Milestone 4 將實作此頁：統計摘要表 + 個別走勢圖
      （X：訊號前 10 日 + 持有天數，Y：累計報酬率）。
    </div>
  </div>
</template>
