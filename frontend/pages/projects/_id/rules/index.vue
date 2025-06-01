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
      <!-- Botão existente para criação de votação -->
      <v-btn v-if="isAdmin" color="info" class="ml-2" @click="openCalendar">
        Submit to Vote
      </v-btn>
      <!-- Novo botão para ir para a página voteRules -->
      <v-btn color="primary" class="ml-2" @click="goToVoteRules">
        Vote Rules
      </v-btn>
    </div>

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

    <!-- Overlay para o Calendário e Relógio -->
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

export default {
  components: { RulesTable },
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],
  data() {
    return {
      rules: [],
      snackbar: false,
      snackbarMessage: '',
      snackbarError: false,
      snackbarErrorMessage: '',
      loading: true,
      newQuestion: '',
      showErrors: false,
      dialogCreateQuestion: false,
      dialogCalendar: false,
      selectedDate: null,
      selectedTime: null,
      user: {},
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
  },
  methods: {
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
    openCalendar() {
      this.dialogCalendar = true;
      if (!this.selectedDate) {
        this.selectedDate = new Date().toISOString().substr(0, 10);
      }
      if (!this.selectedTime) {
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
      console.log("Vote end date:", voteEndDate);
      const questionsList = this.rules.map(rule => rule.regra ? rule.regra : '');
      console.log("Questions list:", questionsList);
      try {
        console.log("Criando nova sessão de votação com vote_end_date:", voteEndDate, "e questions:", questionsList);
        const response = await this.$services.voting.createVotingSession(
          this.projectId, 
          voteEndDate, 
          questionsList
        );
        console.log("Voting session created:", response);
        this.snackbarMessage = "Voting session created successfully!";
        this.snackbar = true;
        
        for (const rule of this.rules) {
          try {
            await this.$services.rules.deleteRule(this.projectId, rule.id);
            console.log(`Regra com id ${rule.id} removida com sucesso.`);
          } catch (err) {
            console.error(`Erro ao remover a regra com id ${rule.id}:`, err);
          }
        }
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
      this.openCalendar();
    },
    goToVoteRules() {
      // Redireciona para a página voteRules, preservando o parâmetro id do projeto.
      this.$router.push({ path: `/projects/${this.projectId}/rules/voteRules` });
    },
  },
};
</script>