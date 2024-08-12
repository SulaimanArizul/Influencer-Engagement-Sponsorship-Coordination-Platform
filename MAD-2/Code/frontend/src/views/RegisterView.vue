<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/lib'
import { useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { useUserStore } from '@/stores/user-store'

const selectedRole = ref<string | null>('SPR')
const router = useRouter()
const userStore = useUserStore()

const checkOnlyOne = (role: string) => {
  selectedRole.value = role
}

const handleRegister = async (event: Event) => {
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
    await api.post('/register', jsonData)
    userStore.updateUser(jsonData as any)
    if (selectedRole.value! === 'INF') router.push('/influencer/')
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
            <h5 class="card-title text-center">Please register</h5>
            <form @submit.prevent="handleRegister">
              <!-- a switch for changing roles SPR,INF -->
              <div class="form-check form-switch float-end">
                <input
                  class="form-check-input"
                  type="checkbox"
                  role="switch"
                  :checked="selectedRole === 'SPR'"
                  @change="checkOnlyOne(selectedRole === 'SPR' ? 'INF' : 'SPR')"
                  id="flexSwitchCheckDefault"
                />
                <label class="form-check-label" for="flexSwitchCheckDefault">{{
                  selectedRole === 'INF' ? 'Influencer' : 'Sponsor'
                }}</label>
              </div>
              <div class="form-group">
                <label for="name">Name</label>
                <input
                  type="text"
                  class="form-control"
                  id="name"
                  name="name"
                  placeholder="Enter name"
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

              <div class="form-group" v-if="selectedRole === 'INF'">
                <label for="category">Category</label>
                <input
                  type="text"
                  class="form-control"
                  id="category"
                  name="category"
                  placeholder="Enter Category"
                  required
                />
              </div>

              <div class="form-group" v-if="selectedRole === 'INF'">
                <label for="niche">Niche</label>
                <input
                  type="text"
                  class="form-control"
                  id="niche"
                  name="niche"
                  placeholder="Enter Niche"
                  required
                />
              </div>

              <div class="form-group" v-if="selectedRole === 'INF'">
                <label for="reach">Reach</label>
                <input
                  type="number"
                  class="form-control"
                  id="reach"
                  name="reach"
                  placeholder="Enter your current reach (Reach = Followers / Activity)"
                  required
                />
              </div>

              <div class="form-group" v-if="selectedRole === 'SPR'">
                <label for="max_budget">Max Budget</label>
                <input
                  type="number"
                  class="form-control"
                  id="max_budget"
                  name="max_budget"
                  placeholder="Enter Max Budget"
                  min="100"
                  required
                />
              </div>

              <div class="form-group" v-if="selectedRole === 'SPR'">
                <label for="industry">Industry</label>
                <input
                  type="text"
                  class="form-control"
                  id="industry"
                  name="industry"
                  placeholder="Enter Industry"
                  min="100"
                  required
                />
              </div>

              <div class="text-center mt-3">
                <button type="submit" class="btn btn-primary w-100">Submit</button>
              </div>
              <RouterLink to="/" class="btn btn-link w-100 text-center mt-3"
                >Have an account? Go Login</RouterLink
              >
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
