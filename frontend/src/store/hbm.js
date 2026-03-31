// frontend/src/store/hbm.js
import { defineStore } from 'pinia'
import axios from 'axios'

const API = '/api'

export const useHbmStore = defineStore('hbm', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('hbm_user') || 'null'),
    lots: [],
    currentLot: null,
    dashboard: null,
    engineers: [],
    loading: false,
    error: null,
  }),

  actions: {
    // ============================
    // 인증
    // ============================
    login(employeeId) {
      const user = { employeeId, role: 'engineer' }
      this.user = user
      localStorage.setItem('hbm_user', JSON.stringify(user))
    },
    setRole(role) {
      if (!this.user) return
      this.user = { ...this.user, role }
      localStorage.setItem('hbm_user', JSON.stringify(this.user))
    },
    logout() {
      this.user = null
      localStorage.removeItem('hbm_user')
    },

    // ============================
    // 대시보드
    // ============================
    async fetchDashboard() {
      try {
        const { data } = await axios.get(`${API}/dashboard`)
        this.dashboard = data
      } catch (e) { this.error = e.message }
    },

    // ============================
    // LOT
    // ============================
    async fetchLots(status = null) {
      this.loading = true
      try {
        const params = status ? { status } : {}
        const { data } = await axios.get(`${API}/lots`, { params })
        this.lots = data
      } catch (e) { this.error = e.message }
      finally { this.loading = false }
    },

    async fetchLot(lotId) {
      this.loading = true
      try {
        const { data } = await axios.get(`${API}/lots/${lotId}`)
        this.currentLot = data
        return data
      } catch (e) { this.error = e.message }
      finally { this.loading = false }
    },

    async fetchLotHistory(lotId) {
      try {
        const { data } = await axios.get(`${API}/lots/${lotId}/history`)
        return data
      } catch (e) { this.error = e.message; return null }
    },

    async createLot(lotData) {
      try {
        const { data } = await axios.post(`${API}/lots`, lotData)
        this.lots.push(data)
        return data
      } catch (e) { this.error = e.message; return null }
    },

    async updateLotStatus(lotId, status) {
      try {
        const { data } = await axios.put(`${API}/lots/${lotId}/status`, { lot_status: status })
        const idx = this.lots.findIndex(l => l.lot_id === lotId)
        if (idx >= 0) this.lots[idx] = data
        return data
      } catch (e) { this.error = e.message; return null }
    },

    // ============================
    // 공정 데이터 등록
    // ============================
    async createIncoming(lotId, body) {
      try {
        const { data } = await axios.post(`${API}/lots/${lotId}/incoming`, body)
        return data
      } catch (e) { this.error = e.message; return null }
    },

    async createPreAnalysis(lotId, body) {
      try {
        const { data } = await axios.post(`${API}/lots/${lotId}/pre-analysis`, body)
        return data
      } catch (e) { this.error = e.message; return null }
    },

    async createStacking(lotId, body) {
      try {
        const { data } = await axios.post(`${API}/lots/${lotId}/stacking`, body)
        return data
      } catch (e) { this.error = e.message; return null }
    },

    async createReflow(lotId, body) {
      try {
        const { data } = await axios.post(`${API}/lots/${lotId}/reflow`, body)
        return data
      } catch (e) { this.error = e.message; return null }
    },

    async createInjection(lotId, body) {
      try {
        const { data } = await axios.post(`${API}/lots/${lotId}/injection`, body)
        return data
      } catch (e) { this.error = e.message; return null }
    },

    async createResult(lotId, body) {
      try {
        const { data } = await axios.post(`${API}/lots/${lotId}/result`, body)
        return data
      } catch (e) { this.error = e.message; return null }
    },

    // ============================
    // AI 추천
    // ============================
    async getAiRecommend(lotId) {
      this.loading = true
      try {
        const { data } = await axios.post(`${API}/lots/${lotId}/recommend`)
        return data
      } catch (e) { this.error = e.message; return null }
      finally { this.loading = false }
    },

    // ============================
    // 챗봇
    // ============================
    async sendChat(message, role, lotId = null) {
      try {
        const { data } = await axios.post(`${API}/chat`, {
          message, role, lot_id: lotId
        })
        return data
      } catch (e) { this.error = e.message; return null }
    },

    // ============================
    // 이미지 분석
    // ============================
    async analyzeImage(file, lotId = null) {
      try {
        const form = new FormData()
        form.append('file', file)
        const params = lotId ? { lot_id: lotId } : {}
        const { data } = await axios.post(`${API}/analyze-image`, form, { params })
        return data
      } catch (e) { this.error = e.message; return null }
    },

    // ============================
    // PDF RAG
    // ============================
    async uploadPdf(file) {
      try {
        const form = new FormData()
        form.append('file', file)
        const { data } = await axios.post(`${API}/upload-pdf`, form)
        return data
      } catch (e) { this.error = e.message; return null }
    },

    async ragQuery(question, topK = 3) {
      try {
        const { data } = await axios.post(`${API}/rag-query`, { question, top_k: topK })
        return data
      } catch (e) { this.error = e.message; return null }
    },

    // ============================
    // 더미 데이터 생성
    // ============================
    async generateDummy(count = 10, yieldRate = 0.98) {
      try {
        const { data } = await axios.post(`${API}/generate-dummy`, {
          count, yield_rate: yieldRate
        })
        return data
      } catch (e) { this.error = e.message; return null }
    },

    // ============================
    // 엔지니어
    // ============================
    async fetchEngineers() {
      try {
        const { data } = await axios.get(`${API}/engineers`)
        this.engineers = data
      } catch (e) { this.error = e.message }
    },
  }
})
