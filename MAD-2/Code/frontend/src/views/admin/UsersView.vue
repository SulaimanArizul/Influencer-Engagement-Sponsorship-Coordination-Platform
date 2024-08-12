<script setup lang="ts">
import AdminNav from '@/components/AdminNav.vue'
import { api } from '@/lib'
import { onMounted, ref, watchEffect } from 'vue'
import { useRoute } from 'vue-router'

const loaded = ref<boolean>(false)
const users = ref<any[]>(Array.from({ length: 12 }, () => ({})))
const route = useRoute()

const getUsersData = async (tableName: string) => {
  try {
    const res = await api.get(`/users/${tableName}`)
    users.value = res.data
    for (const user of users.value) {
      if (user.is_flagged === 1) user.is_flagged = true
      else user.is_flagged = false
    }
    loaded.value = true
  } catch (error) {
    console.error(error)
  }
}

const flagObject = async (id: number, isFlag: boolean) => {
  try {
    if (isFlag) {
      await api.post(`/flag/${route.params.tableName}/${id}`)
    } else {
      await api.post(`/unflag/${route.params.tableName}/${id}`)
    }
    getUsersData(route.params.tableName as string)
  } catch (error) {
    console.error(error)
  }
}

watchEffect(() => {
  getUsersData(route.params.tableName as string)
})

onMounted(() => {
  getUsersData(route.params.tableName as string)
})
</script>

<template>
  <AdminNav />
  <div class="container-fluid">
    <div class="row">
      <div class="col-md-3 my-3" v-for="user in users" :key="user.id" v-if="loaded">
        <div class="card">
          <div class="card-body">
            <h1>{{ user.name }}</h1>
            <p class="card-text">{{ user.email }}</p>
            <p class="card-text">{{ user.industry }}</p>
            <p class="card-text" v-if="user.niche">{{ user.category }} - {{ user.niche }}</p>
          </div>
          <div class="card-footer">
            <button
              class="btn btn-danger w-100"
              @click="flagObject(user.id, true)"
              v-if="!user.is_flagged"
            >
              Flag
            </button>
            <button
              class="btn btn-success w-100"
              @click="flagObject(user.id, false)"
              v-if="user.is_flagged"
            >
              UnFlag
            </button>
          </div>
        </div>
      </div>

      <div class="col-md-3 my-3" v-for="user in users" :key="user.id" v-if="!loaded">
        <div class="card">
          <div class="card-body">
            <h1 class="card-title placeholder-glow">
              <span class="placeholder col-2"></span>
            </h1>
            <p class="card-text placeholder-glow">
              <span class="placeholder col-6"></span>
            </p>
            <p class="card-text placeholder-glow">
              <span class="placeholder col-4"></span>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
