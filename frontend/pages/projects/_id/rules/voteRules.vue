<template>
  <v-card>
    <v-card-title>
      Segunda Tabela de Regras
    </v-card-title>
    <v-expansion-panels>
      <v-expansion-panel v-for="(session, idx) in rulesSecondTable" :key="idx">
        <v-expansion-panel-header>
          Sessão {{ idx + 1 }}
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <StringTableWithResponse 
            :items="session.questions"
            :loading="loadingSecondTable"
            @onSubmit="(res) => submitResponses(session, res)"
          />
          <RuleChat
            :project-id="$route.params.id"
            :session-id="session.id"
            :question-index="0"
          />
        </v-expansion-panel-content>
      </v-expansion-panel>
    </v-expansion-panels>
    <!-- Novo Botão para fechar a página -->
    <v-card-actions>
      <v-spacer />
      <v-btn color="secondary" @click="closePage">
        Fechar
      </v-btn>
    </v-card-actions>

    <!-- Tabela Admin: somente visível para usuários administradores -->
    <v-card v-if="isAdmin" class="mt-5">
      <v-card-title>
        Visualização Administrativa - Todas as Sessões (Regras)
      </v-card-title>
      <v-expansion-panels>
        <v-expansion-panel v-for="sessionAdmin in allSessions" :key="sessionAdmin.id">
          <v-expansion-panel-header>
            Sessão {{ sessionAdmin.id }} - 
            <span v-if="sessionAdmin.finish === false">
              <v-icon small color="green" class="ml-1">Active</v-icon>
            </span>
            <span v-else>
              <v-icon small color="red" class="ml-1">Finished</v-icon>
            </span>
          </v-expansion-panel-header>
          <v-expansion-panel-content>
            <StringTableAdmin 
              :items="sessionAdmin.questions"
              :loading="loadingAdminTable"
              @onFinish="() => finalizeSession(sessionAdmin)"
            />
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-card>

    <!-- Snackbar para exibir mensagem de sucesso -->
    <v-snackbar v-model="snackbar" timeout="3000" top color="success">
      {{ snackbarMessage }}
      <template #action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
    <!-- Snackbar para exibir mensagem de erro-->
    <v-snackbar v-model="snackbarError" timeout="3000" top color="error">
      {{ snackbarErrorMessage }}
      <template #action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbarError = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-card>
</template>

<script>
import StringTableWithResponse from '~/components/rules/stringTableWithResponse.vue';
import StringTableAdmin from '~/components/rules/stringTableAdmin.vue';
import RuleChat from '~/components/rules/RuleChat.vue'
export default {
  components: { StringTableWithResponse, StringTableAdmin, RuleChat },
  data() {
    return {
      rulesSecondTable: [],
      allSessions: [], // Armazena todas as sessões para o admin
      loadingSecondTable: true,
      loadingAdminTable: true,
      validSession: null,
      user: null,
      snackbar: false,
      snackbarMessage: '',
      snackbarError: false,
      snackbarErrorMessage: '',
    };
  },
  computed: {
    isAdmin() {
      // Retorna true se o usuário existir e for admin.
      return this.user && this.user.isProjectAdmin;
    }
  },
  created() {
    this.updateExpiredSessions();
    this.fetchRulesSecondTable();
    this.isAdmin = true; 

    this.fetchUserRole();
  },
  methods: {
    async updateExpiredSessions() {
      const projectId = this.$route.params.id;
      try {
        const response = await this.$services.voting.list(projectId);
        const sessions = response.voting_sessions || [];
        const now = new Date();
        for (const session of sessions) {
          const endDate = new Date(session.vote_end_date);
          if (endDate < now && !session.finish) {
            await this.$services.voting.updateSessionFinish(projectId, session.id);
          }
        }
      } catch (error) {
        console.error('Erro ao atualizar sessões expiradas:', error);
      }
    },

    async fetchRulesSecondTable() {
      const projectId = this.$route.params.id;
      try {
        // Obtém as sessões de votação do projeto
        const response = await this.$services.voting.list(projectId);
        const sessions = response.voting_sessions || [];
        
        // Armazena todas as sessões para a visualização do admin
        this.allSessions = sessions;
        
        // Para cada sessão, busca as respostas do usuário usando o novo endpoint
        for (const session of sessions) {
          try {
            const userAnswersResp = 
              await this.$services.answer.listUserAnswers(projectId, session.id);
            session.userAnswers = userAnswersResp.user_answers;
          } catch (error) {
            console.error(`Erro ao buscar as respostas do usuário para a sessão ${session.id}:`, error);
            session.userAnswers = [];
          }
        }

        // Exibe o estado de cada sessão e as respostas do usuário
        for (const session of sessions) {
          if (!session.userAnswers || session.userAnswers.length === 0) {
            console.log(`Sessão ${session.id} não possui respostas do usuário.`);
            console.log(`Estado da Sessão ${session.id}:`, session.finish);
          } else {
            console.log(`Sessão ${session.id} possui respostas do usuário:`, session.userAnswers);
            console.log(`Estado da Sessão ${session.id}:`, session.finish);
          }
        }
        
        // Linha quebrada para não exceder o limite de 100 caracteres
        const activeSessions = sessions.filter(session => 
          session.finish === false &&
          (!session.userAnswers || session.userAnswers.length === 0)
        );
        
        if (activeSessions.length) {
          this.rulesSecondTable = activeSessions;
          this.validSession = activeSessions[0]; // opcionalmente, usar a primeira sessão ativa
          console.log('Sessões ativas extraídas (ainda não votadas):', activeSessions);
        } else {
          this.rulesSecondTable = [];
          this.validSession = null;
          console.warn('Nenhuma sessão ativa (ainda não votada) encontrada.');
        }

        sessions.forEach(session => console.log('Session', session.id, 'userAnswers:', session.userAnswers));
      } catch (error) {
        console.error('Erro ao buscar regras da segunda tabela:', error);
      } finally {
        this.loadingSecondTable = false;
        this.loadingAdminTable = false;
      }
    },

    async submitResponses(session, responses) {
      const allAnswered = !(responses && responses.incomplete === true);
      if (!allAnswered) {
        this.snackbarErrorMessage = "É necessário responder todas as perguntas da sessão para submeter.";
        this.snackbarError = true;
      } else {
        try {
          console.log('Submetendo respostas:', responses);
          const projectId = this.$route.params.id;
          const votingSessionId = session ? session.id : null;
          console.log('ID do projeto:', projectId);
          console.log('ID da sessão de votação:', votingSessionId);
          console.log('Respostas:', responses.responses);
          
          if (!votingSessionId) {
            throw new Error('Voting session ID não definido.');
          }
          const response = await this.$services.answer.createAnswerSession(
            projectId,
            responses.responses,
            votingSessionId
          );
          console.log('Respostas submetidas com sucesso:', response);
          this.snackbarMessage = 'Responses submitted successfully!';
          this.snackbar = true;

          await this.fetchRulesSecondTable();
        } catch (error) {
          console.error('Erro ao submeter respostas:', error);
          this.snackbarErrorMessage = 'Failed to submit responses. Please try again later.';
          this.snackbarError = true;
        }
      }
    },
    
    closePage() {
      this.$router.back();
    },

    async fetchUserRole() {
      try {
        // Exemplo: busca o "role" do membro através de um repositório.
        const member = await this.$repositories.member.fetchMyRole(this.$route.params.id);
        this.user = member;
      } catch (error) {
        console.error("Erro ao buscar o papel do usuário:", error);
      }
    },
    async finalizeSession(session) {
      const projectId = this.$route.params.id;
      try {
        // Atualiza a sessão definindo finish como true
        await this.$services.voting.updateSessionFinish(projectId, session.id);
        
        // Atualiza a sessão localmente (opcional)
        session.finish = true;
        
        this.snackbarMessage = "Sessão finalizada com sucesso!";
        this.snackbar = true;
        
        // Atualiza as tabelas com a sessão atualizada
        await this.fetchRulesSecondTable();
      } catch (error) {
        console.error("Erro ao finalizar a sessão:", error);
        this.snackbarErrorMessage = "Erro ao finalizar a sessão!";
        this.snackbarError = true;
      }
    },
  },
};
</script>