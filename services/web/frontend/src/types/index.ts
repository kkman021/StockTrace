// Shared TypeScript types matching backend Pydantic schemas.

export type AumSource = 'inline' | 'separate'
export type CrawlerMode = 'light' | 'playwright'
export type SignalType = 'add' | 'reduce'

export interface Etf {
  etf_id: string
  etf_name: string
  issuer: string
  disclosure_url: string
  aum_url: string | null
  aum_source: AumSource
  crawler_mode: CrawlerMode
  fallback_count: number
  is_active: boolean
  added_date: string
  last_success_date: string | null
  last_known_aum: number | null
  notes: string | null
}

export type EtfCreate = Omit<
  Etf,
  'fallback_count' | 'added_date' | 'last_success_date' | 'last_known_aum'
>

export interface EtfUpdate {
  etf_name?: string
  disclosure_url?: string
  aum_url?: string | null
  aum_source?: AumSource
  crawler_mode?: CrawlerMode
  is_active?: boolean
  notes?: string | null
}

export interface ConsensusRow {
  date: string
  stock_id: string
  stock_name: string | null
  breadth_score: string | null  // Decimal serialised as string
  depth_score: string | null
  accumulate_etf_count: number | null
  total_amount: number | null
  consecutive_days: number | null
  signal_tag: string | null
}

export interface ReductionRow {
  date: string
  stock_id: string
  stock_name: string | null
  reduction_breadth: string | null
  reduction_etf_count: number | null
  reduction_consec: number | null
  risk_tag: string | null
}

export interface ThresholdConfig {
  breadth_threshold: number
  depth_threshold: number
  consecutive_days: number
  sliding_window: number
  reduction_breadth_threshold: number
  reduction_consecutive_days: number
}

export type ThresholdConfigPatch = Partial<ThresholdConfig>

export interface SignalRow {
  id: number
  date: string
  stock_id: string
  stock_name: string | null
  signal_type: SignalType
  signal_tag: string
  breadth_score: string | null
  depth_score: string | null
  consecutive_days: number | null
  notified_at: string | null
  created_at: string
}

// 訊號標籤對顯示文字 / 顏色（與後端常數對應）
export const SIGNAL_TAG_LABELS: Record<string, string> = {
  high_consensus: '高度共識',
  wide_consensus: '廣泛共識',
  deep_position: '深度佈局',
  risk_alert: '風險警示',
  watch: '觀察中',
}

export const SIGNAL_TAG_COLORS: Record<string, string> = {
  high_consensus: '#d97706',  // amber
  wide_consensus: '#2563eb',  // blue
  deep_position: '#ca8a04',   // yellow
  risk_alert: '#dc2626',      // red
  watch: '#ea580c',           // orange
}
