import { apiClient } from './client'
import type { SignalRow, SignalType } from '../types'

export const signalsApi = {
  list: (params: { date?: string; signal_type?: SignalType; limit?: number } = {}) =>
    apiClient.get<SignalRow[]>('/signals', { params }).then((r) => r.data),
}
