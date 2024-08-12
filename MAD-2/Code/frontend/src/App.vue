<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useUserStore } from './stores/user-store'

import { onMounted } from 'vue'

const userStore = useUserStore()

onMounted(() => {
  // if the user id is not set, redirect to the login page
  if (!userStore.user) {
    userStore.redirectToLogin()
    return
  }

  const role = userStore.user.role

  // if (role === 'SPR') {
  //   userStore.redirectToSponsorHome()
  // } else if (role === 'INF') {
  //   userStore.redirectToInfluencerHome()
  // } else if (role === 'ADM') {
  //   userStore.redirectToAdminHome()
  // }
})
</script>

<template>
  <RouterView />
</template>
