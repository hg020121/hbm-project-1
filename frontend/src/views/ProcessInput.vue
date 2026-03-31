<template>
  <div class="page">
    <div class="page-header">
      <h1>공정 데이터 입력 <span class="tag">{{ lotId }}</span></h1>
      <button class="btn btn-secondary" @click="$router.back()">← 뒤로</button>
    </div>

    <div class="grid grid-2">
      <!-- 공정 단계 선택 -->
      <div class="panel">
        <h2>공정 단계 선택</h2>
        <div class="step-list">
          <button v-for="step in steps" :key="step.value"
            :class="['step-btn', { active: activeStep === step.value }]"
            @click="activeStep = step.value">
            <span>{{ step.icon }}</span><span>{{ step.label }}</span>
          </button>
        </div>
      </div>

      <!-- 입력 폼 -->
      <div class="panel">
        <h2>{{ currentStep?.label }} 입력</h2>

        <!-- Stacking -->
        <div v-if="activeStep === 'stacking'">
          <div class="form-group"><label>Stacking 순서 (seq)</label><input type="number" v-model="form.stack_seq" class="input" min="1" max="10" /></div>
          <div class="form-group"><label>압력 (MPa)</label><input type="number" step="0.01" v-model="form.pressure" class="input" /></div>
          <div class="form-group"><label>Void 비율 (0~1)</label><input type="number" step="0.001" v-model="form.void_area_pct" class="input" placeholder="예) 0.75" /></div>
          <div class="form-group"><label>엔지니어 ID</label>
            <select v-model="form.engineer_id" class="input">
              <option v-for="e in store.engineers" :key="e.engineer_id" :value="e.engineer_id">{{ e.engineer_id }} - {{ e.name }}</option>
            </select>
          </div>
          <div class="form-group"><label>추천 ID (AI 추천 결과)</label><input v-model="form.recommend_id" class="input" placeholder="예) REC-001" /></div>
          <button class="btn btn-primary" style="width:100%" @click="submitStacking">등록</button>
        </div>

        <!-- Reflow -->
        <div v-if="activeStep === 'reflow'">
          <div class="form-group"><label>Reflow 순서 (seq)</label><input type="number" v-model="form.reflow_seq" class="input" min="1" max="9" /></div>
          <div class="form-group"><label>온도 (°C)</label><input type="number" step="0.1" v-model="form.temperature" class="input" /></div>
          <div class="form-group"><label>엔지니어 ID</label>
            <select v-model="form.engineer_id" class="input">
              <option v-for="e in store.engineers" :key="e.engineer_id" :value="e.engineer_id">{{ e.engineer_id }} - {{ e.name }}</option>
            </select>
          </div>
          <button class="btn btn-primary" style="width:100%" @click="submitReflow">등록</button>
        </div>

        <!-- Injection -->
        <div v-if="activeStep === 'injection'">
          <div class="form-group"><label>주입 압력 (MPa)</label><input type="number" step="0.01" v-model="form.inject_pressure" class="input" /></div>
          <div class="form-group"><label>엔지니어 ID</label>
            <select v-model="form.engineer_id" class="input">
              <option v-for="e in store.engineers" :key="e.engineer_id" :value="e.engineer_id">{{ e.engineer_id }} - {{ e.name }}</option>
            </select>
          </div>
          <button class="btn btn-primary" style="width:100%" @click="submitInjection">등록</button>
        </div>

        <!-- Result -->
        <div v-if="activeStep === 'result'">
          <div class="form-group"><label>최종 Void 비율 (0~1)</label><input type="number" step="0.001" v-model="form.void_area_pct" class="input" /></div>
          <div class="form-group"><label>판정</label>
            <select v-model="form.final_result" class="input">
              <option>사용</option><option>재활용</option><option>사용불가</option>
            </select>
          </div>
          <div class="form-group"><label>엔지니어 ID</label>
            <select v-model="form.engineer_id" class="input">
              <option v-for="e in store.engineers" :key="e.engineer_id" :value="e.engineer_id">{{ e.engineer_id }} - {{ e.name }}</option>
            </select>
          </div>
          <button class="btn btn-primary" style="width:100%" @click="submitResult">등록</button>
        </div>

        <div v-if="successMsg" class="success-msg">✅ {{ successMsg }}</div>
        <div v-if="store.error" class="error-msg">❌ {{ store.error }}</div>
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
const activeStep = ref('stacking')
const successMsg = ref('')
const form = ref({ stack_seq: 1, pressure: 2.20, void_area_pct: null, engineer_id: '', recommend_id: '', reflow_seq: 1, temperature: 250.0, inject_pressure: 0.40, final_result: '사용' })

const steps = [
  { value: 'stacking', label: 'Stacking', icon: '🔧' },
  { value: 'reflow', label: 'Reflow', icon: '🌡️' },
  { value: 'injection', label: 'MUF Injection', icon: '💉' },
  { value: 'result', label: '최종 결과', icon: '📊' },
]

const currentStep = computed(() => steps.find(s => s.value === activeStep.value))

onMounted(async () => {
  await store.fetchEngineers()
  if (store.engineers.length) form.value.engineer_id = store.engineers[0].engineer_id
})

async function submitStacking() {
  const result = await store.createStacking(lotId, {
    lot_id: lotId,
    engineer_id: form.value.engineer_id,
    recommend_id: form.value.recommend_id,
    stack_seq: parseInt(form.value.stack_seq),
    pressure: parseFloat(form.value.pressure),
    void_area_pct: form.value.void_area_pct ? parseFloat(form.value.void_area_pct) : null,
    stack_date: new Date().toISOString(),
  })
  if (result) { successMsg.value = `Stacking ${form.value.stack_seq}회차 등록 완료`; setTimeout(() => successMsg.value = '', 3000) }
}

async function submitReflow() {
  const result = await store.createReflow(lotId, {
    lot_id: lotId,
    engineer_id: form.value.engineer_id,
    reflow_seq: parseInt(form.value.reflow_seq),
    temperature: parseFloat(form.value.temperature),
    reflow_date: new Date().toISOString(),
  })
  if (result) { successMsg.value = `Reflow ${form.value.reflow_seq}회차 등록 완료`; setTimeout(() => successMsg.value = '', 3000) }
}

async function submitInjection() {
  const result = await store.createInjection(lotId, {
    lot_id: lotId,
    engineer_id: form.value.engineer_id,
    inject_pressure: parseFloat(form.value.inject_pressure),
    injection_date: new Date().toISOString(),
  })
  if (result) { successMsg.value = 'Injection 등록 완료'; setTimeout(() => successMsg.value = '', 3000) }
}

async function submitResult() {
  const result = await store.createResult(lotId, {
    lot_id: lotId,
    engineer_id: form.value.engineer_id,
    void_area_pct: parseFloat(form.value.void_area_pct),
    final_result: form.value.final_result,
    analysis_date: new Date().toISOString().slice(0, 10),
  })
  if (result) { successMsg.value = '최종 결과 등록 완료 (DONE)'; setTimeout(() => successMsg.value = '', 3000) }
}
</script>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.page-header h1 { font-size: 22px; font-weight: 800; }
.step-list { display: flex; flex-direction: column; gap: 8px; }
.step-btn { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border: 1px solid var(--line); background: #0e1218; color: var(--muted); border-radius: 10px; cursor: pointer; font-size: 14px; text-align: left; }
.step-btn.active { border-color: var(--brand); color: var(--brand); background: rgba(93,211,255,.08); }
.form-group { margin-bottom: 14px; }
.success-msg { margin-top: 14px; padding: 10px; background: rgba(46,204,113,.1); border: 1px solid var(--ok); border-radius: 8px; color: var(--ok); font-size: 13px; }
.error-msg { margin-top: 14px; padding: 10px; background: rgba(231,76,60,.1); border: 1px solid var(--err); border-radius: 8px; color: var(--err); font-size: 13px; }
</style>
