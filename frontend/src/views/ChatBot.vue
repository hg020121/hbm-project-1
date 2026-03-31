<template>
  <div class="page">
    <div class="chat-layout">
      <div class="chat-sidebar">
        <h2 style="font-size:15px;font-weight:700;margin-bottom:16px">🤖 AI 챗봇</h2>
        <p style="font-size:12px;color:var(--muted);margin-bottom:14px">
          공정/품질 관련 질문을 입력하세요.<br/>
          PDF 논문이 업로드된 경우 논문 기반으로도 답변합니다.
        </p>
        <div class="form-group">
          <label>LOT 컨텍스트 (선택)</label>
          <select v-model="selectedLot" class="input">
            <option value="">없음</option>
            <option v-for="lot in store.lots" :key="lot.lot_id" :value="lot.lot_id">{{ lot.lot_id }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>역할</label>
          <div style="display:flex;gap:8px">
            <button :class="['role-btn', { active: role === 'engineer' }]" @click="role = 'engineer'">⚙️ 공정</button>
            <button :class="['role-btn', { active: role === 'quality' }]" @click="role = 'quality'">🔍 품질</button>
          </div>
        </div>
        <div class="quick-questions">
          <p style="font-size:11px;color:var(--muted);margin-bottom:8px">빠른 질문</p>
          <button v-for="q in quickQuestions" :key="q" class="quick-btn" @click="sendQuick(q)">{{ q }}</button>
        </div>
      </div>

      <div class="chat-main">
        <div class="chat-messages" ref="msgContainer">
          <div v-if="messages.length === 0" class="chat-welcome">
            <div style="font-size:40px;margin-bottom:14px">🤖</div>
            <h3>HBM MR-MUF AI 어시스턴트</h3>
            <p style="color:var(--muted);font-size:13px;margin-top:6px">공정 파라미터, 수율 분석, 논문 기반 정보를 질문해보세요.</p>
          </div>
          <div v-for="(msg, i) in messages" :key="i" :class="['msg', msg.role]">
            <div class="msg-bubble">
              <div class="msg-icon">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
              <div class="msg-text" v-html="formatMsg(msg.content)"></div>
            </div>
            <div class="msg-time">{{ msg.time }}</div>
          </div>
          <div v-if="thinking" class="msg assistant">
            <div class="msg-bubble">
              <div class="msg-icon">🤖</div>
              <div class="msg-text thinking">분석 중<span class="dots">...</span></div>
            </div>
          </div>
        </div>

        <div class="chat-input-area">
          <textarea
            v-model="inputMsg"
            class="chat-input"
            placeholder="질문을 입력하세요... (Enter: 전송, Shift+Enter: 줄바꿈)"
            @keydown.enter.exact.prevent="sendMessage"
            rows="3"
          ></textarea>
          <button class="btn btn-primary send-btn" @click="sendMessage" :disabled="thinking || !inputMsg.trim()">전송</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useHbmStore } from '../store/hbm.js'

const store = useHbmStore()
const messages = ref([])
const inputMsg = ref('')
const thinking = ref(false)
const selectedLot = ref('')
const role = ref(store.user?.role || 'engineer')
const msgContainer = ref(null)

const quickQuestions = [
  'void가 높을 때 어떻게 해야 하나요?',
  '최적 stacking 압력 범위는?',
  'MR-MUF 공정에서 수율을 높이려면?',
  '현재 LOT의 공정 상태를 분석해주세요',
]

onMounted(async () => {
  await store.fetchLots()
})

function formatMsg(text) {
  return text.replace(/\n/g, '<br/>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}

async function sendMessage() {
  if (!inputMsg.value.trim() || thinking.value) return
  const msg = inputMsg.value.trim()
  inputMsg.value = ''

  messages.value.push({ role: 'user', content: msg, time: now() })
  thinking.value = true
  await scrollBottom()

  const result = await store.sendChat(msg, role.value, selectedLot.value || null)
  thinking.value = false

  if (result) {
    messages.value.push({ role: 'assistant', content: result.response, time: now() })
  } else {
    messages.value.push({ role: 'assistant', content: '오류가 발생했습니다. 다시 시도해주세요.', time: now() })
  }
  await scrollBottom()
}

async function sendQuick(q) {
  inputMsg.value = q
  await sendMessage()
}

async function scrollBottom() {
  await nextTick()
  if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight
}

function now() {
  return new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.chat-layout { display: grid; grid-template-columns: 260px 1fr; gap: 16px; height: calc(100vh - 100px); }
.chat-sidebar { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 20px; overflow-y: auto; }
.chat-main { display: flex; flex-direction: column; background: var(--panel); border: 1px solid var(--line); border-radius: 14px; overflow: hidden; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.chat-welcome { text-align: center; padding: 60px 20px; color: var(--ink); }
.msg { display: flex; flex-direction: column; }
.msg.user { align-items: flex-end; }
.msg.assistant { align-items: flex-start; }
.msg-bubble { display: flex; gap: 10px; max-width: 75%; }
.msg.user .msg-bubble { flex-direction: row-reverse; }
.msg-icon { width: 32px; height: 32px; border-radius: 50%; background: var(--line); display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
.msg-text { background: #1a2332; border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; font-size: 14px; line-height: 1.6; }
.msg.user .msg-text { background: #0f3460; border-color: #1e5a9e; }
.msg-time { font-size: 11px; color: var(--muted); margin-top: 4px; padding: 0 10px; }
.thinking { color: var(--muted); }
.dots { animation: blink 1s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
.chat-input-area { display: flex; gap: 10px; padding: 14px; border-top: 1px solid var(--line); }
.chat-input { flex: 1; background: #0e1218; color: var(--ink); border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; font-size: 14px; outline: none; resize: none; font-family: inherit; }
.chat-input:focus { border-color: var(--brand); }
.send-btn { align-self: flex-end; padding: 10px 20px; }
.form-group { margin-bottom: 14px; }
.role-btn { flex: 1; padding: 8px; border: 1px solid var(--line); background: #0e1218; color: var(--muted); border-radius: 8px; cursor: pointer; font-size: 12px; }
.role-btn.active { border-color: var(--brand); color: var(--brand); background: rgba(93,211,255,.08); }
.quick-questions { display: flex; flex-direction: column; gap: 6px; }
.quick-btn { background: #0e1218; border: 1px solid var(--line); color: var(--muted); padding: 8px 10px; border-radius: 8px; cursor: pointer; font-size: 12px; text-align: left; transition: all .15s; }
.quick-btn:hover { border-color: var(--brand); color: var(--brand); }
</style>
