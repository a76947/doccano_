// ~/store/auth.js

export const state = () => ({
  username: null,
  id: null,
  isAuthenticated: false,
  isStaff: false
})

export const mutations = {
  setUsername(state, username) {
    state.username = username
  },
  setUserId(state, userId) {
    state.id = userId
  },
  clearUsername(state) {
    state.username = null
  },
  setAuthenticated(state, isAuthenticated) {
    state.isAuthenticated = isAuthenticated
  },
  setIsStaff(state, isStaff) {
    state.isStaff = isStaff
  }
}

export const getters = {
  // já existentes...
  isAuthenticated(state) {
    return state.isAuthenticated
  },
  getUsername(state) {
    return state.username
  },
  getUserId(state) {
    return state.id
  },
  isStaff(state) {
    return state.isStaff
  },

  // novo getter:
  currentUser(state) {
    return {
      id: state.id,
      username: state.username
    }
  }
}

export const actions = {
  // Exemplo de login (chama repositório)
  async authenticateUser({ commit }, authData) {
    try {
      await this.$repositories.auth.login(authData.username, authData.password)
      commit('setAuthenticated', true)
      // Se quiseres, chama initAuth() para puxar perfil do user
    } catch (error) {
      throw new Error('The credential is invalid')
    }
  },

  // Fetch do perfil do user logado
  async initAuth({ commit }) {
    try {
      const user = await this.$repositories.user.getProfile()  // /v1/me
      commit('setAuthenticated', true)
      commit('setUsername', user.username)
      commit('setUserId', user.id)
      commit('setIsStaff', user.isStaff)
    } catch (error) {
      commit('setAuthenticated', false)
      commit('setIsStaff', false)
      commit('clearUsername')
      commit('setUserId', null)
    }
  },

  // Logout
  async logout({ commit }) {
    try {
      // Chama logout no back-end
      await this.$repositories.auth.logout()
    } catch (error) {
      console.error('Erro ao deslogar no backend:', error)
    }

    // Limpa o estado local
    commit('setAuthenticated', false)
    commit('setIsStaff', false)
    commit('clearUsername')
    commit('setUserId', null)

    // Redirecionar para /login
    // Forma simples: forçar reload e levar para /login
    if (process.browser) {
      window.location = '/auth'
    }
  }
} 