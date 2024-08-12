<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/lib'
import { RouterLink, useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { useUserStore } from '@/stores/user-store'

const selectedRole = ref<string | null>(null)
const router = useRouter()
const userStore = useUserStore()

const checkOnlyOne = (role: string) => {
  selectedRole.value = role
}

const handleLogin = async (event: Event) => {
  try {
    if (!selectedRole.value) {
      toast.warn('Please select a role')
      return
    }
    const { target } = event
    const form = target as HTMLFormElement
    const data = new FormData(form)
    let jsonData = Object.fromEntries(data.entries())
    jsonData = { ...jsonData, role: selectedRole.value! }
    const { data: responseData } = await api.post('/login', jsonData)
    jsonData = { ...jsonData, id: responseData.id }
    userStore.updateUser(jsonData as any)
    if (selectedRole.value! === 'ADM') router.push('/admin')
    else if (selectedRole.value! === 'SPR') router.push('/sponsor/')
    else if (selectedRole.value! === 'INF') router.push('/influencer/')
  } catch (error) {
    // handle error
  }
}
</script>

<style lang="css" scoped>
.full-height {
  height: 100vh;
}

@media (max-width: 768px) {
  .card {
    margin: 20px;
  }
}

@media (min-width: 768px) {
  .min-vh-100 {
    min-height: 100vh;
  }
}
</style>

<template>
  <div class="container-fluid">
    <div class="row no-gutters">
      <!-- Image Column -->
      <div class="col-12 col-md-8 full-height d-none d-md-block">
        <div
          class="full-height"
          style="
            background-image: url('/login.avif');
            background-size: cover;
            background-position: center;
            height: 100vh;
          "
        ></div>
      </div>

      <!-- Form Card Column -->
      <div class="col-12 col-md-4 d-flex align-items-center justify-content-center min-vh-100">
        <div class="card w-100">
          <div class="card-body">
            <h5 class="card-title text-center">Welcome Back</h5>
            <form @submit.prevent="handleLogin">
              <div class="form-group">
                <label for="email">Email address</label>
                <input
                  type="email"
                  class="form-control"
                  id="email"
                  name="email"
                  placeholder="Enter email"
                  required
                />
              </div>
              <div class="form-group">
                <label for="password">Password</label>
                <input
                  type="password"
                  class="form-control"
                  name="password"
                  id="password"
                  placeholder="Password"
                  minlength="6"
                  required
                />
              </div>
              <div class="d-flex gap-4 mt-1 form-group flex-wrap justify-content-evenly">
                <label class="w-100">Select Role</label>
                <div class="form-check">
                  <input
                    class="form-check-input"
                    type="checkbox"
                    :value="'ADM'"
                    :checked="selectedRole === 'ADM'"
                    @change="checkOnlyOne('ADM')"
                  />
                  <label class="form-check-label" for="admin"> Admin </label>
                </div>
                <div class="form-check">
                  <input
                    class="form-check-input"
                    type="checkbox"
                    :value="'SPR'"
                    :checked="selectedRole === 'SPR'"
                    @change="checkOnlyOne('SPR')"
                  />
                  <label class="form-check-label" for="sponsor"> Sponsor </label>
                </div>
                <div class="form-check">
                  <input
                    class="form-check-input"
                    type="checkbox"
                    :value="'INF'"
                    :checked="selectedRole === 'INF'"
                    @change="checkOnlyOne('INF')"
                  />
                  <label class="form-check-label" for="influencer"> Influencer </label>
                </div>
              </div>
              <div class="text-center mt-3">
                <button type="submit" class="btn btn-primary w-100">Submit</button>
              </div>
              <RouterLink to="/register" class="btn btn-link w-100 text-center mt-3"
                >Don't have an account? Register</RouterLink
              >
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
