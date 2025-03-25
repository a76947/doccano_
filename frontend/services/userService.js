import axios from 'axios'

export default {
  async updateUser(userId, data) {
    // Ajustado para /v1/users/<id>/
    const response = await axios.patch(`/v1/users/${userId}/`, data)
    return response.data
  }
}