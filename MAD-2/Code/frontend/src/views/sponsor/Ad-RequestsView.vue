<script setup lang="ts">
import { api } from '@/lib'
import SponsorNav from '@/components/SponsorNav.vue'
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const campaign = ref<any>({})
const adRequests = ref<any[]>(Array.from({ length: 12 }, () => ({})))
const isEdit = ref<boolean>(false)
const influencers = ref<any[]>([])
const loaded = ref<boolean>(false)
const button = ref<any>(null)

const singleAdRequest = ref<any>({
  id: 0,
  campaign_id: 0,
  requirements: '',
  payment_amount: 0,
  influencer_id: 0,
  status: ''
})

const route = useRoute()

const getAdRequests = async (id: string) => {
  try {
    const res = await api.get(`/campaigns/${id}`)
    campaign.value = res.data.campaign
    adRequests.value = res.data.ad_requests
    loaded.value = true
  } catch (error) {
    console.error(error)
  }
}

const getInfluencers = async () => {
  try {
    const res = await api.get('/users/influencers')
    influencers.value = res.data
  } catch (error) {
    console.error(error)
  }
}

const changeSingleAdRequest = (request: any) => {
  singleAdRequest.value = request
  isEdit.value = true
}

const handleAdRequestDelete = async (id: number) => {
  try {
    await api.delete(`/ad-requests/${id}`)
    adRequests.value = adRequests.value.filter((request) => request.id !== id)
  } catch (error) {
    console.error(error)
  }
}

const handleAdRequestEdit = async () => {
  try {
    singleAdRequest.value = {
      ...singleAdRequest.value,
      campaign_id: route.params.id as string
    }
    await api.put(`/ad-requests/${singleAdRequest.value.id}`, singleAdRequest.value)
    button.value?.click()
    singleAdRequest.value = {
      id: 0,
      campaign_id: 0,
      requirements: '',
      payment_amount: 0,
      influencer_id: 0,
      status: ''
    }
  } catch (error) {
    console.error(error)
  }
}

const handleAdRequestCreate = async () => {
  try {
    singleAdRequest.value = {
      ...singleAdRequest.value,
      campaign_id: route.params.id as string
    }
    await api.post('/ad-requests', singleAdRequest.value)
    button.value?.click()
  } catch (error) {
    console.error(error)
  }
}

watch(
  () => route.params,
  () => {
    getAdRequests(route.params.id as string)
  }
)

onMounted(() => {
  getAdRequests(route.params.id as string)
  getInfluencers()
})
</script>

<template>
  <SponsorNav />
  <div class="text-end m-2">
    <button
      type="button"
      class="btn btn-primary"
      data-bs-toggle="modal"
      data-bs-target="#add-request-modal"
    >
      + Ad Request
    </button>
  </div>
  <div class="container-fluid">
    <h4>Ad Requests</h4>
    <div class="row">
      <!-- Ad Requests -->
      <div class="col-md-3 mt-3" v-for="request in adRequests" :key="request.id" v-if="loaded">
        <div class="card">
          <div class="card-body">
            <p class="card-text">Influencer Name : {{ request.influencer_name }}</p>
            <p class="card-text">Amount : {{ request.payment_amount }}</p>
            <p class="card-text text-muted">{{ request.requirements }}</p>
          </div>
          <div class="card-footer"  v-if="request.status.toLowerCase() !== 'pending'">
            <h5>Status : {{ request.status }}</h5>
          </div>
          <div class="card-footer" v-if="request.status.toLowerCase() === 'pending'">
            <div class="d-flex justify-content-around">
              <button
                type="button"
                class="btn btn-primary"
                data-bs-toggle="modal"
                data-bs-target="#add-request-modal"
                @click="changeSingleAdRequest(request)"
              >
                ✎ Edit
              </button>
              <button
                type="button"
                class="btn btn-danger"
                @click="handleAdRequestDelete(request.id)"
              >
                🗑️ Delete
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Ad Request Placeholder -->
      <div class="col-md-3 mt-3" v-for="request in adRequests" :key="request.id" v-if="!loaded">
        <div class="card">
          <div class="card-body">
            <h1 class="card-title placeholder-glow">
              <span class="placeholder col-2"></span>
            </h1>
            <p class="card-text placeholder-glow">
              <span class="placeholder col-8"></span>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Modal starts -->
  <div
    class="modal fade"
    id="add-request-modal"
    tabindex="-1"
    aria-labelledby="add-request-modal-label"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="add-request-modal-label">
            {{ isEdit ? 'Edit Request' : 'Add Request' }}
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
          <form @submit.prevent="handleAdRequestCreate" v-if="!isEdit">
            <!-- Select Influencer -->
            <div class="row">
              <div class="col-md-6">
                <!-- Payment Amount -->
                <div class="form-group">
                  <label for="influencer_id">Payment Amount</label>
                  <input
                    type="number"
                    class="form-control"
                    v-model="singleAdRequest.payment_amount"
                    min="10"
                    required
                  />
                </div>

                <!-- Requirements -->
                <div class="form-group">
                  <label for="requirements">Requirements</label>
                  <textarea
                    class="form-control"
                    v-model="singleAdRequest.requirements"
                    required
                    rows="3"
                  ></textarea>
                </div>
              </div>
              <div class="col-md-6">
                <!-- list of influencers -->
                <div class="card-header">Select Influencer</div>
                <ul class="list-group">
                  <button
                    v-for="influencer in influencers"
                    :key="influencer.id"
                    :class="
                      'list-group-item list-group-item-action' +
                      (singleAdRequest.influencer_id === influencer.id ? ' active' : '')
                    "
                    @click="singleAdRequest.influencer_id = influencer.id"
                  >
                    {{ influencer.name }}
                  </button>
                </ul>
              </div>
            </div>

            <div class="text-center mt-3">
              <button class="btn btn-primary w-100">Save changes</button>
            </div>
          </form>

          <!-- Edit Form -->
          <form @submit.prevent="handleAdRequestEdit" v-if="isEdit">
            <!-- Select Influencer -->
            <div class="form-group">
              <label for="influencer_id">Select Influencer</label>
              <select class="form-control" required v-model="singleAdRequest.influencer_id">
                <option value="">Select Influencer</option>
                <option
                  v-for="influencer in influencers"
                  :key="influencer.id"
                  :value="influencer.id"
                >
                  {{ influencer.name }}
                </option>
              </select>
            </div>

            <!-- Payment Amount -->
            <div class="form-group">
              <label for="influencer_id">Payment Amount</label>
              <input
                type="number"
                class="form-control"
                v-model="singleAdRequest.payment_amount"
                min="10"
                required
              />
            </div>

            <!-- Requirements -->
            <div class="form-group">
              <label for="requirements">Requirements</label>
              <textarea
                class="form-control"
                v-model="singleAdRequest.requirements"
                required
                rows="3"
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
