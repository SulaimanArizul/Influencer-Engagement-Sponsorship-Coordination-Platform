import { ref } from 'vue'
import { defineStore } from 'pinia'
import { useRouter } from 'vue-router'
import Cookies from 'js-cookie'

export const useUserStore = defineStore('user', () => {
  const user = ref({})
  updateUser(JSON.parse(Cookies.get('user') || '{}'))

  const router = useRouter()

  function updateUser(newUser) {
    user.value = newUser
    Cookies.set('user', JSON.stringify(newUser))
  }

  function redirectToLogin() {
    // redirect to login
    router.push('/')
  }

  function logout() {
    user.value = {}
    Cookies.remove('user')
    router.push('/')
  }

  function redirectToSponsorHome() {
    // redirect to sponsor home
    router.push('/sponsor')
  }

  function redirectToInfluencerHome() {
    // redirect to influencer home
    router.push('/influencer')
  }

  function redirectToAdminHome() {
    // redirect to admin home
    router.push('/admin')
  }

  return {
    user,
    updateUser,
    redirectToLogin,
    redirectToInfluencerHome,
    redirectToSponsorHome,
    redirectToAdminHome,
    logout
  }
})
