import { apiClient } from './client'
import type { ConsensusRow, ReductionRow } from '../types'

export const consensusApi = {
  latest: (params: { signal_only?: boolean; limit?: number } = {}) =>
    apiClient.get<ConsensusRow[]>('/consensus', { params }).then((r) => r.data),

  reduction: (params: { risk_only?: boolean; limit?: number } = {}) =>
    apiClient
      .get<ReductionRow[]>('/consensus/reduction', { params })
      .then((r) => r.data),

  byDate: (date: string) =>
    apiClient.get<ConsensusRow[]>(`/consensus/${date}`).then((r) => r.data),

  byStock: (stockId: string, days = 90) =>
    apiClient
      .get<ConsensusRow[]>(`/consensus/stock/${stockId}`, { params: { days } })
      .then((r) => r.data),
}
