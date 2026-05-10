<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  hint?: string
  tone?: 'default' | 'positive' | 'negative'
}>()
</script>

<template>
  <div class="card">
    <div class="text-xs text-slate-500">{{ label }}</div>
    <div
      class="text-2xl font-semibold mt-1"
      :class="{
        'text-emerald-600': tone === 'positive',
        'text-rose-600': tone === 'negative',
        'text-slate-800': tone === 'default' || !tone
      }"
    >
      {{ value }}
    </div>
    <div v-if="hint" class="text-xs text-slate-400 mt-1">{{ hint }}</div>
  </div>
</template>
