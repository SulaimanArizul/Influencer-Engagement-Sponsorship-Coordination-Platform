<script setup lang="ts">
import SponsorNav from '@/components/SponsorNav.vue'
import { api } from '@/lib'
import { onMounted, ref } from 'vue'

const campaigns = ref<any[]>([])
const placeholderCampaigns = ref<any[]>(Array.from({ length: 12 }))
const button = ref()
const singleCampaign = ref({
  id: 0,
  name: '',
  description: '',
  goals: '',
  is_private: false,
  budget: 0,
  start_date: new Date().toISOString().split('T')[0],
  end_date: new Date().toISOString().split('T')[0]
})
const loaded = ref(false)
const isEdit = ref(false)

const getMyCampaigns = async () => {
  try {
    const res = await api.get('/campaigns/me')
    campaigns.value = res.data
    for (const item of campaigns.value) {
      console.log(item,typeof item, item.is_private , typeof item.is_private)
      if (item.is_private === 1) item.is_private = true
      else item.is_private = false
    }
    loaded.value = true
  } catch (error) {
    console.error(error)
  }
}

const handleCampaignDelete = async (id: number) => {
  try {
    await api.delete(`/campaigns/${id}`)
    campaigns.value = campaigns.value.filter((campaign) => campaign.id !== id)
  } catch (error) {
    console.error(error)
  }
}

const handleCampaignUpdate = async () => {
  try {
    const { id } = singleCampaign.value
    await api.put(`/campaigns/${id}`, singleCampaign.value)
    button.value?.click()
    singleCampaign.value = {
      id: 0,
      name: '',
      description: '',
      goals: '',
      is_private: false,
      budget: 0,
      start_date: new Date().toISOString().split('T')[0],
      end_date: new Date().toISOString().split('T')[0]
    }
    getMyCampaigns()
  } catch (error) {
    console.error(error)
  }
}

const handleCampaignCreate = async (event: Event) => {
  try {
    const { target } = event
    const form = target as HTMLFormElement
    const data = new FormData(form)
    singleCampaign.value = Object.fromEntries(data.entries()) as any
    await api.post('/campaigns', singleCampaign.value)
    button.value?.click()
    getMyCampaigns()
  } catch (error) {
    console.error(error)
  }
}

const exportCampaignReport = async () => {
  try {
    const res = await api.post('/reports/campaigns')
    const { data } = res
    const { task_id } = data

    const taskCheckInterval = setInterval(async () => {
      const res = await api.get(`/export-task/${task_id}`, {
        responseType: 'blob'
      })
      if (res.status === 200) {
        clearInterval(taskCheckInterval)
        const url = window.URL.createObjectURL(new Blob([res.data]))
        // Create a link element and simulate a click
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', 'campaigns.csv') // Replace with your file name
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        // Clean up the URL object
        window.URL.revokeObjectURL(url)
      }
    }, 4000)
  } catch (err) {
    console.error(err)
  }
}

const changeDataInModal = (data: any) => {
  singleCampaign.value = data
  isEdit.value = true
}

onMounted(() => {
  getMyCampaigns()
})
</script>

<template>
  <SponsorNav />

  <div class="text-end m-2">
    <button type="button" class="btn btn-info" @click="exportCampaignReport()">
      Export Campaigns Report
    </button>
    <button
      type="button"
      class="btn btn-primary ms-2"
      data-bs-toggle="modal"
      data-bs-target="#add-campaign-modal"
    >
      Add Campaign
    </button>
  </div>
  <div>
    <div class="container-fluid">
      <h4>My Campaigns</h4>
      <div class="row">
        <!-- Campaigns -->
        <div class="col-md-3 my-3" v-for="campaign in campaigns" :key="campaign.id" v-if="loaded">
          <div class="card">
            <h1 class="card-title">{{ campaign.name }}</h1>
            <div class="card-body">
              <p class="card-text">Start Date {{ campaign.start_date }}</p>
              <p class="card-text">End Date {{ campaign.end_date }}</p>
              <p class="card-text">₹ {{ campaign.budget }}</p>
              <p class="card-text text-muted">{{ campaign.description }}</p>
              <p class="card-text text-muted">{{ campaign.goals }}</p>
            </div>
            <div class="card-footer">
              <div class="d-flex justify-content-between">
                <router-link
                  type="button"
                  class="btn btn-success"
                  :to="'/sponsor/ad-requests/' + campaign.id"
                >
                  👀 View
                </router-link>
                <button
                  type="button"
                  class="btn btn-primary"
                  @click="changeDataInModal(campaign)"
                  data-bs-toggle="modal"
                  data-bs-target="#add-campaign-modal"
                >
                  ✎ Edit
                </button>
                <button
                  type="button"
                  class="btn btn-danger"
                  @click="handleCampaignDelete(campaign.id)"
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Campaigns Placeholder -->
        <div
          class="col-md-4 my-3"
          v-for="campaign in placeholderCampaigns"
          :key="campaign"
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

  <div
    class="modal fade"
    id="add-campaign-modal"
    tabindex="-1"
    aria-labelledby="add-campaign-modal-label"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="add-campaign-modal-label">
            {{ isEdit ? 'Edit Campaign' : 'Add Campaign' }}
          </h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            ref="button"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <!-- Add Form -->
          <form @submit.prevent="handleCampaignCreate" v-if="!isEdit">
            <div class="form-check form-switch float-end fs-5">
              <input
                class="form-check-input"
                type="checkbox"
                role="switch"
                :defaultChecked="singleCampaign.is_private"
                v-model="singleCampaign.is_private"
                id="flexSwitchCheckDefault"
              />
              <label class="form-check-label" for="flexSwitchCheckDefault">{{
                singleCampaign.is_private ? 'Private' : 'Public'
              }}</label>
            </div>

            <div class="form-group">
              <label for="name">Name</label>
              <input
                type="text"
                class="form-control"
                id="name"
                name="name"
                v-model="singleCampaign.name"
                required
              />
            </div>

            <div class="form-group">
              <label for="budget">Budget</label>
              <input
                type="number"
                class="form-control"
                id="budget"
                name="budget"
                v-model="singleCampaign.budget"
                required
              />
            </div>

            <div class="form-group">
              <label for="start_date">Start Date</label>
              <input
                type="date"
                class="form-control"
                id="start_date"
                name="start_date"
                v-model="singleCampaign.start_date"
                required
              />
            </div>

            <div class="form-group">
              <label for="end_date">End Date</label>
              <input
                type="date"
                class="form-control"
                id="end_date"
                name="end_date"
                v-model="singleCampaign.end_date"
                required
              />
            </div>

            <div class="form-group">
              <label for="description">Description</label>
              <textarea
                class="form-control"
                id="description"
                name="description"
                rows="3"
                v-model="singleCampaign.description"
              ></textarea>
            </div>
            <div class="form-group">
              <label for="goals">Goals</label>
              <textarea
                class="form-control"
                id="goals"
                name="goals"
                rows="3"
                v-model="singleCampaign.goals"
                required
              ></textarea>
            </div>

            <div class="text-center mt-3">
              <button class="btn btn-primary w-100">Save changes</button>
            </div>
          </form>

          <!-- Update form -->
          <form @submit.prevent="handleCampaignUpdate" v-if="isEdit">
            <div class="form-check form-switch float-end fs-5">
              <input
                class="form-check-input"
                type="checkbox"
                role="switch"
                v-model="singleCampaign.is_private"
                id="flexSwitchCheckDefault"
              />
              <label class="form-check-label" for="flexSwitchCheckDefault">{{
                singleCampaign.is_private ? 'Private' : 'Public'
              }}</label>
            </div>

            <div class="form-group">
              <label for="name">Name</label>
              <input
                type="text"
                class="form-control"
                id="name"
                name="name"
                v-model="singleCampaign.name"
                required
              />
            </div>

            <div class="form-group">
              <label for="budget">Budget</label>
              <input
                type="number"
                class="form-control"
                id="budget"
                name="budget"
                v-model="singleCampaign.budget"
                required
              />
            </div>

            <div class="form-group">
              <label for="start_date">Start Date</label>
              <input
                type="date"
                class="form-control"
                id="start_date"
                name="start_date"
                v-model="singleCampaign.start_date"
                required
              />
            </div>

            <div class="form-group">
              <label for="end_date">End Date</label>
              <input
                type="date"
                class="form-control"
                id="end_date"
                name="end_date"
                v-model="singleCampaign.end_date"
                required
              />
            </div>

            <div class="form-group">
              <label for="description">Description</label>
              <textarea
                class="form-control"
                id="description"
                name="description"
                rows="3"
                v-model="singleCampaign.description"
              ></textarea>
            </div>
            <div class="form-group">
              <label for="goals">Goals</label>
              <textarea
                class="form-control"
                id="goals"
                name="goals"
                rows="3"
                v-model="singleCampaign.goals"
                required
              ></textarea>
            </div>

            <div class="text-center mt-3">
              <button class="btn btn-primary w-100">Save changes</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
