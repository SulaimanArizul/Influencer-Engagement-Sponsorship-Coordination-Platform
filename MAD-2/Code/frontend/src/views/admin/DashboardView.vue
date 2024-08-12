<script setup lang="ts">
import AdminNav from '@/components/AdminNav.vue'
import { api } from '@/lib'
import { onMounted, ref } from 'vue'

const loaded = ref<boolean>(false)
const countsData = ref<any>(Array.from({ length: 12 }, () => ({})))
const toApproveSponsors = ref<any[]>([])
const recentAdRequests = ref<any[]>([])

const handleSponsorStatusChange = async (id: number, status: number) => {
  try {
    await api.put(`/sponsor-status/${id}/${status}`)
    toApproveSponsors.value = toApproveSponsors.value.filter((sponsor) => sponsor.id !== id)
  } catch (error) {
    console.error(error)
  }
}

const getDashboardData = async () => {
  try {
    const res = await api.get('/dashboard')
    countsData.value = res.data.data
    toApproveSponsors.value = res.data.to_approve_sponsors
    recentAdRequests.value = res.data.recent_ad_requests
    loaded.value = true
  } catch (error) {
    console.error(error)
  }
}

onMounted(() => {
  getDashboardData()
})
</script>

<template>
  <AdminNav />
  <div class="container-fluid">
    <div class="row">
      <div class="col-md-2 my-3" v-for="count in countsData" :key="count.title" v-if="loaded">
        <div class="card">
          <div class="card-body">
            <h1>{{ count.count }}</h1>
            <p class="card-text">{{ count.title }}</p>
          </div>
        </div>
      </div>

      <div class="col-md-2 my-3" v-for="count in countsData" :key="count.title" v-if="!loaded">
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
    <div class="row">
      <div class="col-md-6">
        <h3>To Approve Sponsors</h3>
        <table class="table table-striped table-hover table-bordered table-responsive">
          <thead>
            <tr>
              <th>S.No</th>
              <th>Name</th>
              <th>Email</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="sponsor in toApproveSponsors" :key="sponsor.id">
              <td>{{ sponsor.id }}</td>
              <td>{{ sponsor.name }}</td>
              <td>{{ sponsor.email }}</td>
              <td>
                <button
                  class="btn btn-primary mx-1"
                  @click="handleSponsorStatusChange(sponsor.id, 1)"
                >
                  ✓ Approve
                </button>
                <!-- <button class="btn btn-danger" @click="handleSponsorStatusChange(sponsor.id, 0)">
                  ✘
                </button> -->
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="col-md-6">
        <h3>Recent Ad Requests</h3>
        <table class="table table-striped table-hover table-bordered table-responsive">
          <thead>
            <tr>
              <th>S.No</th>
              <th>Campaign Name</th>
              <th>Sponsor Name</th>
              <th>Influencer Name</th>
              <th>Requirements</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="request in recentAdRequests" :key="request.id">
              <td>{{ request.id }}</td>
              <td>{{ request.campaign_name }}</td>
              <td>{{ request.sponsor_name }}</td>
              <td>{{ request.influencer_name }}</td>
              <td>{{ request.requirements }}</td>
              <td>{{ request.status.toUpperCase() }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
