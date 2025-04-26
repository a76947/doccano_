<template>
  <v-card>
    <v-card-title>
      <!-- Se não houver regras, exibe uma mensagem -->
      <template v-if="!hasRules">
        <v-alert type="info" dense class="mb-0">
          No Rules found for this project.
        </v-alert>
      </template>
    </v-card-title>

    <v-card-title>
      Regras
    </v-card-title>
    <RulesTable 
      :items="rules"
      :loading="loading"
      @open-create="openCreateDialog" 
      @deleteRule="handleDelete"
      @editRule="handleEditRule" 
    />

    <!-- Botões -->
    <div class="mt-4">
      <v-btn color="success" @click="openCreateDialog">
        New Question
      </v-btn>
      <v-btn v-if="isAdmin" color="info" class="ml-2" @click="openCalendar">
        Log Data
      </v-btn>
    </div>

    <v-expansion-panels>
      <v-expansion-panel>
        <v-expansion-panel-header>
          Segunda Tabela de Regras
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <StringTableWithResponse 
            :items="rulesSecondTable"
            :loading="loadingSecondTable"
            @onSubmit="submitResponses"
          />
        </v-expansion-panel-content>
      </v-expansion-panel>
    </v-expansion-panels>

    <!-- Overlay para criar uma pergunta -->
    <v-dialog v-model="dialogCreateQuestion" max-width="500px">
      <v-card>
        <v-card-title class="headline">Criar Pergunta</v-card-title>
        <v-card-text class="pa-4">
          <v-textarea
            v-model="newQuestion"
            label="Digite a pergunta"
            :error="showErrors && !newQuestion"
            :error-messages="showErrors && !newQuestion ? ['* Campo obrigatório'] : []"
            required
          />
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn text @click="closeDialog">Cancel</v-btn>
          <v-btn color="primary" text @click="submitQuestion">
            Submit
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Novo Overlay para o Calendário e Relógio -->
    <v-dialog v-model="dialogCalendar" max-width="600px">
      <v-card>
        <v-card-title class="headline">Select Date & Time to end Votation</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="6">
              <v-date-picker v-model="selectedDate"></v-date-picker>
            </v-col>
            <v-col cols="6">
              <v-time-picker v-model="selectedTime" format="24hr"></v-time-picker>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="closeCalendar">Cancel</v-btn>
          <v-btn color="primary" text @click="confirmCalendar">Confirm</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

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
  </v-card>
</template>

<script>
import RulesTable from '~/components/rules/rulesTable.vue';
import StringTableWithResponse from '~/components/rules/stringTableWithResponse.vue';

export default {
  components: { RulesTable, StringTableWithResponse },
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],
  data() {
    return {
      rules: [],
      rulesSecondTable: [],
      snackbar: false,
      snackbarMessage: '',
      snackbarError: false,
      snackbarErrorMessage: '',
      loading: true,
      newQuestion: '',
      showErrors: false,
      dialogCreateQuestion: false,
      dialogCalendar: false,
      selectedDate: null,          // Data selecionada no calendário
      selectedTime: null,          // Horário selecionado
      user: {},
      validSession: null,
    };
  },
  computed: {
    projectId() {
      return this.$route.params.id;
    },
    hasRules() {
      return this.rules && this.rules.length > 0;
    },
    isAdmin() {
      return this.user && this.user.isProjectAdmin;
    },
  },
  async created() {
    try {
      const member = await this.$repositories.member.fetchMyRole(this.projectId);
      this.user = member;
    } catch (error) {
      console.warn("Erro ao buscar o usuário:", error);
    }
  },
  mounted() {
    this.fetchRules();
    this.responseTable();
  },
  methods: {
    async updateExpiredSessions() {
      try {
        const response = await this.$services.voting.list(this.projectId);
        const sessions = response.voting_sessions || [];
        const now = new Date();
        for (const session of sessions) {
          // Converte a end_date para um objeto Date
          const endDate = new Date(session.vote_end_date);
          if (endDate < now && !session.finish) {
            await this.$services.voting.updateSessionFinish(this.projectId, session.id);
          }
        }
      } catch (error) {
        console.error('Erro ao atualizar sessões expiradas:', error);
      }
    },

    async responseTable() {
      await this.updateExpiredSessions();
      await this.fetchRulesSecondTable();
    },

    async submitResponses(responses) {
      console.log('Respostas recebidas da StringTableWithResponse:', responses);
      if (responses.incomplete) {
        this.snackbarErrorMessage = 'Please answer all questions before submitting.';
        this.snackbarError = true;
      } else {
        console.log('Respostas completas:', responses.responses);
        await this.submitAnswers(this.validSession.id, 
        this.projectId, responses.responses); // <--- CORRETO AGORA
        this.snackbarMessage = 'Responses submitted successfully!';
        this.snackbar = true;
      }
    },

    async submitAnswers(votingSessionId, projectId, responses) {
      console.log('Submetendo respostas:', responses);
      console.log('ID da votação:', votingSessionId);
      console.log('ID do projeto:', projectId);
      try {
        
        const response = await this.$services.answer.createAnswerSession(
          projectId,
          responses,
          votingSessionId
        );
        console.log('Respostas submetidas com sucesso:', response);
        this.snackbarMessage = 'Responses submitted successfully!';
        this.snackbar = true;
      } catch (error) {
          console.error('Erro ao submeter respostas:', error);
          this.snackbarErrorMessage = 'Failed to submit responses. Please try again later.';
          this.snackbarError = true;
      }
    },

    handleEditRule({ id, editedText }) {
      console.log('Edit recebido no index para id:', id, 'com o texto:', editedText);
      this.$services.rules.editRule(this.projectId, id, editedText)
        .then(response => {
          console.log('API edit response:', response);
          this.snackbarMessage = 'Rule updated successfully!';
          this.snackbar = true;
          this.fetchRules();
        })
        .catch(err => {
          console.error('Error editing rule:', err.response || err);
          if (err.response && err.response.data && err.response.data.error) {
            this.snackbarErrorMessage = err.response.data.error;
          } else {
            this.snackbarErrorMessage = 'Failed to update rule. Please try again later.';
          }
          this.snackbarError = true;
        });
    },
    async handleDelete(id) {
      console.log('ID recebido para remoção no index:', id);
      try {
        const response = await this.$services.rules.deleteRule(this.projectId, id);
        if (response && (response.status === 200 || response.message)) {
          console.log('API delete response:', response);
          this.snackbarMessage = 'Rule deleted successfully!';
          this.snackbar = true;
        } else {
          throw new Error('No response returned from delete request.');
        }
      } catch (err) {
        console.error('Error deleting rule:', err.response || err);
        if (err.response && err.response.data && err.response.data.error) {
          this.snackbarErrorMessage = err.response.data.error;
        } else {
          this.snackbarErrorMessage = 'Failed to delete rule. Please try again later.';
        }
        this.snackbarError = true;
      } finally {
        this.fetchRules();
      }
    },
    openCreateDialog() {
      this.dialogCreateQuestion = true;
    },
    closeDialog() {
      this.dialogCreateQuestion = false;
      this.newQuestion = '';
      this.showErrors = false;
    },
    async submitQuestion() {
      if (!this.newQuestion) {
        this.showErrors = true;
        return;
      }
      try {
        const response = await this.$services.rules.createRule(this.projectId, this.newQuestion);
        console.log("Pergunta submetida:", this.newQuestion);
        console.log('API response:', response);
        this.snackbarMessage = 'Question submitted successfully!';
        this.snackbar = true;
        this.fetchRules();
        this.newQuestion = '';
        this.closeDialog();
      } catch (err) {
        console.error('Error submitting question:', err.response || err);
        if (err.response && err.response.data && err.response.data.error) {
          this.snackbarErrorMessage = err.response.data.error;
        } else {
          this.snackbarErrorMessage = 'Failed to submit question. Please try again later.';
        }
        this.snackbarError = true;
      } finally {
        this.showErrors = false;
      }
    },
    async fetchRules() {
      try {
        const response = await this.$services.rules.listRulesToSubmit(this.projectId);
        console.log('API response:', response);
        if (!response.rules || response.rules.length === 0) {
          this.snackbarErrorMessage = 'No Rules found for this project.';
          this.snackbarError = true;
          this.rules = [];
        } else {
          this.rules = [...response.rules];
        }
      } catch (err) {
        console.error('Error fetching rules:', err);
        this.snackbarErrorMessage = 'Failed to fetch rules. Please try again later.';
        this.snackbarError = true;
      } finally {
        this.loading = false;
      }
    },
    async fetchRulesSecondTable() {
      try {
        const response = await this.$services.voting.list(this.projectId);
        console.log('API response votações:', response);
        
        const sessions = response.voting_sessions || [];
        
        // Seleciona o primeiro tuplo cuja sessão não esteja finalizada (finish !== true)
        this.validSession = sessions.find(session => session.finish !== true);
        
        if (this.validSession && this.validSession.questions 
        && this.validSession.questions.length) {
          // Atribui rulesSecondTable com as regras (strings) do primeiro tuplo válido
          this.rulesSecondTable = this.validSession.questions;
          console.log('Sessão válida encontrada:', this.validSession.id);
          console.log('Regras extraídas do primeiro tuplo não finalizado:', this.rulesSecondTable);
        } else {
          this.snackbarErrorMessage = 'No valid session found to extract rules.';
          this.snackbarError = true;
          this.rulesSecondTable = [];
        }
      } catch (err) {
        console.error('Error fetching rules:', err);
        this.snackbarErrorMessage = 'Failed to fetch rules. Please try again later.';
        this.snackbarError = true;
      } finally {
        this.loadingSecondTable = false;
      }
    },
    openCalendar() {
      this.dialogCalendar = true;
      if (!this.selectedDate) {
        this.selectedDate = new Date().toISOString().substr(0, 10);
      }
      if (!this.selectedTime) {
        // Formata a hora atual (ex: "14:30")
        const now = new Date();
        const hour = now.getHours().toString().padStart(2, '0');
        const minute = now.getMinutes().toString().padStart(2, '0');
        this.selectedTime = `${hour}:${minute}`;
      }
    },
    closeCalendar() {
      this.dialogCalendar = false;
    },

    async createVotingSession() {
      const voteEndDate = new Date(`${this.selectedDate}T${this.selectedTime}:00Z`).toISOString();
      
      // Extrai somente o texto da regra e ignora demais propriedades (como os ids)
      console.log("Vote end date:", this.rules);
      const questionsList = this.rules.map(rule => rule.regra ? rule.regra : '');
      console.log("Questions list:", questionsList);
      
      try {
        console.log("Criando nova sessão de votação com vote_end_date:", voteEndDate, "e questions:", questionsList);
        const response = await this.$services.voting.createVotingSession(
          this.projectId, 
          voteEndDate, 
          questionsList);
        console.log("Voting session created:", response);
        this.snackbarMessage = "Voting session created successfully!";
        this.snackbar = true;
        
        // Após criar a sessão, elimina cada regra da base de dados.
        for (const rule of this.rules) {
          try {
            await this.$services.rules.deleteRule(this.projectId, rule.id);
            console.log(`Regra com id ${rule.id} removida com sucesso.`);
          } catch (err) {
            console.error(`Erro ao remover a regra com id ${rule.id}:`, err);
          }
        }
        // Atualiza a lista local para refletir que todas as regras foram removidas.
        this.rules = [];
        
      } catch (err) {
        console.error("Error creating voting session:", err);
        this.snackbarErrorMessage = "Failed to create voting session.";
        this.snackbarError = true;
      }
    },
    confirmCalendar() {
      console.log('Selected date:', this.selectedDate);
      console.log('Selected time:', this.selectedTime);
      this.createVotingSession();
      this.closeCalendar();
    },
    toVotation() {
      // Se o método toVotation() era o handler anterior, agora ele chama openCalendar()
      this.openCalendar();
    },
  },
};
</script>