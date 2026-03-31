<template>
  <div class="page">
    <div class="page-header">
      <h1>공정 대시보드 <span class="tag">공정연구원</span></h1>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="showDummy = true">더미 데이터 생성</button>
        <button class="btn btn-primary" @click="showNewLot = true">+ 새 LOT 등록</button>
      </div>
    </div>

    <!-- KPI 카드 -->
    <div class="grid grid-4" style="margin-bottom:20px" v-if="dashboard">
      <div class="kpi-card">
        <div class="kpi-value">{{ dashboard.total_lots }}</div>
        <div class="kpi-label">전체 LOT</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value" style="color:var(--ok)">{{ dashboard.yield_rate }}%</div>
        <div class="kpi-label">수율</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value" style="color:var(--warn)">{{ dashboard.in_progress_lots }}</div>
        <div class="kpi-label">진행 중 LOT</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value" style="color:var(--err)">{{ dashboard.defect_count }}</div>
        <div class="kpi-label">불량 LOT</div>
      </div>
    </div>

    <div class="grid grid-2">
      <!-- LOT 목록 -->
      <div class="panel" style="grid-column: span 2">
        <h2>LOT 현황 <span class="tag">{{ lots.length }}건</span></h2>
        <div class="filter-row">
          <button
            v-for="f in filters" :key="f.value"
            :class="['filter-btn', { active: activeFilter === f.value }]"
            @click="filterLots(f.value)"
          >{{ f.label }}</button>
        </div>
        <div v-if="store.loading" class="loading">로딩 중...</div>
        <table v-else class="lot-table">
          <thead>
            <tr>
              <th>LOT ID</th><th>상태</th><th>입고일</th><th>공정</th><th>액션</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lot in lots" :key="lot.lot_id">
              <td><strong>{{ lot.lot_id }}</strong></td>
              <td><span :class="statusBadge(lot.lot_status)">{{ lot.lot_status }}</span></td>
              <td>{{ lot.created_at ? lot.created_at.slice(0,10) : '-' }}</td>
              <td>{{ progressLabel(lot.lot_status) }}</td>
              <td>
                <button class="btn btn-secondary" style="padding:4px 10px;font-size:12px" @click="goDetail(lot.lot_id)">상세</button>
                <button class="btn btn-primary" style="padding:4px 10px;font-size:12px;margin-left:6px" @click="goRecommend(lot.lot_id)">AI 추천</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 새 LOT 모달 -->
    <div v-if="showNewLot" class="modal-overlay" @click.self="showNewLot = false">
      <div class="modal">
        <h3>새 LOT 등록</h3>
        <div class="form-group"><label>LOT ID</label><input v-model="newLot.lot_id" class="input" placeholder="예) LOT-051" /></div>
        <div class="grid grid-2">
          <div class="form-group"><label>Vendor ID</label><input v-model="newLot.vendor_id" class="input" placeholder="예) HC-001" /></div>
          <div class="form-group"><label>입고일</label><input type="date" v-model="newLot.incoming_date" class="input" /></div>
          <div class="form-group"><label>점도 (Pa·s)</label><input type="number" step="0.01" v-model="newLot.viscosity" class="input" /></div>
          <div class="form-group"><label>CTE (ppm/°C)</label><input type="number" step="0.1" v-model="newLot.cte" class="input" /></div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showNewLot = false">취소</button>
          <button class="btn btn-primary" @click="submitNewLot">등록</button>
        </div>
      </div>
    </div>

    <!-- 더미 데이터 생성 모달 -->
    <div v-if="showDummy" class="modal-overlay" @click.self="showDummy = false">
      <div class="modal">
        <h3>더미 데이터 생성</h3>
        <div class="form-group"><label>LOT 개수</label><input type="number" v-model="dummyCount" class="input" min="1" max="100" /></div>
        <div class="form-group"><label>목표 수율 (%)</label><input type="number" v-model="dummyYield" class="input" step="0.01" min="0" max="1" /></div>
        <p style="font-size:12px;color:var(--muted);margin-bottom:16px">step4 방식으로 stacking 10회 + reflow 9회 데이터를 생성합니다.</p>
        <div v-if="dummyResult" class="result-box">
          <p style="color:var(--ok)">✅ {{ dummyResult.created }}개 LOT 생성 완료</p>
          <p style="font-size:12px;color:var(--muted)">불량: {{ dummyResult.defect_lots?.join(', ') }}</p>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showDummy = false">닫기</button>
          <button class="btn btn-primary" @click="submitDummy" :disabled="store.loading">
            {{ store.loading ? '생성 중...' : '생성' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useHbmStore } from '../store/hbm.js'

const store = useHbmStore()
const router = useRouter()
const lots = ref([])
const dashboard = ref(null)
const showNewLot = ref(false)
const showDummy = ref(false)
const activeFilter = ref('all')
const dummyCount = ref(10)
const dummyYield = ref(0.98)
const dummyResult = ref(null)

const newLot = ref({ lot_id: '', vendor_id: '', incoming_date: '', viscosity: 3.8, cte: 19.0 })

const filters = [
  { value: 'all', label: '전체' },
  { value: 'INCOMING', label: '입고' },
  { value: 'PRE_ANALYSIS', label: '사전분석' },
  { value: 'DONE', label: '완료' },
]

onMounted(async () => {
  await store.fetchDashboard()
  dashboard.value = store.dashboard
  await store.fetchLots()
  lots.value = store.lots
})

async function filterLots(status) {
  activeFilter.value = status
  await store.fetchLots(status === 'all' ? null : status)
  lots.value = store.lots
}

function statusBadge(status) {
  if (status === 'DONE') return 'badge badge-ok'
  if (status === 'INJECTION') return 'badge badge-blue'
  if (status?.startsWith('STACKING')) return 'badge badge-warn'
  if (status?.startsWith('REFLOW')) return 'badge badge-warn'
  return 'badge badge-err'
}

function progressLabel(status) {
  if (status === 'DONE') return '완료'
  if (status === 'INJECTION') return 'MUF 주입'
  if (status?.startsWith('STACKING_')) return `적층 ${status.split('_')[1]}회차`
  if (status?.startsWith('REFLOW_')) return `리플로우 ${status.split('_')[1]}회차`
  return status
}

function goDetail(lotId) { router.push(`/lot/${lotId}`) }
function goRecommend(lotId) { router.push(`/recommend/${lotId}`) }

async function submitNewLot() {
  const lot = await store.createLot({ lot_id: newLot.value.lot_id, lot_status: 'INCOMING' })
  if (lot) {
    await store.createIncoming(newLot.value.lot_id, {
      lot_id: newLot.value.lot_id,
      vendor_id: newLot.value.vendor_id,
      viscosity: newLot.value.viscosity,
      cte: newLot.value.cte,
      incoming_date: newLot.value.incoming_date,
    })
    showNewLot.value = false
    await store.fetchLots()
    lots.value = store.lots
    await store.fetchDashboard()
    dashboard.value = store.dashboard
  }
}

async function submitDummy() {
  dummyResult.value = await store.generateDummy(dummyCount.value, dummyYield.value)
  await store.fetchLots()
  lots.value = store.lots
  await store.fetchDashboard()
  dashboard.value = store.dashboard
}
</script>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h1 { font-size: 22px; font-weight: 800; display: flex; align-items: center; gap: 10px; }
.header-actions { display: flex; gap: 10px; }
.filter-row { display: flex; gap: 8px; margin-bottom: 14px; }
.filter-btn { background: #0e1218; border: 1px solid var(--line); color: var(--muted); padding: 5px 14px; border-radius: 999px; cursor: pointer; font-size: 12px; }
.filter-btn.active { border-color: var(--brand); color: var(--brand); background: rgba(93,211,255,.08); }
.form-group { margin-bottom: 14px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 999; }
.modal { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 28px; width: 480px; }
.modal h3 { font-size: 17px; font-weight: 700; margin-bottom: 20px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.result-box { background: rgba(46,204,113,.08); border: 1px solid var(--ok); border-radius: 10px; padding: 12px; margin-bottom: 14px; }
</style>
