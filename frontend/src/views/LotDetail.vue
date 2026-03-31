<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>LOT 상세 <span class="tag">{{ lotId }}</span></h1>
        <p style="color:var(--muted);font-size:13px;margin-top:4px" v-if="history">상태: {{ history.lot.lot_status }}</p>
      </div>
      <div style="display:flex;gap:10px">
        <button class="btn btn-primary" @click="$router.push(`/recommend/${lotId}`)">🤖 AI 추천</button>
        <button class="btn btn-secondary" @click="$router.back()">← 뒤로</button>
      </div>
    </div>

    <div v-if="!history" class="loading">로딩 중...</div>
    <div v-else class="grid grid-2">
      <!-- 소재 정보 -->
      <div class="panel">
        <h2>📦 입고 & 사전분석</h2>
        <table class="info-table" v-if="history.incoming">
          <tr><td class="info-label">Vendor</td><td>{{ history.incoming.vendor_id }}</td></tr>
          <tr><td class="info-label">Viscosity</td><td>{{ history.incoming.viscosity }} Pa·s</td></tr>
          <tr><td class="info-label">CTE</td><td>{{ history.incoming.cte }} ppm/°C</td></tr>
          <tr><td class="info-label">입고일</td><td>{{ history.incoming.incoming_date }}</td></tr>
        </table>
        <div v-if="history.pre_analysis" style="margin-top:14px;padding-top:14px;border-top:1px solid var(--line)">
          <div style="font-size:12px;color:var(--muted);margin-bottom:8px">사전분석 결과</div>
          <table class="info-table">
            <tr><td class="info-label">측정 점도</td><td>{{ history.pre_analysis.measured_viscosity }} Pa·s</td></tr>
            <tr><td class="info-label">측정 CTE</td><td>{{ history.pre_analysis.measured_cte }} ppm/°C</td></tr>
          </table>
        </div>
      </div>

      <!-- 최종 결과 -->
      <div class="panel">
        <h2>📊 최종 결과</h2>
        <div v-if="history.result">
          <div class="result-big">
            <span :class="resultBadge(history.result.final_result)">{{ history.result.final_result }}</span>
          </div>
          <table class="info-table" style="margin-top:14px">
            <tr><td class="info-label">최종 Void</td>
              <td><span :style="{ color: voidColor(history.result.void_area_pct) }">{{ (history.result.void_area_pct * 100).toFixed(1) }}%</span></td>
            </tr>
            <tr><td class="info-label">분석일</td><td>{{ history.result.analysis_date }}</td></tr>
          </table>
        </div>
        <div v-else style="color:var(--muted);font-size:13px;padding:20px 0;text-align:center">결과 분석 대기 중</div>
      </div>

      <!-- Stacking 이력 -->
      <div class="panel" style="grid-column:span 2">
        <h2>🔧 Stacking 공정 이력 <span class="tag">{{ history.stackings.length }}회</span></h2>
        <div class="void-trend">
          <div class="void-trend-bars">
            <div v-for="s in history.stackings" :key="s.stack_id" class="trend-bar-wrap">
              <div class="trend-bar" :style="{
                height: ((s.void_area_pct || 0) * 100) + 'px',
                background: voidColor(s.void_area_pct || 0)
              }"></div>
              <span class="trend-label">{{ s.stack_seq }}</span>
            </div>
          </div>
          <div class="trend-ylabel">Void (%)</div>
        </div>
        <table class="lot-table" style="margin-top:14px">
          <thead>
            <tr><th>seq</th><th>압력 (MPa)</th><th>Void (%)</th><th>날짜</th><th>추천ID</th></tr>
          </thead>
          <tbody>
            <tr v-for="s in history.stackings" :key="s.stack_id">
              <td>{{ s.stack_seq }}</td>
              <td>{{ s.pressure }}</td>
              <td :style="{ color: voidColor(s.void_area_pct || 0) }">{{ ((s.void_area_pct || 0) * 100).toFixed(1) }}%</td>
              <td>{{ s.stack_date?.slice(0, 10) }}</td>
              <td style="font-size:11px;color:var(--muted)">{{ s.recommend_id }}</td>
            </tr>
          </tbody>
        </table>

        <!-- 층별 VOID 히트맵 -->
        <div v-if="layerVoids.length" class="heatmap-wrap">
          <div class="heatmap-header">
            <div class="heatmap-title">VOID PATTERN — 층별 히트맵</div>
            <span class="heatmap-lot-badge">{{ lotId }}</span>
          </div>
          <div class="heatmap-grid">
            <div
              v-for="(lv, li) in [...layerVoids].reverse()"
              :key="li"
              class="heatmap-row"
            >
              <span class="layer-label">L{{ layerVoids.length - li }}</span>
              <div
                v-for="(cell, ci) in getLayerCells(lv, li)"
                :key="ci"
                class="heatmap-cell"
                :style="{ background: cellColor(cell) }"
                :title="`L${layerVoids.length - li} | 실측 ${(lv * 100).toFixed(1)}%`"
              ></div>
            </div>
          </div>
          <div class="heatmap-legend">
            <span class="legend-item"><span class="legend-dot" style="background:#2ecc71"></span> 낮음</span>
            <span class="legend-item"><span class="legend-dot" style="background:#f39c12"></span> 중간</span>
            <span class="legend-item"><span class="legend-dot" style="background:#e74c3c"></span> 높음</span>
            <span class="legend-note">* LOT 내 상대값 기준</span>
          </div>
          <div class="heatmap-stats">
            <div class="heatmap-stat">
              <div class="stat-value" style="color:var(--ok)">{{ (Math.min(...layerVoids) * 100).toFixed(1) }}%</div>
              <div class="stat-label">최소 VOID</div>
            </div>
            <div class="heatmap-stat">
              <div class="stat-value" style="color:var(--warn)">{{ avgVoid }}%</div>
              <div class="stat-label">평균 VOID</div>
            </div>
            <div class="heatmap-stat">
              <div class="stat-value" style="color:var(--err)">{{ (Math.max(...layerVoids) * 100).toFixed(1) }}%</div>
              <div class="stat-label">최대 VOID</div>
            </div>
            <div class="heatmap-stat">
              <div class="stat-value" :style="{ color: specExceeded > 0 ? 'var(--err)' : 'var(--ok)' }">{{ specExceeded }}층</div>
              <div class="stat-label">SPEC 초과</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Reflow 이력 -->
      <div class="panel">
        <h2>🌡️ Reflow 이력 <span class="tag">{{ history.reflows.length }}회</span></h2>
        <table class="lot-table">
          <thead><tr><th>seq</th><th>온도 (°C)</th><th>날짜</th></tr></thead>
          <tbody>
            <tr v-for="r in history.reflows" :key="r.reflow_id">
              <td>{{ r.reflow_seq }}</td>
              <td>{{ r.temperature }}</td>
              <td>{{ r.reflow_date?.slice(0, 10) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- AI 추천 이력 -->
      <div class="panel">
        <h2>🤖 AI 추천 이력 <span class="tag">{{ history.ai_recommends.length }}건</span></h2>
        <table class="lot-table">
          <thead><tr><th>추천ID</th><th>압력 (MPa)</th><th>온도 (°C)</th><th>시간</th></tr></thead>
          <tbody>
            <tr v-for="r in history.ai_recommends" :key="r.recommend_id">
              <td style="font-size:11px">{{ r.recommend_id }}</td>
              <td>{{ r.recommend_pressure }}</td>
              <td>{{ r.recommend_temp }}</td>
              <td style="font-size:11px;color:var(--muted)">{{ r.recommended_at?.slice(0, 16) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useHbmStore } from '../store/hbm.js'

const store = useHbmStore()
const route = useRoute()
const lotId = route.params.id
const history = ref(null)

onMounted(async () => {
  history.value = await store.fetchLotHistory(lotId)
})

function voidColor(v) {
  if (v > 0.05) return '#e74c3c'
  if (v > 0.02) return '#f39c12'
  return '#2ecc71'
}

function cellColor(v) {
  if (v > 0.05) return '#e74c3c'
  if (v > 0.02) return '#f39c12'
  return '#2ecc71'
}

function resultBadge(r) {
  if (r === '사용') return 'badge badge-ok'
  if (r === '재활용') return 'badge badge-warn'
  return 'badge badge-err'
}

// LOT 내 min~max 범위를 0.01~0.09로 정규화 (절댓값 무관하게 색상 분포 생성)
const voidRange = computed(() => {
  const voids = layerVoids.value
  if (!voids.length) return { min: 0, max: 0.1 }
  const min = Math.min(...voids)
  const max = Math.max(...voids)
  return { min, max: max === min ? min + 0.01 : max }
})

function normalizeVoid(v) {
  const { min, max } = voidRange.value
  return 0.01 + ((v - min) / (max - min)) * 0.08
}

function getLayerCells(layerVoid, layerIdx) {
  const dv = normalizeVoid(layerVoid)
  return Array.from({ length: 12 }, (_, i) => {
    const noise = Math.sin(i * 3.7 + layerIdx * 5.1) * dv * 0.5
    return Math.max(0, Math.min(0.12, dv + noise))
  })
}

const layerVoids = computed(() => {
  if (!history.value?.stackings?.length) return []
  return [...history.value.stackings]
    .sort((a, b) => a.stack_seq - b.stack_seq)
    .map(s => s.void_area_pct || 0)
})

const avgVoid = computed(() => {
  if (!layerVoids.value.length) return '0.0'
  const avg = layerVoids.value.reduce((a, b) => a + b, 0) / layerVoids.value.length
  return (avg * 100).toFixed(1)
})

const specExceeded = computed(() => {
  return layerVoids.value.filter(v => v > 0.05).length
})
</script>

<style scoped>
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; }
.page-header h1 { font-size: 22px; font-weight: 800; }
.info-table { width: 100%; border-collapse: collapse; }
.info-table tr { border-bottom: 1px solid var(--line); }
.info-table td { padding: 8px 4px; font-size: 13px; }
.info-label { color: var(--muted); width: 120px; }
.result-big { text-align: center; padding: 20px; }
.result-big .badge { font-size: 18px; padding: 8px 20px; }
.void-trend { display: flex; align-items: flex-end; gap: 12px; padding: 10px 0; }
.void-trend-bars { display: flex; align-items: flex-end; gap: 6px; flex: 1; height: 120px; }
.trend-bar-wrap { display: flex; flex-direction: column; align-items: center; gap: 4px; flex: 1; height: 100%; justify-content: flex-end; }
.trend-bar { width: 100%; border-radius: 4px 4px 0 0; min-height: 2px; transition: height .3s; }
.trend-label { font-size: 10px; color: var(--muted); }
.trend-ylabel { font-size: 11px; color: var(--muted); writing-mode: vertical-rl; }

/* 히트맵 */
.heatmap-wrap { margin-top: 20px; background: #0e1218; border: 1px solid var(--line); border-radius: 10px; padding: 16px; }
.heatmap-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.heatmap-title { font-size: 11px; font-weight: 700; color: var(--muted); letter-spacing: .5px; text-transform: uppercase; }
.heatmap-lot-badge { font-size: 10px; font-weight: 700; color: var(--brand); background: rgba(93,211,255,.1); border: 1px solid var(--brand); border-radius: 4px; padding: 2px 8px; letter-spacing: .5px; }
.heatmap-grid { display: flex; flex-direction: column; gap: 4px; }
.heatmap-row { display: flex; align-items: center; gap: 4px; }
.layer-label { font-size: 10px; color: var(--muted); width: 22px; text-align: right; flex-shrink: 0; }
.heatmap-cell { flex: 1; height: 28px; border-radius: 3px; cursor: pointer; transition: opacity .15s; }
.heatmap-cell:hover { opacity: 0.75; }
.heatmap-legend { display: flex; align-items: center; gap: 14px; margin-top: 12px; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--muted); }
.legend-dot { width: 10px; height: 10px; border-radius: 2px; }
.legend-note { font-size: 10px; color: var(--muted); margin-left: auto; opacity: .7; }
.heatmap-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 14px; border-top: 1px solid var(--line); padding-top: 14px; }
.heatmap-stat { text-align: center; }
.stat-value { font-size: 15px; font-weight: 800; }
.stat-label { font-size: 10px; color: var(--muted); margin-top: 2px; }
</style>
