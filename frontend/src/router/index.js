// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import EngineerDashboard from '../views/EngineerDashboard.vue'
import QualityDashboard from '../views/QualityDashboard.vue'
import LotDetail from '../views/LotDetail.vue'
import ProcessInput from '../views/ProcessInput.vue'
import AiRecommend from '../views/AiRecommend.vue'
import ChatBot from '../views/ChatBot.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/engineer', component: EngineerDashboard, meta: { role: 'engineer' } },
  { path: '/quality', component: QualityDashboard, meta: { role: 'quality' } },
  { path: '/lot/:id', component: LotDetail },
  { path: '/process/:id', component: ProcessInput },
  { path: '/recommend/:id', component: AiRecommend },
  { path: '/chat', component: ChatBot },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
