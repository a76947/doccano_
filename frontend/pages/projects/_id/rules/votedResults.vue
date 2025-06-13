<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <span>Resultados das Votações</span>
      <v-spacer></v-spacer>
      <v-select
        v-model="selectedSession"
        :items="sessionOptions"
        label="Selecione a Sessão"
        outlined
        dense
        class="ml-4"
        style="max-width: 200px"
      ></v-select>
    </v-card-title>

    <v-data-table
      :headers="headers"
      :items="filteredQuestions"
      :loading="loading"
      class="elevation-1"
    >
      <template #[`item.session`]="{ item }">
        Sessão {{ item.sessionId }}
      </template>
      <template #[`item.votes`]="{ item }">
        <div class="vote-chart-container">
          <div v-if="item.votes.sim === 0 && item.votes.nao === 0" class="text-caption text-center">
            Nenhum voto registrado
          </div>
          <template v-else>
            <div class="vote-bars">
              <div class="vote-bar-container">
                <div class="vote-bar yes" :style="{ width: item.percentages.sim + '%' }">
                  <span class="percentage-text">{{ item.percentages.sim }}%</span>
                </div>
                <div class="vote-bar-background"></div>
              </div>
              <div class="vote-bar-container">
                <div class="vote-bar no" :style="{ width: item.percentages.nao + '%' }">
                  <span class="percentage-text">{{ item.percentages.nao }}%</span>
                </div>
                <div class="vote-bar-background"></div>
              </div>
            </div>
            <div class="vote-labels">
              <span class="vote-label">Sim: {{ item.votes.sim }}</span>
              <span class="vote-label">Não: {{ item.votes.nao }}</span>
            </div>
          </template>
        </div>
      </template>
      <template #[`item.participation`]="{ item }">
        <div class="participation-info">
          <div class="participation-icons">
            <span class="participation-item voted">
              <v-icon small color="success">mdi-checkbox-marked-circle</v-icon>
              <span class="label">Membros que Votaram:</span>
              <span class="count">{{ item.votersCount }}</span>
            </span>
            <span class="participation-item not-voted">
              <v-icon small color="error">mdi-close-circle</v-icon>
              <span class="label">Membros que Não Votaram:</span>
              <span class="count">{{ item.nonVotersCount }}</span>
            </span>
          </div>
        </div>
      </template>
      <template #[`item.history`]="{ item }">
        <v-btn
          small
          color="info"
          @click="openHistory(item.sessionId, item._index)"
        >
          Histórico
        </v-btn>
      </template>
    </v-data-table>

    <!-- Botão para voltar -->
    <v-card-actions>
      <v-spacer />
      <v-btn color="secondary" @click="goBack">
        Voltar
      </v-btn>
    </v-card-actions>

    <!-- Snackbars para feedback -->
    <v-snackbar v-model="snackbar" timeout="3000" top color="success">
      {{ snackbarMessage }}
      <template #action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
    <v-snackbar v-model="snackbarError" timeout="3000" top color="error">
      {{ snackbarErrorMessage }}
      <template #action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbarError = false">Close</v-btn>
      </template>
    </v-snackbar>

    <v-dialog v-model="dialogHistory" max-width="600px">
      <RuleChat
        v-if="dialogHistory"
        :project-id="projectId"
        :session-id="historySessionId"
        :question-index="historyQuestionIndex"
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
      votedSessions: [],
      loading: true,
      snackbar: false,
      snackbarMessage: '',
      snackbarError: false,
      snackbarErrorMessage: '',
      selectedSession: 'all',
      totalMembers: 0,
      headers: [
        { text: 'Sessão', value: 'session' },
        { text: 'Regra', value: 'question' },
        { text: 'Votos', value: 'votes' },
        { text: 'Participação', value: 'participation' },
        { text: 'Histórico', value: 'history', sortable: false },
      ],
      dialogHistory: false,
      historySessionId: null,
      historyQuestionIndex: null,
    };
  },
  computed: {
    projectId() {
      return this.$route.params.id;
    },
    sessionOptions() {
      const options = [
        { text: 'Todas as Sessões', value: 'all' }
      ];
      
      this.votedSessions.forEach(session => {
        options.push({
          text: `Sessão ${session.id}`,
          value: session.id.toString()
        });
      });
      
      return options;
    },
    filteredQuestions() {
      if (this.selectedSession === 'all') {
        return this.votedSessions.flatMap(session => 
          session.questions.map((question, index) => ({
            _index: index,
            sessionId: session.id,
            question: question.question,
            votes: this.getResponseCounts(question.responses),
            percentages: this.calculatePercentages(question.responses),
            votersCount: this.getUniqueVotersCount(question.responses),
            nonVotersCount: this.totalMembers - this.getUniqueVotersCount(question.responses)
          }))
        );
      } else {
        const session = this.votedSessions.find(s => s.id.toString() === this.selectedSession);
        if (!session) return [];
        
        return session.questions.map((question, index) => ({
          _index: index,
          sessionId: session.id,
          question: question.question,
          votes: this.getResponseCounts(question.responses),
          percentages: this.calculatePercentages(question.responses),
          votersCount: this.getUniqueVotersCount(question.responses),
          nonVotersCount: this.totalMembers - this.getUniqueVotersCount(question.responses)
        }));
      }
    },
    membersWhoVoted() {
      if (this.selectedSession === 'all') return 0;
      
      const session = this.votedSessions.find(s => s.id.toString() === this.selectedSession);
      if (!session) return 0;

      const firstQuestion = session.questions[0];
      if (!firstQuestion) return 0;

      const uniqueVoters = new Set(firstQuestion.responses.map(r => r.created_by));
      return uniqueVoters.size;
    },
    membersWhoDidNotVote() {
      return this.totalMembers - this.membersWhoVoted;
    }
  },
  mounted() {
    this.fetchVotedSessions();
    this.fetchTotalMembers();
  },
  methods: {
    calculatePercentages(responses) {
      const counts = this.getResponseCounts(responses);
      const total = counts.sim + counts.nao;
      
      if (total === 0) {
        return { sim: 0, nao: 0 };
      }

      return {
        sim: Math.round((counts.sim / total) * 100),
        nao: Math.round((counts.nao / total) * 100)
      };
    },
    async fetchTotalMembers() {
      try {
        // Primeiro tenta buscar o papel do usuário atual
        const myRole = await this.$repositories.member.fetchMyRole(this.projectId);
        
        // Se for admin, busca a lista completa de membros
        if (myRole.isProjectAdmin) {
          const response = await this.$repositories.member.list(this.projectId);
          this.totalMembers = response.length;
        } else {
          // Se não for admin, apenas conta o próprio usuário
          this.totalMembers = 1;
        }
      } catch (error) {
        console.error('Erro ao buscar membros:', error);
        this.snackbarErrorMessage = 'Erro ao buscar informações dos membros.';
        this.snackbarError = true;
        // Em caso de erro, assume pelo menos 1 membro (o próprio usuário)
        this.totalMembers = 1;
      }
    },
    async fetchVotedSessions() {
      try {
        const response = await this.$services.voting.list(this.projectId);
        const sessions = response.voting_sessions || [];
        console.log('Sessões recebidas:', sessions);
        
        // Array para armazenar as sessões processadas
        const processedSessions = [];
        
        // Processa cada sessão finalizada
        for (const session of sessions) {
          console.log('Processando sessão:', session);
          if (session.finish === true) {
            try {
              // Tenta buscar as respostas do usuário
              console.log(`Buscando respostas para sessão ${session.id}...`);
              const userAnswersResp = await this.$services.answer.listUserAnswers(
                this.projectId,
                session.id
              );
              console.log('Resposta recebida:', userAnswersResp);
              
              // Se tiver respostas, adiciona à lista
              if (userAnswersResp && userAnswersResp.user_answers) {
                const processedSession = {
                  ...session,
                  questions: session.questions.map((q, index) => ({
                    question: q,
                    responses: userAnswersResp.user_answers.map(answer => ({
                      answer: answer.answer[index],
                      created_by: answer.created_by
                    }))
                  }))
                };
                console.log('Sessão processada:', processedSession);
                processedSessions.push(processedSession);
              } else {
                console.log(`Sessão ${session.id} não possui respostas no formato esperado`);
              }
            } catch (error) {
              console.error(`Erro ao buscar respostas para sessão ${session.id}:`, error);
            }
          }
        }
        
        this.votedSessions = processedSessions;
        if (processedSessions.length === 0) {
          this.snackbarErrorMessage = 'Nenhuma sessão com respostas encontrada.';
          this.snackbarError = true;
        }
      } catch (error) {
        console.error('Erro ao buscar sessões:', error);
        this.snackbarErrorMessage = 'Erro ao buscar sessões. Por favor, tente novamente.';
        this.snackbarError = true;
      } finally {
        this.loading = false;
      }
    },
    getResponseCounts(responses) {
      const counts = {
        'sim': 0,
        'nao': 0
      };
      
      responses.forEach(response => {
        if (Object.prototype.hasOwnProperty.call(counts, response.answer)) {
          counts[response.answer]++;
        }
      });
      
      return counts;
    },
    getUniqueVotersCount(responses) {
      const uniqueVoters = new Set(responses.map(r => r.created_by));
      return uniqueVoters.size;
    },
    goBack() {
      this.$router.back();
    },
    openHistory(sessionId, questionIndex) {
      this.historySessionId = sessionId;
      this.historyQuestionIndex = questionIndex;
      this.dialogHistory = true;
    },
  },
};
</script>

<style scoped>
.vote-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 8px;
  width: 100%;
}

.vote-bar-container {
  position: relative;
  height: 35px;
  width: 100%;
  background-color: #f5f5f5;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
}

.vote-bar {
  position: relative;
  height: 100%;
  transition: width 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
}

.vote-bar.yes {
  background-color: #4CAF50;
}

.vote-bar.no {
  background-color: #EF5350;
}

.percentage-text {
  color: white;
  font-weight: 500;
  font-size: 0.875rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  z-index: 1;
  white-space: nowrap;
}

.vote-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.6);
  margin-top: 4px;
}

.vote-label {
  margin: 0 4px;
}

.vote-chart-container {
  width: 100%;
  padding: 8px 0;
  min-height: 35px;
}

.text-center {
  text-align: center;
  width: 100%;
}

.participation-info {
  padding: 4px 0;
  min-width: 300px;
}

.participation-icons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.participation-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.participation-item .label {
  font-size: 0.875rem;
  color: rgba(0, 0, 0, 0.6);
}

.participation-item .count {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
}

.participation-item.voted .count {
  color: #2E7D32;
}

.participation-item.not-voted .count {
  color: #C62828;
}
</style> 