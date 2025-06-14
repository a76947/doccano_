export const state = () => ({
  message: null,
  type: null, // 'success', 'error', 'warning', 'info'
  snackbar: false
})

export const mutations = {
  SET_NOTIFICATION(state, { message, type }) {
    state.message = message
    state.type = type
    state.snackbar = true
  },
  CLEAR_NOTIFICATION(state) {
    state.message = null
    state.type = null
    state.snackbar = false
  }
}

export const actions = {
  open({ commit }, { message, type = 'info' }) {
    commit('SET_NOTIFICATION', { message, type })
  },
  close({ commit }) {
    commit('CLEAR_NOTIFICATION')
  }
} 