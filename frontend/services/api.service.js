import axios from 'axios'
import { API_URL } from '../constants'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

class ApiService {
  constructor() {
    this.axios = axios.create({
      baseURL: API_URL,
      withCredentials: true,
      paramsSerializer: (params) => {
        const parts = []
        for (const key in params) {
          if (Object.prototype.hasOwnProperty.call(params, key)) {
            const value = params[key]
            if (Array.isArray(value)) {
              value.forEach((item) => {
                parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(item)}`)
              })
            } else {
              parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
            }
          }
        }
        return parts.join("&")
      }
    })
    this.axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // No Nuxt, o store é injetado no contexto da aplicação
          // O logout será tratado pelo middleware de autenticação
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  request(method, url, data = {}, config = {}) {
    return this.axios({
      method,
      url,
      data,
      ...config
    })
  }

  get(url, config = {}) {
    return this.request('get', url, {}, config)
  }

  post(url, data = {}, config = {}) {
    return this.request('post', url, data, config)
  }

  put(url, data = {}, config = {}) {
    return this.request('put', url, data, config)
  }

  patch(url, data = {}, config = {}) {
    return this.request('patch', url, data, config)
  }

  delete(url, config = {}) {
    return this.request('delete', url, {}, config)
  }
}

export default new ApiService()
