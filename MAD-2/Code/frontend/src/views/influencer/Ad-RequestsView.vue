<script setup lang="ts">
import { api } from '@/lib'
import InfluencerNav from '@/components/InfluencerNav.vue'
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user-store'

const campaign = ref<any>({})
const adRequests = ref<any[]>(Array.from({ length: 12 }, () => ({})))
const loaded = ref<boolean>(false)
const button = ref<any>(null)
const isEdit = ref(false)

const singleAdRequest = ref<any>({
  id: 0,
  campaign_id: 0,
  requirements: '',
  payment_amount: 0,
  influencer_id: 0,
  status: '',
  activites: [] as any[]
})

const route = useRoute()
const userStore = useUserStore()

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

const changeSingleAdRequest = (request: any) => {
  getAdActivity(request)
  singleAdRequest.value = request
  isEdit.value = true
}

const handleAdRequestCreate = async () => {
  try {
    let toSendObj: any = {
      influencer_id: userStore.user.id,
      campaign_id: route.params.id as string,
      payment_amount: singleAdRequest.value.payment_amount,
      requirements: singleAdRequest.value.requirements
    }
    await api.post(`/ad-requests`, toSendObj)
    getAdRequests(route.params.id as string)
    button.value?.click()
    singleAdRequest.value = {
      id: 0,
      campaign_id: 0,
      requirements: '',
      payment_amount: 0,
      influencer_id: 0,
      status: '',
      activities: []
    }
  } catch (error) {
    console.error(error)
  }
}

const handleAdRequestEdit = async () => {
  try {
    const { id } = singleAdRequest.value
    singleAdRequest.value = {
      payment_amount: singleAdRequest.value.payment_amount,
      campaign_id: route.params.id as string
    }
    await api.put(`/ad-requests/${id}`, singleAdRequest.value)
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

const handleStatusChange = async (request: any, status: 'accepted' | 'rejected') => {
  try {
    await api.put(`/ad-requests/${request.id}/${status}`)
    const updatedAdRequest = adRequests.value.find((ar) => ar.id == request.id)
    updatedAdRequest.status = status
  } catch (error) {
    console.error(error)
  }
}

const getAdActivity = async (request: any) => {
  try {
    const res = await api.get(`/activity/${request.id}`)
    singleAdRequest.value.activities = res.data
    loaded.value = true
  } catch (error) {
    console.error(error)
  }
}

const cleanEdit = () => {
  isEdit.value = false
  singleAdRequest.value = {
    id: 0,
    campaign_id: 0,
    requirements: '',
    payment_amount: 0,
    influencer_id: 0,
    status: '',
    activities: []
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
})
</script>

<template>
  <InfluencerNav />
  <div class="text-end m-2">
    <button
      type="button"
      class="btn btn-primary"
      data-bs-toggle="modal"
      data-bs-target="#add-request-modal"
      @click="cleanEdit()"
    >
      + Raise Ad Request
    </button>
  </div>
  <div class="container-fluid">
    <h4>Ad Requests</h4>
    <div class="row">
      <!-- Ad Requests -->
      <div class="col-md-3 mt-3" v-for="request in adRequests" :key="request.id" v-if="loaded">
        <div class="card">
          <div class="card-body">
            <p class="card-text">Amount : {{ request.payment_amount }}</p>
            <p class="card-text text-muted">{{ request.requirements }}</p>
          </div>
          <div
            class="card-footer d-flex justify-content-around"
            v-if="request.status.toLowerCase() !== 'pending'"
          >
            <button
              class="btn btn-success"
              data-bs-target="#activity-request-modal"
              data-bs-toggle="modal"
              @click="changeSingleAdRequest(request)"
            >
              Activity
            </button>
          </div>
          <div
            class="card-footer d-flex justify-content-around"
            v-if="request.status.toLowerCase() === 'pending'"
          >
            <button
              class="btn btn-success"
              data-bs-target="#add-request-modal"
              data-bs-toggle="modal"
              @click="changeSingleAdRequest(request)"
            >
              Negotiate
            </button>
            <button class="btn btn-primary" @click="handleStatusChange(request, 'accepted')">
              Accept
            </button>
            <button class="btn btn-danger" @click="handleStatusChange(request, 'rejected')">
              Reject
            </button>
          </div>
        </div>
      </div>

      <!-- Ad Request Placeholder -->
      <div class="col-md-3 mt-3" v-for="request in adRequests" :key="request.id" v-if="!loaded">
        <div class="card">
          <div class="card-body">
            <p class="card-text placeholder-glow">
              <span class="placeholder col-4"></span>
            </p>
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
          <h1 class="modal-title fs-5" id="add-request-modal-label">Negotiate Payment</h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            ref="button"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <!-- Add Ad Request -->
          <form @submit.prevent="handleAdRequestCreate" v-if="!isEdit">
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

          <!-- Edit Form -->
          <form @submit.prevent="handleAdRequestEdit" v-if="isEdit">
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
            <div class="text-center mt-3">
              <button class="btn btn-primary w-100">Save changes</button>
            </div>
          </form>
        </div>
        <div class="modal-footer overflow-auto h-25">
          <div class="card col-12" v-for="activity in singleAdRequest.activities" :key="activity">
            <div class="card-body">
              <p class="card-text">{{ activity.message }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Activity Model Starts -->
  <div
    class="modal fade"
    id="activity-request-modal"
    tabindex="-1"
    aria-labelledby="add-request-modal-label"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="add-request-modal-label">Negotiate Payment</h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            ref="button"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body overflow-auto h-25">
          <div
            class="card col-12 my-1"
            v-for="activity in singleAdRequest.activities"
            :key="activity"
          >
            <div class="card-body">
              <p class="card-text">{{ activity.message }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
