<script setup>
import { api } from '@/lib'
import { useUserStore } from '@/stores/user-store'

const userStore = useUserStore()

const handleLogout = async () => {
  try {
    await api.get('/logout')
    userStore.logout()
  } catch (error) {
    console.error(error)
  }
}
</script>
<template>
  <nav class="navbar navbar-expand-lg bg-body-tertiary" data-bs-theme="dark">
    <div class="container-fluid">
      <router-link class="navbar-brand" to="/sponsor">Ad Platform</router-link>
      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarSupportedContent"
        aria-controls="navbarSupportedContent"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item">
            <button class="nav-item nav-link active" @click="handleLogout">Logout</button>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>
