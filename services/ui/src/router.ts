import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/consensus' },
  { path: '/consensus', component: () => import('./pages/Consensus.vue'), meta: { title: '共識榜' } },
  { path: '/signals', component: () => import('./pages/Signals.vue'), meta: { title: '訊號清單' } },
  { path: '/backtest', component: () => import('./pages/Backtest.vue'), meta: { title: '回測沙盒' } },
  { path: '/admin', component: () => import('./pages/Admin.vue'), meta: { title: '管理' } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.afterEach((to) => {
  document.title = `${to.meta.title || ''} · StockTrace`
})

export default router
