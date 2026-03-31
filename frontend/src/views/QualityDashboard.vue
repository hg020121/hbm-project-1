<template>
  <div class="page">
    <div class="page-header">
      <h1>품질 분석 대시보드 <span class="tag">품질조사원</span></h1>
    </div>

    <!-- KPI 카드 -->
    <div class="grid grid-4" style="margin-bottom:20px" v-if="dashboard">
      <div class="kpi-card">
        <div class="kpi-value" style="color:var(--ok)">{{ dashboard.yield_rate }}%</div>
        <div class="kpi-label">전체 수율</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value">{{ dashboard.done_lots }}</div>
        <div class="kpi-label">완료 LOT</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value" style="color:var(--err)">{{ dashboard.defect_count }}</div>
        <div class="kpi-label">불량 건수</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value" style="color:var(--warn)">{{ (dashboard.avg_void * 100).toFixed(1) }}%</div>
        <div class="kpi-label">평균 void</div>
      </div>
    </div>

    <!-- 완료 LOT 결과 -->
    <div class="panel" style="margin-bottom:20px">
      <h2>완료 LOT 결과 분석 <span class="tag">DONE</span></h2>
      <table class="lot-table">
        <thead>
          <tr><th>LOT ID</th><th>최종 void</th><th>판정</th><th>분석일</th><th>액션</th></tr>
        </thead>
        <tbody>
          <tr v-for="r in results" :key="r.lot_id">
            <td><strong>{{ r.lot_id }}</strong></td>
            <td>
              <div class="void-indicator">
                <div class="void-bar-inline" :style="{ width: (r.void_area_pct * 100) + '%', background: voidColor(r.void_area_pct) }"></div>
                <span>{{ (r.void_area_pct * 100).toFixed(1) }}%</span>
              </div>
            </td>
            <td><span :class="resultBadge(r.final_result)">{{ r.final_result }}</span></td>
            <td>{{ r.analysis_date }}</td>
            <td>
              <button class="btn btn-secondary" style="padding:4px 10px;font-size:12px" @click="$router.push(`/lot/${r.lot_id}`)">상세</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Sol 3 + Sol 4 -->
    <div class="grid grid-2">

      <!-- Sol 3: PDF RAG -->
      <div class="panel">
        <h2>📄 논문 업로드 <span class="tag">RAG</span></h2>
        <p style="font-size:12px;color:var(--muted);margin-bottom:14px">PDF 논문을 업로드하면 벡터DB에 저장되어 AI 챗봇과 추천에 활용됩니다.</p>
        <input type="file" accept=".pdf" @change="onPdfUpload" ref="pdfInput" style="display:none" />
        <button class="btn btn-primary" @click="$refs.pdfInput.click()" :disabled="uploading">
          {{ uploading ? '업로드 중...' : '📎 PDF 업로드' }}
        </button>
        <div v-if="pdfResult" class="upload-result">
          <p style="color:var(--ok)">✅ {{ pdfResult.filename }}</p>
          <p style="font-size:12px;color:var(--muted)">{{ pdfResult.chunks }}개 청크 벡터화 완료</p>
        </div>

        <div style="margin-top:20px">
          <h3 style="font-size:13px;margin-bottom:10px">논문 기반 질의</h3>
          <textarea v-model="ragQuestion" class="input" style="min-height:80px;resize:vertical" placeholder="예) MR-MUF 공정에서 void 발생을 줄이는 방법은?"></textarea>
          <button class="btn btn-secondary" style="margin-top:8px;width:100%" @click="doRagQuery" :disabled="querying">
            {{ querying ? '검색 중...' : '🔍 논문에서 검색' }}
          </button>
          <div v-if="ragAnswer" class="rag-answer">
            <p style="font-size:12px;line-height:1.7">{{ ragAnswer }}</p>
          </div>
        </div>
      </div>

      <!-- Sol 4: 이미지 Vision AI + 히트맵 -->
      <div class="panel">
        <h2>📷 SAM 이미지 분석 <span class="tag">Vision AI</span></h2>
        <p style="font-size:12px;color:var(--muted);margin-bottom:14px">SAM 검사 이미지를 업로드하면 GPT Vision이 void를 분석합니다.</p>
        <input type="file" accept="image/*" @change="onImageUpload" ref="imgInput" style="display:none" />
        <button class="btn btn-primary" @click="$refs.imgInput.click()" :disabled="analyzing">
          {{ analyzing ? '분석 중...' : '🖼️ 이미지 업로드' }}
        </button>

        <div v-if="analyzing" class="loading" style="padding:20px">분석 중...</div>

        <div v-if="imageResult && !analyzing">
          <!-- void 추정 + 분석 텍스트 -->
          <div class="image-analysis-result">
            <div class="analysis-row">
              <span class="analysis-label">void 추정</span>
              <span class="analysis-value" :style="{ color: voidColor(imageResult.void_estimate || 0) }">
                {{ ((imageResult.void_estimate || 0) * 100).toFixed(1) }}%
              </span>
            </div>
            <p style="font-size:12px;color:var(--muted);margin-top:8px;line-height:1.6">{{ imageResult.analysis }}</p>
            <p style="font-size:12px;color:var(--brand);margin-top:6px;line-height:1.6">💡 {{ imageResult.recommendation }}</p>
          </div>

          <!-- 층별 히트맵 -->
          <div v-if="imageResult.layer_voids && imageResult.layer_voids.length" class="heatmap-wrap">
            <div class="heatmap-header">
              <div class="heatmap-title">VOID PATTERN — 층별 히트맵</div>
              <span class="heatmap-lot-badge">GPT Vision</span>
            </div>

            <div class="heatmap-grid">
              <div
                v-for="(layerVoid, li) in [...imageResult.layer_voids].reverse()"
                :key="li"
                class="heatmap-row"
              >
                <span class="layer-label">L{{ 10 - li }}</span>
                <div
                  v-for="(cell, ci) in getLayerCells(layerVoid, li)"
                  :key="ci"
                  class="heatmap-cell"
                  :style="{ background: cellColor(cell) }"
                  :title="`L${10 - li} | ${(layerVoid * 100).toFixed(1)}%`"
                ></div>
              </div>
            </div>

            <!-- 범례 -->
            <div class="heatmap-legend">
              <span class="legend-item"><span class="legend-dot" style="background:#2ecc71"></span> &lt;2%</span>
              <span class="legend-item"><span class="legend-dot" style="background:#f39c12"></span> 2~5%</span>
              <span class="legend-item"><span class="legend-dot" style="background:#e74c3c"></span> &gt;5%</span>
            </div>

            <!-- 통계 -->
            <div class="heatmap-stats">
              <div class="heatmap-stat">
                <div class="stat-value" style="color:var(--ok)">{{ (Math.min(...imageResult.layer_voids) * 100).toFixed(1) }}%</div>
                <div class="stat-label">최소 VOID</div>
              </div>
              <div class="heatmap-stat">
                <div class="stat-value" style="color:var(--warn)">{{ avgLayerVoid }}%</div>
                <div class="stat-label">평균 VOID</div>
              </div>
              <div class="heatmap-stat">
                <div class="stat-value" style="color:var(--err)">{{ (Math.max(...imageResult.layer_voids) * 100).toFixed(1) }}%</div>
                <div class="stat-label">최대 VOID</div>
              </div>
              <div class="heatmap-stat">
                <div class="stat-value" :style="{ color: specExceeded > 0 ? 'var(--err)' : 'var(--ok)' }">{{ specExceeded }}층</div>
                <div class="stat-label">SPEC 초과</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useHbmStore } from '../store/hbm.js'
import axios from 'axios'

const store = useHbmStore()
const dashboard = ref(null)
const results = ref([])
const pdfInput = ref(null)
const imgInput = ref(null)
const pdfResult = ref(null)
const uploading = ref(false)
const ragQuestion = ref('')
const ragAnswer = ref('')
const querying = ref(false)
const imageResult = ref(null)
const analyzing = ref(false)

onMounted(async () => {
  await store.fetchDashboard()
  dashboard.value = store.dashboard
  const { data } = await axios.get('/api/lots', { params: { status: 'DONE' } })
  for (const lot of data.slice(0, 20)) {
    const h = await store.fetchLotHistory(lot.lot_id)
    if (h?.result) results.value.push({ lot_id: lot.lot_id, ...h.result })
  }
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

// 층별 셀 12개 생성 (층 평균값 기반 노이즈 추가)
function getLayerCells(layerVoid, layerIdx) {
  return Array.from({ length: 12 }, (_, i) => {
    const noise = Math.sin(i * 3.7 + layerIdx * 5.1) * layerVoid * 0.4
    return Math.max(0, Math.min(1, layerVoid + noise))
  })
}

const avgLayerVoid = computed(() => {
  if (!imageResult.value?.layer_voids?.length) return '0.0'
  const avg = imageResult.value.layer_voids.reduce((a, b) => a + b, 0) / imageResult.value.layer_voids.length
  return (avg * 100).toFixed(1)
})

const specExceeded = computed(() => {
  if (!imageResult.value?.layer_voids?.length) return 0
  return imageResult.value.layer_voids.filter(v => v > 0.05).length
})

async function onPdfUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  uploading.value = true
  pdfResult.value = await store.uploadPdf(file)
  uploading.value = false
}

async function doRagQuery() {
  if (!ragQuestion.value) return
  querying.value = true
  const result = await store.ragQuery(ragQuestion.value)
  ragAnswer.value = result?.answer || '답변을 찾을 수 없습니다.'
  querying.value = false
}

async function onImageUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  analyzing.value = true
  imageResult.value = null
  imageResult.value = await store.analyzeImage(file)
  analyzing.value = false
}
</script>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h1 { font-size: 22px; font-weight: 800; }
.void-indicator { display: flex; align-items: center; gap: 8px; }
.void-bar-inline { height: 6px; border-radius: 3px; max-width: 80px; }
.upload-result { margin-top: 12px; background: rgba(46,204,113,.08); border: 1px solid var(--ok); border-radius: 8px; padding: 10px; }
.rag-answer { margin-top: 10px; background: rgba(93,211,255,.05); border: 1px solid var(--line); border-radius: 8px; padding: 12px; }
.image-analysis-result { margin-top: 12px; background: #0e1218; border: 1px solid var(--line); border-radius: 10px; padding: 14px; }
.analysis-row { display: flex; justify-content: space-between; align-items: center; }
.analysis-label { font-size: 13px; color: var(--muted); }
.analysis-value { font-size: 22px; font-weight: 800; }

/* 히트맵 */
.heatmap-wrap { margin-top: 14px; background: #0e1218; border: 1px solid var(--line); border-radius: 10px; padding: 16px; }
.heatmap-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.heatmap-title { font-size: 11px; font-weight: 700; color: var(--muted); letter-spacing: .5px; text-transform: uppercase; }
.heatmap-lot-badge { font-size: 10px; font-weight: 700; color: var(--brand); background: rgba(93,211,255,.1); border: 1px solid var(--brand); border-radius: 4px; padding: 2px 8px; letter-spacing: .5px; }
.heatmap-grid { display: flex; flex-direction: column; gap: 4px; }
.heatmap-row { display: flex; align-items: center; gap: 4px; }
.layer-label { font-size: 10px; color: var(--muted); width: 22px; text-align: right; flex-shrink: 0; }
.heatmap-cell { flex: 1; height: 28px; border-radius: 3px; cursor: pointer; transition: opacity .15s; }
.heatmap-cell:hover { opacity: 0.75; }
.heatmap-legend { display: flex; gap: 14px; margin-top: 12px; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--muted); }
.legend-dot { width: 10px; height: 10px; border-radius: 2px; }
.heatmap-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 14px; border-top: 1px solid var(--line); padding-top: 14px; }
.heatmap-stat { text-align: center; }
.stat-value { font-size: 15px; font-weight: 800; }
.stat-label { font-size: 10px; color: var(--muted); margin-top: 2px; }
</style>
