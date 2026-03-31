<template>
  <div id="app">
    <nav v-if="user" class="navbar">
      <div class="nav-brand">
        <span class="dot"></span>
        <span class="brand-text">HBM MR-MUF AI 시스템</span>
      </div>

      <div class="role-toggle">
        <button
          :class="['toggle-btn', { active: user.role === 'engineer' }]"
          @click="switchRole('engineer')"
        >
          🔧 공정 모니터링
        </button>
        <button
          :class="['toggle-btn', { active: user.role === 'quality' }]"
          @click="switchRole('quality')"
        >
          🔬 품질 정밀분석
        </button>
      </div>

      <div class="nav-right">
        <button @click="$router.push('/chat')" class="btn-chat">💬 AI 챗봇</button>
        <span class="user-badge">{{ user.employeeId }}</span>
        <button @click="logout" class="btn-logout">로그아웃</button>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useHbmStore } from './store/hbm.js'

const store = useHbmStore()
const router = useRouter()
const user = computed(() => store.user)

function switchRole(role) {
  store.setRole(role)
  router.push(role === 'engineer' ? '/engineer' : '/quality')
}

function logout() {
  store.logout()
  router.push('/login')
}
</script>

<style>
:root {
  --bg: #0b0e11;
  --panel: #12161c;
  --ink: #e6edf3;
  --muted: #9fb0c0;
  --brand: #5dd3ff;
  --ok: #2ecc71;
  --warn: #f39c12;
  --err: #e74c3c;
  --line: #1e2732;
  --accent: #8ad6ff;
  --red: #ff4757;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--ink); font-family: 'Noto Sans KR', system-ui, sans-serif; }
a { color: var(--brand); text-decoration: none; }
.navbar {
  position: sticky; top: 0; z-index: 100;
  background: rgba(11,14,17,.85);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--line);
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 28px;
}
.nav-brand { display: flex; align-items: center; gap: 10px; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: var(--brand); box-shadow: 0 0 12px var(--brand); }
.brand-text { font-size: 16px; font-weight: 700; letter-spacing: .3px; }

.role-toggle {
  display: flex; gap: 4px;
  background: #0e1218; border: 1px solid var(--line);
  border-radius: 10px; padding: 4px;
}
.toggle-btn {
  padding: 6px 18px; border-radius: 7px; border: none;
  background: transparent; color: var(--muted);
  cursor: pointer; font-size: 13px; font-weight: 600;
  transition: all .2s;
}
.toggle-btn:hover { color: var(--ink); }
.toggle-btn.active {
  background: var(--brand); color: #0b0e11;
}

.nav-right { display: flex; align-items: center; gap: 12px; }
.user-badge { background: var(--panel); border: 1px solid var(--line); padding: 4px 10px; border-radius: 999px; color: var(--muted); font-size: 12px; }
.btn-chat { background: rgba(93,211,255,.1); border: 1px solid var(--brand); color: var(--brand); padding: 4px 12px; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all .15s; }
.btn-chat:hover { background: var(--brand); color: #0b0e11; }
.btn-logout { background: none; border: 1px solid var(--err); color: var(--err); padding: 4px 12px; border-radius: 8px; cursor: pointer; font-size: 12px; }
.btn-logout:hover { background: var(--err); color: white; }

/* 공통 컴포넌트 스타일 */
.page { padding: 28px; max-width: 1300px; margin: 0 auto; }
.panel { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 20px; }
.panel h2 { font-size: 15px; font-weight: 700; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
.tag { font-size: 11px; padding: 2px 8px; border-radius: 999px; border: 1px solid var(--line); color: var(--muted); }
.btn { appearance: none; border: none; padding: 10px 18px; border-radius: 10px; font-weight: 700; cursor: pointer; font-size: 14px; transition: all .15s; }
.btn-primary { background: linear-gradient(180deg,#1e90ff,#0077ff); color: white; box-shadow: 0 4px 14px rgba(0,119,255,.3); }
.btn-primary:hover { filter: brightness(1.1); }
.btn-secondary { background: var(--panel); color: var(--ink); border: 1px solid var(--line); }
.btn-danger { background: linear-gradient(180deg,#ff6b6b,#e74c3c); color: white; }
.btn-success { background: linear-gradient(180deg,#2ecc71,#27ae60); color: white; }
.btn:disabled { opacity: .5; cursor: not-allowed; }
.grid { display: grid; gap: 16px; }
.grid-2 { grid-template-columns: repeat(2, 1fr); }
.grid-3 { grid-template-columns: repeat(3, 1fr); }
.grid-4 { grid-template-columns: repeat(4, 1fr); }
.input { width: 100%; background: #0e1218; color: var(--ink); border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; font-size: 14px; outline: none; }
.input:focus { border-color: var(--brand); }
label { font-size: 12px; color: var(--muted); display: block; margin-bottom: 6px; }
.kpi-card { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 20px; text-align: center; }
.kpi-value { font-size: 32px; font-weight: 800; color: var(--brand); }
.kpi-label { font-size: 12px; color: var(--muted); margin-top: 4px; }
.badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.badge-ok { background: rgba(46,204,113,.15); color: var(--ok); border: 1px solid var(--ok); }
.badge-warn { background: rgba(243,156,18,.15); color: var(--warn); border: 1px solid var(--warn); }
.badge-err { background: rgba(231,76,60,.15); color: var(--err); border: 1px solid var(--err); }
.badge-blue { background: rgba(93,211,255,.15); color: var(--brand); border: 1px solid var(--brand); }
.lot-table { width: 100%; border-collapse: collapse; }
.lot-table th, .lot-table td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--line); font-size: 13px; }
.lot-table th { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .5px; }
.lot-table tr:hover td { background: rgba(255,255,255,.02); }
.loading { text-align: center; padding: 40px; color: var(--muted); }
.progress-ring { position: relative; display: inline-flex; align-items: center; justify-content: center; }
</style>
