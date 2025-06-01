<template>
  <v-card>
    <v-card-title>
      Segunda Tabela de Regras
    </v-card-title>
    <v-expansion-panels>
      <v-expansion-panel v-for="(session, index) in rulesSecondTable" :key="index">
        <v-expansion-panel-header>
          Sessão {{ index + 1 }}
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <StringTableWithResponse 
            :items="session.questions"
            :loading="loadingSecondTable"
            @onSubmit="(res) => submitResponses(session, res)"
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

export default {
  components: { StringTableWithResponse },
  data() {
    return {
      rulesSecondTable: [],
      loadingSecondTable: true,
      validSession: null,
      snackbar: false,
      snackbarMessage: '',
      snackbarError: false,
      snackbarErrorMessage: '',
    };
  },
  created() {
    this.fetchRulesSecondTable();
  },
  methods: {
    async fetchRulesSecondTable() {
      const projectId = this.$route.params.id;
      try {
        // Obtém as sessões de votação do projeto
        const response = await this.$services.voting.list(projectId);
        const sessions = response.voting_sessions || [];
        
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
        
        
        const activeSessions = sessions.filter(session => session.finish === false && 
        (!session.userAnswers || session.userAnswers.length === 0));
        

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
  },
};
</script>