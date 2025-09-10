import ApiService from '@/services/api.service'

/**
 * Nuxt plugin that displays a single snackbar when the backend signals that
 * the database is unavailable (HTTP 503).
 */
export default ({ $axios, store }) => {
  // Helper to show the notification only once per page load.
  const notifyDbDown = () => {
    if (process.server) return // run only in browser
    if (window.__db_down_notified) return
    window.__db_down_notified = true
    store.dispatch('notification/open', {
      message: 'Base de dados indisponível',
      type: 'error'
    })
  }

  // Intercept Nuxt Axios requests.
  $axios.onError((error) => {
    if (error.response?.status === 503) {
      notifyDbDown()
    }
  })

  // Intercept the internal ApiService instance used pelos repositórios.
  if (ApiService?.axios?.interceptors?.response) {
    ApiService.axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 503) {
          notifyDbDown()
        }
        return Promise.reject(error)
      }
    )
  }
} 