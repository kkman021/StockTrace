<script setup lang="ts">
defineProps<{ message: string; hint?: string }>()
</script>

<template>
  <div class="text-center py-12 text-slate-500">
    <div class="text-base">{{ message }}</div>
    <div v-if="hint" class="text-sm text-slate-400 mt-1">{{ hint }}</div>
  </div>
</template>
