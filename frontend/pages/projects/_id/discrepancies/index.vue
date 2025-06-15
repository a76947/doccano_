<template>
  <v-card>
    <v-card-title>
      <v-row align="center">
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="search"
            label="Search"
            prepend-icon="mdi-magnify"
            single-line
            hide-details
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6" class="text-right">
          <v-btn-toggle
            v-model="sortOrder"
            mandatory
            @change="updateSort"
          >
            <v-btn small value="desc">
              <v-icon>mdi-sort-descending</v-icon>
              Descending
            </v-btn>
            <v-btn small value="asc">
              <v-icon>mdi-sort-ascending</v-icon>
              Ascending
            </v-btn>
          </v-btn-toggle>
        </v-col>
      </v-row>

      <!-- Perspective Filters -->
      <v-row class="mt-2">
        <v-col cols="12" md="10" lg="8" class="ml-auto">
          <v-btn
            color="primary"
            class="filter-btn"
            @click="showFilterDialog = true"
          >
            <v-icon left>mdi-filter-variant</v-icon>
            Perspective Filters
            <v-chip
              v-if="hasActiveFilters"
              color="error"
              small
              class="ml-2"
            >
              {{ activeFiltersCount }}
            </v-chip>
          </v-btn>
        </v-col>
      </v-row>
    </v-card-title>

    <!-- Filter Dialog -->
    <v-dialog
      v-model="showFilterDialog"
      max-width="900px"
      content-class="filter-dialog"
    >
      <v-card class="filter-dialog-card">
        <v-card-title class="filter-dialog-title">
          <div class="d-flex align-center">
            <v-icon left color="primary" class="mr-2">mdi-filter-variant</v-icon>
            <span class="text-h6">Perspective Filters</span>
          </div>
          <v-spacer></v-spacer>
          <v-btn
            v-if="hasActiveFilters"
            color="error"
            text
            class="clear-filters-btn"
            @click="clearFilters"
          >
            <v-icon small left>mdi-close</v-icon>
            Clear Filters
          </v-btn>
          <v-btn
            icon
            @click="showFilterDialog = false"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-card-text class="filter-dialog-content">
          <v-row>
            <v-col v-for="(group, groupIndex) in perspectiveGroups" 
              :key="groupIndex" 
              cols="12" 
              md="6"
            >
              <v-card flat class="perspective-filter-card">
                <v-card-title class="py-2">
                  <v-icon left color="primary" class="mr-2">mdi-account-group</v-icon>
                  <span class="text-subtitle-1 font-weight-medium">{{ group.name }}</span>
                </v-card-title>
                <v-divider class="mx-4"></v-divider>
                <v-card-text class="py-2">
                  <div v-for="question in group.questions" :key="question.id" class="mb-4">
                    <div class="d-flex align-center mb-1">
                      <v-icon small color="primary" class="mr-2">mdi-help-circle</v-icon>
                      <div class="text-subtitle-2 font-weight-medium">{{ question.question }}</div>
                    </div>
                    
                    <!-- String/Int Options -->
                    <v-select
                      v-if="question.data_type === 'string' || question.data_type === 'int'"
                      v-model="selectedAnswers[question.id]"
                      :items="question.options"
                      :label="'Select ' + question.question"
                      multiple
                      chips
                      deletable-chips
                      clearable
                      outlined
                      dense
                      class="mt-1"
                      @change="applyFilters"
                    >
                      <template #selection="{ item, index }">
                        <v-chip
                          v-if="index < 2"
                          color="primary"
                          outlined
                          x-small
                          class="mr-1"
                        >
                          {{ item }}
                        </v-chip>
                        <span
                          v-else-if="index === 2"
                          class="grey--text text-caption pl-2"
                        >
                          (+{{ selectedAnswers[question.id].length - 2 }} others)
                        </span>
                      </template>
                    </v-select>

                    <!-- Boolean Options -->
                    <v-radio-group
                      v-else-if="question.data_type === 'boolean'"
                      v-model="selectedAnswers[question.id]"
                      row
                      dense
                      class="mt-1"
                      @change="applyFilters"
                    >
                      <v-radio
                        :value="true"
                        color="primary"
                        class="mr-4"
                      >
                        <template #label>
                          <div class="d-flex align-center">
                            <v-icon small color="success" class="mr-1">mdi-check-circle</v-icon>
                            <span class="text-caption">Yes</span>
                          </div>
                        </template>
                      </v-radio>
                      <v-radio
                        :value="false"
                        color="primary"
                      >
                        <template #label>
                          <div class="d-flex align-center">
                            <v-icon small color="error" class="mr-1">mdi-close-circle</v-icon>
                            <span class="text-caption">No</span>
                          </div>
                        </template>
                      </v-radio>
                    </v-radio-group>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>

        <v-card-actions class="filter-dialog-actions">
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            @click="showFilterDialog = false"
          >
            Close
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Data Table -->
    <v-data-table
      :headers="headers"
      :items="filteredDiscrepancies"
      :search="search"
      :loading="loading"
      :items-per-page="10"
      class="elevation-1"
    >
      <template #[`item.text`]="{ item }">
        <div class="text-truncate" style="max-width: 300px;">
          {{ item.text }}
        </div>
      </template>

      <template #[`item.labels`]="{ item }">
        <v-simple-table dense class="dataset-table">
          <template #default>
            <thead>
              <tr>
                <th class="dataset-header">Dataset Label</th>
                <th class="dataset-header">Percentage</th>
                <th class="dataset-header">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(percentage, label) in sortedPercentages(item.percentages)" 
              :key="label" class="dataset-row">
                <td class="dataset-cell">{{ label }}</td>
                <td class="dataset-cell">{{ percentage.toFixed(2) }}%</td>
                <td class="dataset-cell">
                  <v-chip
                    :color="percentage >= 70 ? 'success' : 'error'"
                    small
                    class="status-chip"
                  >
                    {{ percentage >= 70 ? 'Agreement' : 'Disagreement' }}
                  </v-chip>
                </td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </template>

      <template #[`item.is_discrepancy`]="{ item }">
        <v-chip
          :color="item.is_discrepancy ? 'error' : 'success'"
          small
          class="status-chip"
        >
          {{ item.is_discrepancy ? 'Disagreement' : 'Agreement' }}
        </v-chip>
      </template>

      <template #[`item.max_percentage`]="{ item }">
        <span class="percentage-value">{{ item.max_percentage.toFixed(2) }}%</span>
      </template>

      <!-- Novo botão Discussão -->
      <template #[`item.actions`]="{ item }">
        <v-btn small color="primary" @click="goToDiscussion(item)">
          Discussão
        </v-btn>
      </template>
    </v-data-table>

    <!-- Snackbars -->
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
import { usePerspectiveApplicationService } from '@/services/application/perspective/perspectiveApplicationService'

export default {
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  data() {
    return {
      discrepancies: [],
      perspectiveGroups: [],
      selectedAnswers: {},
      showFilterDialog: false,
      snackbar: false,
      snackbarMessage: '',
      snackbarError: false,
      snackbarErrorMessage: '',
      loading: true,
      sortOrder: 'desc',
      search: '',
      headers: [
        { text: 'Text', value: 'text', sortable: true },
        { text: 'Dataset Labels', value: 'labels', sortable: false },
        { text: 'Overall Status', value: 'is_discrepancy', sortable: true },
        { text: 'Max Percentage', value: 'max_percentage', sortable: true },
        { text: 'Discussão', value: 'actions', sortable: false }
      ]
    };
  },

  computed: {
    projectId() {
      return this.$route.params.id;
    },
    sortedDiscrepancies() {
      return [...this.discrepancies].sort((a, b) => {
        return this.sortOrder === 'asc' ? a.max_percentage - b.max_percentage : 
        b.max_percentage - a.max_percentage;
      });
    },
    filteredDiscrepancies() {
  let filtered = [...this.discrepancies];

  const hasPerspectiveFilters = Object.keys(this.selectedAnswers).length > 0;

  if (hasPerspectiveFilters) {
    filtered = filtered.filter(discrepancy => {
      const perspectiveAnswers = discrepancy.perspective_answers || {};
      const annotators = discrepancy.annotators || [];

      for (const [selectedQuestionId, selectedValue] of Object.entries(this.selectedAnswers)) {
        if (
          selectedValue === null ||
          selectedValue === undefined ||
          (Array.isArray(selectedValue) && selectedValue.length === 0)
        ) continue;

        let matchFound = false;

        for (const group of Object.values(perspectiveAnswers)) {
          for (const [questionId, answersByAnnotator] of Object.entries(group)) {
            if (questionId !== selectedQuestionId) continue;

            for (const annotatorId of annotators) {
              const rawAnswer = answersByAnnotator[annotatorId];

              if (rawAnswer !== undefined) {
                if (Array.isArray(selectedValue)) {
                  if (selectedValue.includes(rawAnswer)) {
                    matchFound = true;
                    break;
                  }
                } else {
                  // booleano (corrigido!)
                  const answerStr = rawAnswer.toLowerCase?.();
                  const answerBool =
                    answerStr === 'true' || answerStr === 'yes'
                      ? true
                      : answerStr === 'false' || answerStr === 'no'
                      ? false
                      : null;

                  if (answerBool === null) continue;

                  if (selectedValue === answerBool) {
                    matchFound = true;
                    break;
                  }
                }
              }
            }
            if (matchFound) break;
          }
          if (matchFound) break;
        }

        if (!matchFound) return false;
      }

      return true;
    });
  }

  if (this.sortOrder) {
    filtered.sort((a, b) =>
      this.sortOrder === 'asc'
        ? a.max_percentage - b.max_percentage
        : b.max_percentage - a.max_percentage
    );
  }

  return filtered;
}
,
    hasActiveFilters() {
      return Object.values(this.selectedAnswers).some(values => {
        if (Array.isArray(values)) {
          return values.length > 0
        }
        return values !== null && values !== undefined
      })
    },
    activeFiltersCount() {
      return Object.values(this.selectedAnswers).reduce((count, values) => {
        if (Array.isArray(values)) {
          return count + values.length;
        }
        return count + (values !== null && values !== undefined ? 1 : 0);
      }, 0);
    }
  },

  async created() {
    this.loadSelectedAnswers();
    await this.fetchDiscrepancies();
    await this.fetchPerspectiveGroups();
  },

  watch: {
    selectedAnswers: {
      handler(newVal) {
        localStorage.setItem(`perspectiveFilters-${this.projectId}`, JSON.stringify(newVal));
      },
      deep: true
    }
  },

  methods: {
    loadSelectedAnswers() {
      const savedFilters = localStorage.getItem(`perspectiveFilters-${this.projectId}`);
      if (savedFilters) {
        try {
          this.selectedAnswers = JSON.parse(savedFilters);
        } catch (e) {
          console.error("Error parsing saved perspective filters:", e);
          this.selectedAnswers = {};
        }
      }
    },
    async fetchDiscrepancies() {
      try {
        const response = await this.$services.discrepancy.listDiscrepancie(this.projectId);
        this.discrepancies = response.discrepancies || [];
      } catch (err) {
        console.error('Error fetching discrepancies:', err);
        this.snackbarErrorMessage = 'Failed to fetch discrepancies. Please try again later.';
        this.snackbarError = true;
      } finally {
        this.loading = false;
      }
    },

    async fetchPerspectiveGroups() {
      try {
        const service = usePerspectiveApplicationService();
        const response = await service.listPerspectiveGroups(this.projectId);
        this.perspectiveGroups = response.results || [];
      } catch (err) {
        console.error('Error fetching perspective groups:', err);
        this.snackbarErrorMessage = 'Failed to fetch perspective groups.';
        this.snackbarError = true;
      }
    },

    applyFilters() {
      console.log('Applying filters...')
      // Filters are automatically applied via reactivity when selectedAnswers changes
    },

    updateSort() {
      // A ordenação é feita automaticamente pelo computed property
    },

    sortedPercentages(percentages) {
      const sorted = Object.entries(percentages).sort((a, b) => {
        return this.sortOrder === 'asc' ? a[1] - b[1] : b[1] - a[1];
      });
      return Object.fromEntries(sorted);
    },

    clearFilters() {
      console.log('Clearing filters...')
      this.selectedAnswers = {}
      this.$nextTick(() => {
        this.applyFilters()
      })
    },

    goToDiscussion(item) {
      this.$router.push(this.localePath(`/projects/${this.projectId}/discrepancies/${item.id}`))
    }
  }
};
</script>

<style scoped>
.v-data-table {
  width: 100%;
}

.dataset-table {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  margin: 8px 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.dataset-header {
  background-color: #f5f5f5 !important;
  font-weight: 600 !important;
  color: #424242 !important;
  padding: 8px 16px !important;
  border-bottom: 2px solid #e0e0e0 !important;
}

.dataset-row {
  border-bottom: 1px solid #e0e0e0;
}

.dataset-row:last-child {
  border-bottom: none;
}

.dataset-cell {
  padding: 12px 16px !important;
  font-size: 0.9rem;
}

.status-chip {
  font-weight: 500;
  min-width: 100px;
  justify-content: center;
}

.percentage-value {
  font-weight: 600;
  color: #424242;
}

/* Estilo para o texto truncado */
.text-truncate {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

/* Estilo para a tabela principal */
.v-data-table ::v-deep th {
  font-weight: 600 !important;
  color: #424242 !important;
  background-color: #f5f5f5 !important;
}

.v-data-table ::v-deep td {
  padding: 16px !important;
}

/* Estilo para as linhas alternadas */
.v-data-table ::v-deep tbody tr:nth-of-type(odd) {
  background-color: #fafafa;
}

/* Estilo para hover nas linhas */
.v-data-table ::v-deep tbody tr:hover {
  background-color: #f5f5f5;
}

.filter-btn {
  background: linear-gradient(145deg, #e3f2fd, #bbdefb) !important;
  color: #1976d2 !important;
  border-radius: 24px;
  padding: 0 24px;
  height: 40px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  display: flex;
  justify-content: center;
  align-items: center;
}

.filter-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.filter-dialog-card {
  border-radius: 16px;
  overflow: hidden;
}

.filter-dialog-title {
  background: linear-gradient(145deg, #e3f2fd, #bbdefb);
  padding: 16px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.filter-dialog-content {
  padding: 24px;
  max-height: 70vh;
  overflow-y: auto;
}

.filter-dialog-actions {
  padding: 16px 24px;
  background: #f5f5f5;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.perspective-filter-card {
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  transition: all 0.3s ease;
  background: linear-gradient(145deg, #ffffff, #fafafa);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
  margin-bottom: 16px;
}

.perspective-filter-card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.perspective-filter-card .v-card-title {
  background: linear-gradient(145deg, #e8f5e9, #c8e6c9);
  border-radius: 12px 12px 0 0;
  padding: 12px 16px;
}

.perspective-filter-card .v-card-title .v-icon {
  color: #2e7d32;
}

.perspective-filter-card .v-card-text {
  padding: 16px;
}

.v-select ::v-deep .v-select__selections {
  flex-wrap: nowrap;
}

.v-select ::v-deep .v-chip {
  margin: 2px;
  background: linear-gradient(145deg, #e3f2fd, #bbdefb) !important;
  border: none !important;
}

.v-radio ::v-deep .v-radio__label {
  font-size: 0.9rem;
  color: rgba(0, 0, 0, 0.87);
}

.clear-filters-btn {
  background: linear-gradient(145deg, #ffebee, #ffcdd2) !important;
  color: #c62828 !important;
  border-radius: 16px;
  padding: 0 16px;
  height: 32px;
  font-weight: 500;
}

.clear-filters-btn:hover {
  background: linear-gradient(145deg, #ffcdd2, #ef9a9a) !important;
  transform: translateY(-1px);
}

/* Add styles for the filter groups */
.perspective-filter-card .text-subtitle-1 {
  color: #1b5e20;
  font-weight: 600;
}

.perspective-filter-card .text-subtitle-2 {
  color: #2e7d32;
  font-weight: 500;
}

/* Style for the select and radio inputs */
.v-select ::v-deep .v-input__slot {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}

.v-radio-group ::v-deep .v-radio {
  margin-right: 24px;
}

.v-radio-group ::v-deep .v-radio__label {
  color: #424242;
}

/* Custom scrollbar for the dialog content */
.filter-dialog-content::-webkit-scrollbar {
  width: 8px;
}

.filter-dialog-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.filter-dialog-content::-webkit-scrollbar-thumb {
  background: #bbdefb;
  border-radius: 4px;
}

.filter-dialog-content::-webkit-scrollbar-thumb:hover {
  background: #90caf9;
}
</style>