<template>
  <div class="login-wrap">
    <div class="login-box">
      <div class="login-logo">
        <div class="logo-dot"></div>
        <h1>HBM MR-MUF<br/>AI 공정 추천 시스템</h1>
      </div>
      <p class="login-sub">AI 공정 추천 시스템 로그인</p>

      <div class="form-group">
        <label>사번</label>
        <input v-model="employeeId" class="input" placeholder="SKH-001" @keyup.enter="doLogin" />
      </div>

      <div class="form-group">
        <label>비밀번호</label>
        <input v-model="password" type="password" class="input" placeholder="비밀번호를 입력하세요" @keyup.enter="doLogin" />
      </div>

      <button class="btn btn-primary login-btn" @click="doLogin" :disabled="!employeeId || !password">
        시스템 접속
      </button>

      <p class="test-hint">테스트 계정: SKH-001 / 1234</p>
      <p class="test-hint-sub">접속 후 대시보드 상단에서 역할을 전환할 수 있습니다.</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useHbmStore } from '../store/hbm.js'

const store = useHbmStore()
const router = useRouter()
const employeeId = ref('')
const password = ref('')

function doLogin() {
  if (!employeeId.value || !password.value) return
  store.login(employeeId.value)
  router.push('/engineer')
}
</script>

<style scoped>
.login-wrap {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: radial-gradient(ellipse at 50% 30%, #0d2a3a 0%, #0b0e11 70%);
}
.login-box {
  background: var(--panel); border: 1px solid var(--line);
  border-radius: 20px; padding: 40px 36px; width: 420px;
  box-shadow: 0 20px 60px rgba(0,0,0,.5);
}
.login-logo { display: flex; align-items: center; gap: 14px; margin-bottom: 8px; }
.logo-dot { width: 14px; height: 14px; border-radius: 50%; background: var(--brand); box-shadow: 0 0 20px var(--brand); flex-shrink: 0; }
h1 { font-size: 20px; font-weight: 800; line-height: 1.3; }
.login-sub { font-size: 12px; color: var(--muted); margin-bottom: 28px; }
.form-group { margin-bottom: 16px; }
.login-btn { width: 100%; padding: 14px; font-size: 15px; margin-top: 4px; }
.test-hint { margin-top: 16px; text-align: center; font-size: 12px; color: var(--brand); }
.test-hint-sub { margin-top: 4px; text-align: center; font-size: 11px; color: var(--muted); }
</style>
