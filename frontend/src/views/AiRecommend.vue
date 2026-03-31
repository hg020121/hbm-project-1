<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>공정 시작 전 예측 <span class="tag">Decision Gate + AI</span></h1>
        <p style="color:var(--muted);font-size:13px;margin-top:4px">LOT {{ lotId }}</p>
      </div>
      <button class="btn btn-secondary" @click="$router.back()">← 뒤로</button>
    </div>

    <div v-if="loading" class="loading" style="padding:80px">AI 분석 중... 잠시 기다려주세요 🤖</div>

    <div v-else-if="history" class="decision-layout">
      <!-- 좌측: LOT & 소재 요약 -->
      <div class="panel lot-summary">
        <h2>⚙️ LOT & 소재 요약</h2>
        <div class="info-row"><span class="info-label">LOT</span><span class="info-value">{{ history.lot.lot_id }}</span></div>
        <div class="info-row" v-if="history.incoming">
          <span class="info-label">Vendor</span><span class="info-value">{{ history.incoming.vendor_id }}</span>
        </div>
        <div class="info-row" v-if="history.incoming">
          <span class="info-label">Viscosity</span><span class="info-value">{{ history.incoming.viscosity }} Pa·s</span>
        </div>
        <div class="info-row" v-if="history.incoming">
          <span class="info-label">CTE</span><span class="info-value">{{ history.incoming.cte }} ppm/°C</span>
        </div>
        <div class="info-row">
          <span class="info-label">공정 상태</span>
          <span :class="statusBadge(history.lot.lot_status)">{{ history.lot.lot_status }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Incoming QC</span>
          <span class="badge badge-ok">✅ PASS</span>
        </div>
      </div>

      <!-- 중앙: KPI + AI 추천 -->
      <div class="center-col">
        <!-- KPI 게이지 -->
        <div class="panel kpi-panel">
          <h2>KPI</h2>
          <div class="kpi-row">
            <div class="gauge-card" :class="voidRiskClass">
              <div class="gauge-value">{{ voidRisk }}%</div>
              <div class="gauge-label">Void Risk ↑</div>
              <div class="gauge-level">{{ voidRiskLabel }}</div>
            </div>
            <div class="gauge-card warn">
              <div class="gauge-value">{{ stackCount * 10 }}%</div>
              <div class="gauge-label">공정 진행률</div>
              <div class="gauge-level">MEDIUM</div>
            </div>
            <div class="gauge-card" :class="riskLevelClass">
              <div class="gauge-icon">⚠️</div>
              <div class="gauge-label">Risk Level</div>
              <div class="gauge-level">{{ recommend?.reason ? riskLevel : 'ANALYZING' }}</div>
            </div>
          </div>
        </div>

        <!-- AI 추천 결과 -->
        <div class="panel ai-panel" v-if="recommend">
          <h2>🧠 AI Recommendation</h2>
          <div class="recommend-items">
            <div class="recommend-item">
              <span class="rec-icon">🌡️</span>
              <span>Reflow Temp <strong>{{ recommend.recommend_temp }}°C</strong></span>
            </div>
            <div class="recommend-item">
              <span class="rec-icon">⚡</span>
              <span>Stack Pressure <strong>{{ recommend.recommend_pressure }} MPa</strong></span>
            </div>
          </div>
        </div>
        <div class="panel ai-panel" v-else>
          <h2>🧠 AI Recommendation</h2>
          <button class="btn btn-primary" @click="getRecommend" :disabled="recommending">
            {{ recommending ? 'AI 분석 중...' : '🤖 AI 추천 받기' }}
          </button>
        </div>

        <!-- 액션 버튼 -->
        <div class="action-row">
          <button class="btn btn-danger" @click="proceed('go')">공정 진행</button>
          <button class="btn btn-warn" @click="proceed('modify')">조건 수정 후 진행</button>
          <button class="btn btn-secondary" @click="proceed('hold')">⚠️ HOLD</button>
        </div>
      </div>

      <!-- 우측: RAG Explain Panel -->
      <div class="panel explain-panel">
        <div class="explain-header">
          <h2>RAG Explain Panel</h2>
        </div>
        <div class="explain-tabs">
          <button :class="['etab', { active: activeTab === 'why' }]" @click="activeTab = 'why'">왜 위험한가?</button>
          <button :class="['etab', { active: activeTab === 'similar' }]" @click="activeTab = 'similar'">유사 LOT</button>
          <button :class="['etab', { active: activeTab === 'basis' }]" @click="activeTab = 'basis'">권장 조치 근거</button>
        </div>

        <div v-if="activeTab === 'why'" class="explain-content">
          <div class="explain-warn" v-if="recommend">
            ⚠️ {{ recommend.reason || '분석 중입니다.' }}
          </div>
          <div v-else class="explain-empty">AI 추천을 먼저 실행하세요.</div>
        </div>

        <div v-if="activeTab === 'similar'" class="explain-content">
          <div class="void-chart-label">Void Trend</div>
          <div class="void-bars">
            <div v-for="(s, i) in history.stackings" :key="i" class="void-bar-wrap">
              <div class="void-bar" :style="{ height: (s.void_area_pct * 100) + '%', background: voidColor(s.void_area_pct) }"></div>
              <span class="void-seq">{{ s.stack_seq }}</span>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'basis'" class="explain-content">
          <div class="explain-item" v-for="stk in history.stackings.slice(-3)" :key="stk.stack_id">
            <span class="explain-seq">seq{{ stk.stack_seq }}</span>
            <span>압력 {{ stk.pressure }} MPa</span>
            <span>void {{ (stk.void_area_pct * 100).toFixed(1) }}%</span>
          </div>
          <div v-if="!history.stackings.length" class="explain-empty">공정 이력 없음</div>
        </div>

        <!-- 이미지 업로드 분석 -->
        <div class="image-upload-section">
          <div class="explain-divider"></div>
          <h3 style="font-size:13px;margin-bottom:8px">📷 SAM 이미지 분석</h3>
          <input type="file" accept="image/*" @change="onImageUpload" class="file-input" ref="imgInput" />
          <button class="btn btn-secondary" style="font-size:12px;padding:6px 12px;width:100%" @click="$refs.imgInput.click()">이미지 업로드</button>
          <div v-if="imageResult" class="image-result">
            <p><strong>void 추정:</strong> {{ (imageResult.void_estimate * 100).toFixed(1) }}%</p>
            <p style="font-size:12px;color:var(--muted);margin-top:4px">{{ imageResult.analysis }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useHbmStore } from '../store/hbm.js'

const store = useHbmStore()
const route = useRoute()
const router = useRouter()
const lotId = route.params.id
const history = ref(null)
const recommend = ref(null)
const loading = ref(true)
const recommending = ref(false)
const activeTab = ref('why')
const imageResult = ref(null)
const imgInput = ref(null)

onMounted(async () => {
  history.value = await store.fetchLotHistory(lotId)
  loading.value = false
})

const stackCount = computed(() => history.value?.stackings?.length || 0)
const lastVoid = computed(() => {
  const stackings = history.value?.stackings || []
  return stackings.length ? stackings[stackings.length - 1].void_area_pct : 0
})
const voidRisk = computed(() => Math.round(lastVoid.value * 100))
const voidRiskLabel = computed(() => voidRisk.value > 70 ? 'HIGH' : voidRisk.value > 40 ? 'MEDIUM' : 'LOW')
const voidRiskClass = computed(() => voidRisk.value > 70 ? 'danger' : voidRisk.value > 40 ? 'warn' : 'ok')
const riskLevel = computed(() => voidRisk.value > 70 ? 'HIGH' : 'MEDIUM')
const riskLevelClass = computed(() => voidRisk.value > 70 ? 'danger' : 'warn')

function statusBadge(s) {
  if (s === 'DONE') return 'badge badge-ok'
  if (s?.startsWith('STACKING')) return 'badge badge-warn'
  return 'badge badge-blue'
}

function voidColor(v) {
  if (v > 0.7) return '#e74c3c'
  if (v > 0.4) return '#f39c12'
  return '#2ecc71'
}

async function getRecommend() {
  recommending.value = true
  recommend.value = await store.getAiRecommend(lotId)
  recommending.value = false
}

function proceed(action) {
  if (action === 'go') router.push(`/process/${lotId}`)
  else if (action === 'hold') alert(`LOT ${lotId}를 HOLD 상태로 변경합니다.`)
  else router.push(`/process/${lotId}`)
}

async function onImageUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  imageResult.value = await store.analyzeImage(file, lotId)
}
</script>

<style scoped>
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; }
.page-header h1 { font-size: 22px; font-weight: 800; }
.decision-layout { display: grid; grid-template-columns: 240px 1fr 260px; gap: 16px; align-items: start; }
.lot-summary .info-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--line); font-size: 13px; }
.info-label { color: var(--muted); }
.info-value { font-weight: 600; }
.center-col { display: flex; flex-direction: column; gap: 14px; }
.kpi-panel .kpi-row { display: flex; gap: 12px; }
.gauge-card { flex: 1; background: #0e1218; border: 1px solid var(--line); border-radius: 12px; padding: 16px; text-align: center; }
.gauge-card.danger { border-color: var(--err); }
.gauge-card.warn { border-color: var(--warn); }
.gauge-card.ok { border-color: var(--ok); }
.gauge-value { font-size: 28px; font-weight: 800; color: var(--brand); }
.gauge-card.danger .gauge-value { color: var(--err); }
.gauge-card.warn .gauge-value { color: var(--warn); }
.gauge-card.ok .gauge-value { color: var(--ok); }
.gauge-label { font-size: 11px; color: var(--muted); margin-top: 4px; }
.gauge-level { font-size: 13px; font-weight: 700; margin-top: 6px; }
.gauge-card.danger .gauge-level { color: var(--err); }
.gauge-card.warn .gauge-level { color: var(--warn); }
.gauge-icon { font-size: 24px; }
.ai-panel .recommend-items { display: flex; flex-direction: column; gap: 10px; }
.recommend-item { display: flex; align-items: center; gap: 10px; font-size: 14px; padding: 10px; background: rgba(93,211,255,.05); border-radius: 8px; border: 1px solid rgba(93,211,255,.1); }
.rec-icon { font-size: 18px; }
.action-row { display: flex; gap: 10px; }
.action-row .btn { flex: 1; padding: 12px; }
.btn-warn { background: linear-gradient(180deg,#f39c12,#e67e22); color: white; border: none; }
.explain-panel { display: flex; flex-direction: column; gap: 12px; }
.explain-tabs { display: flex; gap: 4px; }
.etab { background: none; border: 1px solid var(--line); color: var(--muted); padding: 4px 10px; border-radius: 8px; cursor: pointer; font-size: 11px; }
.etab.active { border-color: var(--brand); color: var(--brand); background: rgba(93,211,255,.08); }
.explain-content { font-size: 13px; min-height: 80px; }
.explain-warn { background: rgba(231,76,60,.1); border: 1px solid var(--err); border-radius: 8px; padding: 10px; color: var(--err); font-size: 12px; line-height: 1.6; }
.explain-empty { color: var(--muted); padding: 20px 0; text-align: center; }
.explain-item { display: flex; justify-content: space-between; font-size: 12px; padding: 6px 0; border-bottom: 1px solid var(--line); }
.explain-seq { color: var(--brand); font-weight: 700; }
.void-chart-label { font-size: 11px; color: var(--muted); margin-bottom: 8px; }
.void-bars { display: flex; align-items: flex-end; gap: 4px; height: 60px; }
.void-bar-wrap { display: flex; flex-direction: column; align-items: center; gap: 2px; flex: 1; height: 100%; justify-content: flex-end; }
.void-bar { width: 100%; border-radius: 3px 3px 0 0; min-height: 2px; }
.void-seq { font-size: 9px; color: var(--muted); }
.explain-divider { border: 0; border-top: 1px dashed var(--line); margin: 8px 0; }
.file-input { display: none; }
.image-result { margin-top: 8px; background: rgba(93,211,255,.05); border: 1px solid var(--line); border-radius: 8px; padding: 10px; font-size: 12px; }
</style>
