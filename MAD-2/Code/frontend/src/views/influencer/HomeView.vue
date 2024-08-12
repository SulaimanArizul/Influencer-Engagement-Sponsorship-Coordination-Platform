<script setup lang="ts">
import InfluencerNav from '@/components/InfluencerNav.vue'
import { api } from '@/lib'
import { onMounted, reactive, ref } from 'vue'
import { watchDebounced } from '@vueuse/core'

const campaignsPlaceholder = ref<any[]>(Array.from({ length: 6 }, () => ({})))
const filteredCampaigns = ref<any[]>([])
const loaded = ref<boolean>(false)
const bugets = reactive({
  min: 0,
  max: 0
})
const params = reactive({
  name: '',
  goals: '',
  start_date: '',
  end_date: '',
  budget_lte: 0,
  budget_gte: 0
})

const getPublicCampaigns = async () => {
  try {
    loaded.value = false
    const actualParams = new URLSearchParams()
    for (const key in params) {
      if (params[key as keyof typeof params] as any) {
        actualParams.append(key, params[key as keyof typeof params] as any)
      }
    }
    const res = await api.get(`/campaigns/filter?${actualParams.toString()}`)
    filteredCampaigns.value = res.data.campaigns
    bugets.max = res.data.max_budget
    if (res.data.max_budget === res.data.min_budget) bugets.min = 0
    loaded.value = true
  } catch (error) {
    console.error(error)
  }
}

watchDebounced(
  params,
  () => {
    getPublicCampaigns()
  },
  { debounce: 1000, maxWait: 2000 }
)

onMounted(() => {
  getPublicCampaigns()
})
</script>

<template>
  <InfluencerNav />

  <div class="container-fluid">
    <div class="row">
      <div class="col-md-2">
        <div class="row">
          <div class="card m-md-2 p-0">
            <h5 class="card-title text-center my-2">Filter Campaigns</h5>
            <div class="card-body">
              <!-- Name Filter -->
              <div class="form-group">
                <input
                  type="text"
                  class="form-control"
                  id="name"
                  name="name"
                  placeholder="Name"
                  v-model="params.name"
                />
              </div>

              <!-- Goals Filter -->
              <div class="form-group my-2">
                <input
                  type="text"
                  class="form-control"
                  id="goals"
                  name="goals"
                  placeholder="Goals"
                  v-model="params.goals"
                />
              </div>

              <!-- Start Date Filter -->
              <div class="form-group my-2">
                <label for="start_date">Start Date</label>
                <input
                  type="date"
                  class="form-control"
                  id="start_date"
                  name="start_date"
                  v-model="params.start_date"
                />
              </div>

              <!-- End Date Filter -->
              <div class="form-group my-2">
                <label for="end_date">End Date</label>
                <input
                  type="date"
                  class="form-control"
                  id="end_date"
                  name="end_date"
                  v-model="params.end_date"
                />
              </div>

              <!-- Budget Less Than Filter -->
              <div class="form-group my-2">
                <label for="budget_lte">Budget Low Range ₹ {{ params.budget_gte }}</label>
                <input
                  type="range"
                  class="form-range"
                  :min="bugets.min"
                  step="5"
                  :max="bugets.max"
                  name="budget_gte"
                  v-model="params.budget_gte"
                />
              </div>

              <!-- Budget Greater Than Filter -->
              <div class="form-group my-2">
                <label for="budget_gte">Budget High Range ₹ {{ params.budget_lte }}</label>
                <input
                  type="range"
                  class="form-range"
                  :min="bugets.min"
                  step="5"
                  :max="bugets.max"
                  name="budget_lte"
                  v-model="params.budget_lte"
                />
              </div>

              <button type="submit" class="btn btn-primary my-2 w-100">Filter</button>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-10">
        <div class="row">
          <!-- Campaigns -->
          <div
            class="col-md-4 my-2"
            v-for="campaign in filteredCampaigns"
            :key="campaign.id"
            v-if="loaded"
          >
            <div class="card">
              <h1 class="card-title">{{ campaign.name }}</h1>
              <div class="card-body">
                <p class="card-text">Start Date : {{ campaign.start_date }}</p>
                <p class="card-text">End Date : {{ campaign.end_date }}</p>
                <p class="card-text">₹ {{ campaign.budget }}</p>
                <p class="card-text text-muted">{{ campaign.description }}</p>
                <p class="card-text text-muted">{{ campaign.goals }}</p>
              </div>
              <div class="card-footer">
                <div class="d-flex justify-content-between">
                  <router-link
                    type="button"
                    class="btn btn-success w-100"
                    :to="'/influencer/ad-requests/' + campaign.id"
                  >
                    👀 View
                  </router-link>
                </div>
              </div>
            </div>
          </div>

          <!-- Campaigns Placeholder -->
          <div
            class="col-md-4 my-2"
            v-for="campaign in campaignsPlaceholder"
            :key="campaign.id"
            v-if="!loaded"
          >
            <div class="card">
              <div class="card-title placeholder-glow">
                <span class="placeholder col-6"></span>
              </div>
              <div class="card-body">
                <p class="card-text placeholder-glow">
                  <span class="placeholder col-2"></span>
                </p>
                <p class="card-text placeholder-glow">
                  <span class="placeholder col-2"></span>
                </p>
                <p class="card-text placeholder-glow">
                  <span class="placeholder col-2"></span>
                </p>
                <div class="card-footer placeholder-glow">
                  <a class="btn btn-primary disabled placeholder col-6" aria-disabled="true"></a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
