import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: () => import('../views/Dashboard.vue') },
    { path: '/reduction', name: 'reduction', component: () => import('../views/Reduction.vue') },
    { path: '/etf', name: 'etf', component: () => import('../views/EtfList.vue') },
    { path: '/config', name: 'config', component: () => import('../views/Config.vue') },
    { path: '/backtest', name: 'backtest', component: () => import('../views/Backtest.vue') },
    {
      path: '/backtest/:runId',
      name: 'backtest-detail',
      component: () => import('../views/BacktestDetail.vue'),
      props: true,
    },
  ],
})

export default router
