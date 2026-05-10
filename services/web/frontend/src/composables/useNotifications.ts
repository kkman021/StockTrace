import { onBeforeUnmount, ref } from 'vue'
import { SIGNAL_TAG_LABELS } from '../types'

interface SignalEventPayload {
  stock_id: string
  stock_name?: string
  signal_tag: string
  summary?: string
  breadth_score?: number
  consecutive_days?: number
}

/**
 * Web Notification + SSE 訊號接收（規格 §13、§23.2）。
 *
 * 後端 /api/signals/stream 透過 Redis pub/sub 廣播新訊號（目前僅心跳，
 * 待 services/web/app/services/notification.py 串接 pub/sub 後完整生效）。
 */
export function useSignalNotifications() {
  const status = ref<'idle' | 'connected' | 'denied' | 'unsupported'>('idle')
  let eventSource: EventSource | null = null

  async function start(): Promise<void> {
    if (typeof window === 'undefined' || !('EventSource' in window)) {
      status.value = 'unsupported'
      return
    }

    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission()
      if (permission !== 'granted') {
        status.value = 'denied'
        // 仍訂閱 SSE，只是不顯示通知
      }
    }

    eventSource = new EventSource('/api/signals/stream')
    eventSource.onopen = () => {
      status.value = 'connected'
    }
    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as SignalEventPayload
        if (!payload.stock_id) return  // 心跳事件
        showNotification(payload)
      } catch {
        // 非 JSON 心跳，忽略
      }
    }
    eventSource.onerror = () => {
      // EventSource 會自動重連；這裡只重設狀態
      status.value = 'idle'
    }
  }

  function showNotification(payload: SignalEventPayload): void {
    if (typeof Notification === 'undefined' || Notification.permission !== 'granted') {
      return
    }
    const label = SIGNAL_TAG_LABELS[payload.signal_tag] ?? payload.signal_tag
    const title = `${label}：${payload.stock_name ?? payload.stock_id}`
    const body =
      payload.summary ??
      `廣度 ${payload.breadth_score != null ? `${(payload.breadth_score * 100).toFixed(0)}%` : '-'} ｜ 連續 ${payload.consecutive_days ?? '-'} 日`
    new Notification(title, { body, tag: payload.stock_id })
  }

  function stop(): void {
    eventSource?.close()
    eventSource = null
    status.value = 'idle'
  }

  onBeforeUnmount(stop)

  return { status, start, stop }
}
