import { $axios } from "@/backend/api"

export default {
  async fetchGroups() {
    const response = await $axios.get('/groups/')
    return response.data
  },
  async createGroup(data: { name: string; permissions?: number[] }) {
    const response = await $axios.post('/groups/', data)
    return response.data
  }
}
