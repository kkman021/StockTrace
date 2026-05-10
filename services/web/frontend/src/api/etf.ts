import { apiClient } from './client'
import type { Etf, EtfCreate, EtfUpdate } from '../types'

export const etfApi = {
  list: (activeOnly = false) =>
    apiClient
      .get<Etf[]>('/etf', { params: { active_only: activeOnly } })
      .then((r) => r.data),

  get: (etfId: string) => apiClient.get<Etf>(`/etf/${etfId}`).then((r) => r.data),

  create: (payload: EtfCreate) =>
    apiClient.post<Etf>('/etf', payload).then((r) => r.data),

  update: (etfId: string, payload: EtfUpdate) =>
    apiClient.patch<Etf>(`/etf/${etfId}`, payload).then((r) => r.data),

  resetCrawler: (etfId: string) =>
    apiClient.post<void>(`/etf/${etfId}/reset-crawler`).then(() => undefined),

  overrideAum: (etfId: string, aum: number) =>
    apiClient.post<void>(`/etf/${etfId}/aum`, { aum }).then(() => undefined),
}
