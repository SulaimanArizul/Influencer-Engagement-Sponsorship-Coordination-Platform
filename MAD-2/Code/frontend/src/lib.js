import axios from 'axios'
import Cookies from 'js-cookie'
import { toast } from 'vue3-toastify'

export const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-type': 'application/json'
  },
  withCredentials: true
})

api.interceptors.response.use(
  (response) => {
    if (response.data.msg) {
      toast.success(response.data.msg)
    }
    return response
  },
  (error) => {
    try {
      if (error.response.status === 401 || error.response.status === 403) {
        Cookies.remove('user')
        window.location.href = '/'
      }
      toast.error(error.response.data.msg)
    } catch (newError) {
      toast.error(error.message)
    }
    return Promise.reject(error)
  }
)
