<template>
  <v-card outlined class="pa-2 mb-4">
    <v-card-title class="subtitle-2 grey--text text--darken-1">
      Discussão da Regra
    </v-card-title>
    <v-divider></v-divider>
    <div class="chat-window" ref="chatWindow">
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="d-flex flex-column mb-1"
      >
        <span class="font-weight-bold">{{ msg.username || 'Anônimo' }}</span>
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
      placeholder="Escreva uma mensagem..."
      @keyup.enter="send"
      hide-details
    ></v-text-field>
    <v-btn small color="primary" @click="send">Enviar</v-btn>
  </v-card>
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
      }
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