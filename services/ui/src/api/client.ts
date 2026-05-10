import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 60000
})

client.interceptors.response.use(
  (r) => r,
  (e) => {
    console.error('[api]', e?.response?.status, e?.config?.url, e?.message)
    return Promise.reject(e)
  }
)

export default client
