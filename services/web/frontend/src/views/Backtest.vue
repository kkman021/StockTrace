<script setup lang="ts">
// 回測頁面骨架；實作待 Milestone 4。
// TODO: 表單建立回測 (POST /api/backtest)
// TODO: 列表歷史回測 (GET /api/backtest)
</script>

<template>
  <div>
    <h1>回測模組</h1>
    <div class="banner banner-info">
      回測功能將於 Milestone 4 實作（規格 §12）。建議系統運行至少 3 個月後再使用。
    </div>
    <div class="card">
      <p class="muted">
        將提供：時間範圍、廣度 / 深度門檻、連續門檻、持有天數、目標標的等獨立沙盒設定，
        並產出統計摘要表與個別走勢圖（細線 + 平均線）。
      </p>
    </div>
  </div>
</template>
