import { apiClient } from './client'
import type { ThresholdConfig, ThresholdConfigPatch } from '../types'

export const configApi = {
  get: () => apiClient.get<ThresholdConfig>('/config').then((r) => r.data),

  patch: (payload: ThresholdConfigPatch) =>
    apiClient.patch<ThresholdConfig>('/config', payload).then((r) => r.data),
}
