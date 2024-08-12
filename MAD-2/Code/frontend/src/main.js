import '../node_modules/bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.min.js'
import 'vue3-toastify/dist/index.css'
import Vue3Toastify from 'vue3-toastify'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router/index.js'

const app = createApp(App)

app.use(createPinia())
app.use(Vue3Toastify, {
  autoClose: 3000
})
app.use(router)

app.mount('#app')
