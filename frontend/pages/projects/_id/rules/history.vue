<template>
  <v-card>
    <v-card-title>Histórico das Discussões de Regras</v-card-title>
    <v-select
      v-model="selectedSession"
      :items="sessionOptions"
      label="Sessão"
      dense
      outlined
      class="ma-4"
    />
    <v-list two-line>
      <v-list-item
        v-for="(question, idx) in questions"
        :key="idx"
        @click="openChat(idx)"
      >
        <v-list-item-content>
          <v-list-item-title>{{ question }}</v-list-item-title>
        </v-list-item-content>
        <v-list-item-action>
          <v-icon color="info">mdi-chat</v-icon>
        </v-list-item-action>
      </v-list-item>
    </v-list>

    <v-dialog v-model="dialog" max-width="600px">
      <RuleChat
        v-if="dialog"
        :project-id="projectId"
        :session-id="selectedSession"
        :question-index="currentQuestionIndex"
      />
    </v-dialog>
  </v-card>
</template>

<script>
import RuleChat from '~/components/rules/RuleChat.vue'
export default {
  components: { RuleChat },
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],
  data() {
    return {
      sessions: [],
      selectedSession: null,
      dialog: false,
      currentQuestionIndex: null,
    }
  },
  computed: {
    projectId() {
      return this.$route.params.id
    },
    sessionOptions() {
      return this.sessions.map(s => ({ text: `Sessão ${s.id}`, value: s.id }))
    },
    questions() {
      const sess = this.sessions.find(s => s.id === this.selectedSession)
      return sess ? sess.questions : []
    },
  },
  async mounted() {
    await this.fetchSessions()
    if (this.sessions.length) this.selectedSession = this.sessions[0].id
  },
  methods: {
    async fetchSessions() {
      try {
        const resp = await this.$services.voting.list(this.projectId)
        this.sessions = resp.voting_sessions.filter(s => !!s.questions)
      } catch (e) {
        console.error('Erro ao buscar sessões', e)
      }
    },
    openChat(idx) {
      this.currentQuestionIndex = idx
      this.dialog = true
    },
  },
}
</script> 