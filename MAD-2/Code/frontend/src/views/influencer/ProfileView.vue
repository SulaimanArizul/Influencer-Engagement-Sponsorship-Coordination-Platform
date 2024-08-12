<script setup lang="ts">
import InfluencerNav from '@/components/InfluencerNav.vue'
import { api } from '@/lib'
import { ref, watchEffect } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const profile = ref<any>({})
const isMe = ref<boolean>(false)

const getProfile = async () => {
  try {
    const res = await api.get(`/profile/${route.params.id}`)
    profile.value = res.data.user
    isMe.value = res.data.is_me
  } catch (error) {
    console.error(error)
  }
}

const handleProfileUpdate = async () => {
  try {
    await api.post(`/profile/update`, profile.value)
  } catch (error) {
    console.error(error)
  }
}

watchEffect(() => {
  getProfile()
})
</script>

<template>
  <InfluencerNav />
  <div class="d-flex justify-content-center align-items-center" style="height: 90dvh">
    <div class="card w-50">
      <div class="card-body">
        <form @submit.prevent="handleProfileUpdate" v-if="isMe">
          <div class="form-group">
            <label for="name">Name</label>
            <input
              type="text"
              class="form-control"
              id="name"
              name="name"
              placeholder="Enter name"
              v-model="profile.name"
              required
            />
          </div>
          <div class="form-group">
            <label for="email">Email address</label>
            <input
              type="email"
              class="form-control"
              id="email"
              name="email"
              placeholder="Enter email"
              v-model="profile.email"
              required
            />
          </div>

          <div class="form-group">
            <label for="category">Category</label>
            <input
              type="text"
              class="form-control"
              id="category"
              name="category"
              placeholder="Enter Category"
              v-model="profile.category"
              required
            />
          </div>

          <div class="form-group">
            <label for="niche">Niche</label>
            <input
              type="text"
              class="form-control"
              id="niche"
              name="niche"
              placeholder="Enter Niche"
              v-model="profile.niche"
              required
            />
          </div>

          <div class="form-group">
            <label for="reach">Reach</label>
            <input
              type="number"
              class="form-control"
              id="reach"
              name="reach"
              v-model="profile.reach"
              placeholder="Enter your current reach (Reach = Followers / Activity)"
              required
            />
          </div>
          <div class="text-center mt-3">
            <button type="submit" class="btn btn-primary w-100">Save Changes</button>
          </div>
        </form>

        <div class="" v-if="!isMe">
          <p class="card-text">Name : {{ profile.name }}</p>
          <p class="card-text">Email : {{ profile.email }}</p>
          <p class="card-text">Category : {{ profile.category }}</p>
          <p class="card-text">Niche : {{ profile.niche }}</p>
          <p class="card-text">Reach : {{ profile.reach }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
