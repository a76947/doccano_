<template>
  <v-card>
    <v-card-title>
      <!-- Se não houver discrepâncias, exibe uma mensagem -->
      <template v-if="!hasDiscrepancies">
        <v-alert type="info" dense class="mb-0">
          No discrepancies found for this project.
        </v-alert>
      </template>
    </v-card-title>

    <DiscrepanciesTable 
      :items="discrepancies"
      :loading="loading"
      @open-create="openCreateDialog" 
    />

    <!-- Overlay para criar perguntas -->
    <v-dialog v-model="dialogCreateQuestion" max-width="500px">
      <v-card>
        <v-card-title class="headline">Criar Perguntas</v-card-title>
        <v-card-text class="pa-4">
          <!-- Rótulo para o texto -->
          <p class="font-weight-bold mb-2">Text:</p>
          <!-- Exibe o texto minimizado ou completo -->
          <p class="mb-4">
            {{
              showFullText
                ? discrepancyText
                : truncateText(discrepancyText, 100)
            }}
          </p>
          <!-- Botão para alternar a visualização -->
          <div v-if="discrepancyText.length > 100" class="mt-2 mb-4">
            <v-btn text small @click="toggleFullText">
              {{ showFullText ? 'Ver menos' : 'Ver mais' }}
            </v-btn>
          </div>

          <!-- Exibe as porcentagens e as tags juntas com espaçamento -->
          <div class="d-flex flex-wrap mt-2 mb-4">
            <!-- Percentagens -->
            <div v-if="selectedItem && selectedItem.percentages" class="mr-4">
              <v-chip
                v-for="(value, key, idx) in selectedItem.percentages"
                :key="`perc-${idx}`"
                class="ma-1"
                color="blue lighten-2"
                text-color="white"
              >
                {{ key }}: {{ value }}
              </v-chip>
            </div>
            <!-- Tags -->
            <div v-if="selectedItem && selectedItem.tags && selectedItem.tags.length" class="ml-2">
              <p class="font-weight-bold mb-2">Tags:</p>
              <v-chip
                v-for="(tag, idx) in tags"
                :key="`tag-${idx}`"
                class="ma-1"
                color="green lighten-2"
                text-color="white"
              >
                {{ tag }}
              </v-chip>
            </div>
          </div>

          <!-- Seção para adicionar novas perguntas -->
          <div class="mt-4 mb-4">
            <v-btn color="secondary" @click="toggleQuestionInput">
              Criar Pergunta
            </v-btn>
          </div>
          <!-- Campo para inserir nova pergunta -->
          <div v-if="showQuestionInput" class="mt-4 mb-4">
            <v-textarea
              v-model="newQuestion"
              label="Digite a nova pergunta"
              :error="showErrors && !newQuestion"
              :error-messages="showErrors && !newQuestion ? ['* Campo obrigatório'] : []"
              required
            />
            <v-btn color="primary" class="mt-2" @click="addQuestion">
              Adicionar Pergunta
            </v-btn>
          </div>
          <!-- Lista das perguntas adicionadas -->
          <div v-if="newQuestions.length" class="mt-4">
            <div v-for="(question, idx) in newQuestions" :key="idx" class="mb-2">
              <v-chip close @click:close="removeQuestion(idx)">
                {{ question }}
              </v-chip>
            </div>
          </div>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn text @click="closeDialog">Cancel</v-btn>
          <v-btn color="primary" text @click="submitQuestion">
            Salvar
          </v-btn>
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
import DiscrepanciesTable from '~/components/discrepancies/discrepanciesTable.vue';

export default {
  components: { DiscrepanciesTable },
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],
  data() {
    return {
      discrepancies: [],
      snackbar: false,
      snackbarMessage: '',
      snackbarError: false,
      snackbarErrorMessage: '',
      loading: true,
      sortOrder: 'asc',
      dialogCreateQuestion: false,
      discrepancyText: '',
      tags: [],
      newQuestion: '',
      newQuestions: [],
      showErrors: false,
      showQuestionInput: false,
      showFullText: false,
      selectedItem: null,
    };
  },
  computed: {
    projectId() {
      return this.$route.params.id;
    },
    hasDiscrepancies() {
      return this.discrepancies && this.discrepancies.length > 0;
    },
  },
  mounted() {
    this.fetchDiscrepancies();
  },
  methods: {
    async fetchDiscrepancies() {
      try {
        const response = await this.$services.discrepancy.listDiscrepancie(
          this.projectId
        );
        console.log('API response:', response);
        this.discrepancies = response.discrepancies || [];
      } catch (err) {
        console.error('Error fetching discrepancies:', err);
        this.snackbarErrorMessage =
          'Failed to fetch discrepancies. Please try again later.';
        this.snackbarError = true;
      } finally {
        this.loading = false;
      }
    },
    openCreateDialog(item) {
      this.selectedItem = item;
      this.discrepancyText = item.text;
      this.tags = Object.keys(item.percentages);
      this.newQuestion = '';
      this.newQuestions = [];
      this.showQuestionInput = false;
      this.showFullText = false;
      this.dialogCreateQuestion = true;
    },
    toggleFullText() {
      this.showFullText = !this.showFullText;
    },
    toggleQuestionInput() {
      this.showQuestionInput = !this.showQuestionInput;
      if (this.showQuestionInput) {
        this.newQuestion = '';
      }
    },
    addQuestion() {
      this.showErrors = true;
      if (!this.newQuestion) return;
      this.newQuestions.push(this.newQuestion);
      this.newQuestion = '';
      this.showQuestionInput = false;
      this.showErrors = false;
    },
    removeQuestion(idx) {
      this.newQuestions.splice(idx, 1);
    },
    submitQuestion() {
      if (this.newQuestions.length === 0) {
        this.showErrors = true;
        return;
      }
      console.log('Salvando novas perguntas:', this.newQuestions);
      this.snackbarMessage = 'Perguntas criadas com sucesso!';
      this.snackbar = true;
      // Envie newQuestions para a API se necessário.
      this.closeDialog();
    },
    closeDialog() {
      this.dialogCreateQuestion = false;
      this.newQuestion = '';
      this.newQuestions = [];
      this.showErrors = false;
      this.showQuestionInput = false;
      this.showFullText = false;
      this.selectedItem = null;
    },
    truncateText(text, maxLength) {
      return text.length > maxLength
        ? text.substring(0, maxLength) + '...'
        : text;
    },
    toggleSortOrder() {
      this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
    },
    sortedPercentages(percentages) {
      const sorted = Object.entries(percentages).sort((a, b) => {
        return this.sortOrder === 'asc' ? a[1] - b[1] : b[1] - a[1];
      });
      return Object.fromEntries(sorted);
    },
  },
};
</script>

<style scoped>
.discrepancies-page {
  font-family: Arial, sans-serif;
  padding: 20px;
}

.loading {
  font-size: 18px;
  color: #666;
}

.no-data {
  font-size: 16px;
  color: #999;
}

.discrepancy-item {
  margin-bottom: 20px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
}

.discrepancy-item p {
  margin: 5px 0;
}

.discrepancy-item ul {
  margin: 5px 0 0 20px;
}
</style>