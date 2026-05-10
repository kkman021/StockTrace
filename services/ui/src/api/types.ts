// API 回應型別（與 web 端 schemas 對齊；不齊全但涵蓋介面所需）

export interface ConsensusRow {
  date: string
  stock_id: string
  stock_name: string | null
  breadth_score: number | null
  depth_score: number | null
  consecutive_days: number | null
  signal_tag: string | null
  reduction_breadth: number | null
  reduction_consec: number | null
  risk_tag: string | null
  data_status: string
}

export interface SignalRow {
  id: number
  date: string
  stock_id: string
  stock_name: string | null
  signal_type: 'add' | 'reduce'
  signal_tag: string
  breadth_score: number | null
  depth_score: number | null
  consecutive_days: number | null
}

export interface EtfRow {
  etf_id: string
  etf_name: string
  issuer: string
  disclosure_url: string
  aum_url: string | null
  aum_source: 'inline' | 'separate'
  crawler_mode: 'light' | 'playwright'
  fallback_count: number
  is_active: boolean
  last_known_aum: number | null
  last_success_date: string | null
}

export interface CrawlStatusItem {
  etf_id: string
  etf_name: string
  crawler_mode: 'light' | 'playwright'
  fallback_count: number
  last_success_date: string | null
  today_log: {
    status: 'success' | 'failed'
    crawler_used: 'light' | 'playwright' | null
    records_count: number
    duration_ms: number | null
    error_message: string | null
  } | null
}

export interface CrawlStatusResponse {
  date: string
  total: number
  success_today: number
  items: CrawlStatusItem[]
}

export interface BacktestRun {
  id: number
  start_date: string
  end_date: string
  holding_days: number
  breadth_threshold: number
  depth_threshold: number
  consecutive_days: number
  target_stocks: string[] | null
  status: string
}

export interface BacktestSummaryRow {
  stock_id: string
  stock_name: string | null
  trigger_count: number
  win_rate: number
  avg_return: number
  max_return: number
  min_return: number
  avg_breadth: number
  avg_depth: number
}

export interface SystemConfigEntry {
  key: string
  value: string
  description: string | null
}
