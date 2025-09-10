<template>
  <div>
    <v-card outlined class="pa-2 mb-4">
      <v-card-title class="subtitle-2 grey--text text--darken-1">
        Discussão da Regra
      </v-card-title>
      <v-divider></v-divider>
      <div ref="chatWindow" class="chat-window">
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="d-flex flex-column mb-1"
        >
          <span 
            class="font-weight-bold" 
            :style="{ color: getUserColor(msg.username || 'Anônimo') }"
          >
            {{ msg.username || 'Anônimo' }}
          </span>
          <span>{{ msg.message }}</span>
          <span class="caption grey--text">{{ formatDate(msg.created_at) }}</span>
        </div>
        <div v-if="messages.length === 0" class="caption grey--text text-center">
          Não há mensagens ainda.
        </div>
      </div>

      <v-divider></v-divider>

      <v-text-field
        v-model="text"
        dense
        hide-details
        placeholder="Escreva uma mensagem..."
        @keyup.enter="send"
      ></v-text-field>
      <v-btn small color="primary" @click="send">Enviar</v-btn>
    </v-card>

    <v-snackbar
      v-model="snackbar"
      :color="snackbarColor"
      timeout="5000"
      top
    >
      {{ snackbarText }}
      <template #action="{ attrs }">
        <v-btn
          text
          v-bind="attrs"
          @click="snackbar = false"
        >
          Fechar
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
export default {
  name: 'RuleChat',
  props: {
    projectId: { type: [String, Number], required: true },
    sessionId: { type: [String, Number], required: true },
    questionIndex: { type: Number, required: true },
  },
  data() {
    return {
      messages: [],
      text: '',
      loading: false,
      snackbar: false,
      snackbarText: '',
      snackbarColor: 'warning'
    }
  },
  mounted() {
    this.fetchMessages()
  },
  methods: {
    async fetchMessages() {
      this.loading = true
      try {
        const res = await this.$services.ruleDiscussion.list(
          this.projectId,
          this.sessionId,
          this.questionIndex
        )
        this.messages = res.messages || res
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      } catch (e) {
        console.error('Erro ao buscar mensagens', e)
        this.showError('Erro ao carregar mensagens')
      } finally {
        this.loading = false
      }
    },
    async send() {
      if (!this.text.trim()) return
      try {
        await this.$services.ruleDiscussion.create(
          this.projectId,
          this.sessionId,
          this.questionIndex,
          this.text.trim()
        )
        this.text = ''
        await this.fetchMessages()
      } catch (e) {
        console.error('Erro ao enviar mensagem', e)
        if (e.response && e.response.status === 503) {
          // Emit event to parent page for critical errors
          this.$emit('critical-error', {
            code: 503,
            message: 'Serviço indisponível. O servidor está temporariamente fora do ar.'
          })
        } else {
          // Handle non-critical errors locally with snackbar
          this.showError('Erro ao enviar mensagem. Por favor, tente novamente mais tarde.')
        }
      }
    },
    showError(message) {
      this.snackbarText = message
      this.snackbarColor = 'error'
      this.snackbar = true
      // Force update in case there's a reactivity issue
      this.$nextTick(() => {
        setTimeout(() => {
          if (!this.snackbar) {
            this.snackbar = true
          }
        }, 100)
      })
    },
    scrollToBottom() {
      const el = this.$refs.chatWindow
      if (el && el.scrollTo) {
        el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
      }
    },
    formatDate(d) {
      const date = new Date(d)
      return date.toLocaleString()
    },
    getUserColor(username) {
      // Define a palette of distinct colors
      const colors = [
        '#FF0000', // Red
        '#00A0FF', // Blue
        '#00FF00', // Green
        '#FF00FF', // Magenta
        '#FFA500', // Orange
        '#9400D3', // Purple
        '#008080', // Teal
        '#FF4500', // Orange-Red
        '#FFD700', // Gold
        '#4B0082', // Indigo
        '#800000', // Maroon
        '#00FFFF', // Cyan
        '#8B4513', // Brown
        '#000000', // Black
        '#708090'  // Slate Gray
      ]
      
      // Create a hash from the username
      let hash = 0
      for (let i = 0; i < username.length; i++) {
        hash = ((hash << 5) - hash) + username.charCodeAt(i)
        hash = hash & hash // Convert to 32bit integer
      }
      
      // Use the hash to pick a color from our palette
      const index = Math.abs(hash) % colors.length
      return colors[index]
    },
  },
}
</script>

<style scoped>
.chat-window {
  max-height: 200px;
  overflow-y: auto;
  padding: 8px;
}
</style>