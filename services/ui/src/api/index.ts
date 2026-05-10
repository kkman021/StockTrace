import client from './client'
import type {
  BacktestRun,
  BacktestSummaryRow,
  ConsensusRow,
  CrawlStatusResponse,
  EtfRow,
  SignalRow,
  SystemConfigEntry
} from './types'

// ---------- consensus ---------- //
export const fetchConsensus = (date: string, signalType?: 'add' | 'reduce') =>
  client
    .get<ConsensusRow[]>('/consensus', { params: { date, signal_type: signalType } })
    .then((r) => r.data)

// ---------- signals ---------- //
export const fetchSignals = (date?: string, signalType?: 'add' | 'reduce') =>
  client
    .get<SignalRow[]>('/signals', { params: { date, signal_type: signalType } })
    .then((r) => r.data)

// ---------- etf ---------- //
export const fetchEtfs = () => client.get<EtfRow[]>('/etf').then((r) => r.data)

export const upsertEtf = (etf: Partial<EtfRow>) =>
  client.post<EtfRow>('/etf', etf).then((r) => r.data)

export const resetCrawler = (etfId: string) =>
  client.post(`/etf/${etfId}/reset-crawler`).then((r) => r.data)

// ---------- config ---------- //
export const fetchConfig = () => client.get<SystemConfigEntry[]>('/config').then((r) => r.data)

export const updateConfig = (key: string, value: string) =>
  client.put(`/config/${key}`, { value }).then((r) => r.data)

// ---------- admin ---------- //
export const fetchCrawlStatus = (date?: string) =>
  client
    .get<CrawlStatusResponse>('/admin/crawl-status', { params: { date } })
    .then((r) => r.data)

export const triggerCrawl = (date?: string, retryMissingOnly = false) =>
  client
    .post('/admin/crawl', null, { params: { date, retry_missing_only: retryMissingOnly } })
    .then((r) => r.data)

export const triggerSingleCrawl = (etfId: string, date?: string) =>
  client.post(`/admin/crawl/${etfId}`, null, { params: { date } }).then((r) => r.data)

export const triggerAnalyze = (date: string) =>
  client.post(`/admin/analyze/${date}`).then((r) => r.data)

export const triggerDetect = (date: string) =>
  client.post(`/admin/detect-signals/${date}`).then((r) => r.data)

// ---------- backtest ---------- //
export const createBacktest = (payload: {
  start_date: string
  end_date: string
  holding_days: number
  breadth_threshold: number
  depth_threshold: number
  consecutive_days: number
  target_stocks?: string[]
}) => client.post<BacktestRun>('/backtest', payload).then((r) => r.data)

export const fetchBacktests = () => client.get<BacktestRun[]>('/backtest').then((r) => r.data)

export const fetchBacktestSummary = (id: number) =>
  client.get<BacktestSummaryRow[]>(`/backtest/${id}/summary`).then((r) => r.data)

// ---------- search ---------- //
export const searchSignals = (params: {
  q?: string
  signal_type?: string
  signal_tag?: string
  date_from?: string
  date_to?: string
}) => client.get('/admin/search-signals', { params }).then((r) => r.data)
