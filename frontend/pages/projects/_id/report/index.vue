<template>
  <layout-text>
    <template #header>
      <v-card flat>
        <v-card-title class="d-flex align-center">
          <span class="text-h5">Relatório de Anotações</span>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            :loading="loading"
            @click="generateReport"
          >
            Gerar Relatório
          </v-btn>
        </v-card-title>
      </v-card>
    </template>

    <template #content>
      <v-card>
        <v-card-text>
          <!-- Filtros -->
          <v-row>
            <v-col cols="12" md="6">
              <v-autocomplete
                v-model="selectedDatasets"
                :items="availableDatasets"
                item-text="text"
                item-value="value"
                label="Datasets"
                multiple
                chips
                :loading="loading"
                :disabled="loading"
                @change="handleDatasetChange"
              >
                <template #selection="{ item, index }">
                  <v-chip
                    v-if="index === 0"
                    :color="item.value === 'all' ? 'primary' : 'secondary'"
                    class="mr-2"
                  >
                    {{ item.text }}
                  </v-chip>
                  <span
                    v-else-if="index === 1"
                    class="grey--text text-caption pl-2"
                  >
                    (+{{ selectedDatasets.length - 1 }} outros)
                  </span>
                </template>
              </v-autocomplete>
            </v-col>
            <v-col cols="12" md="6">
              <v-select
                v-model="selectedAgreement"
                :items="agreementOptions"
                item-text="text"
                item-value="value"
                label="Acordo de Anotação"
                :loading="loading"
                :disabled="loading"
                @change="generateReport"
              ></v-select>
            </v-col>
          </v-row>

          <!-- Perspective Filters -->
          <v-row class="mt-2">
            <v-col cols="12" md="8" lg="6" class="ml-auto">
              <v-expansion-panels>
                <v-expansion-panel class="filter-panel">
                  <v-expansion-panel-header class="filter-header">
                    <div class="d-flex align-center">
                      <v-icon left color="primary" class="mr-2">mdi-filter-variant</v-icon>
                      <span class="text-subtitle-2 font-weight-medium">Filtros de Perspectiva</span>
                    </div>
                    <template #actions>
                      <v-btn
                        v-if="hasActiveFilters"
                        small
                        text
                        color="error"
                        class="mr-2 clear-filters-btn"
                        @click.stop="clearFilters"
                      >
                        <v-icon small left>mdi-close</v-icon>
                        Limpar Filtros
                      </v-btn>
                      <v-icon color="primary" small>
                        {{ showFilters ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                      </v-icon>
                    </template>
                  </v-expansion-panel-header>
                  <v-expansion-panel-content class="filter-content">
                    <v-row>
                      <v-col v-for="(group, groupIndex) in perspectiveGroups" 
                        :key="groupIndex" 
                        cols="12" 
                        md="6"
                      >
                        <v-card flat class="perspective-filter-card">
                          <v-card-title class="py-2">
                            <v-icon left color="primary" 
                              class="mr-2">mdi-account-group</v-icon>
                            <span class="text-subtitle-1 font-weight-medium">{{ group.name }}</span>
                          </v-card-title>
                          <v-divider class="mx-4"></v-divider>
                          <v-card-text class="py-2">
                            <div v-for="question in group.questions" 
                            :key="question.id" class="mb-4">
                              <div class="d-flex align-center mb-1">
                                <v-icon small color="primary" 
                                  class="mr-2">mdi-help-circle</v-icon>
                                <div class="text-subtitle-2 
                                font-weight-medium">{{ question.question }}</div>
                              </div>
                              
                              <!-- String/Int Options -->
                              <v-select
                                v-if="question.data_type === 'string' || 
                                question.data_type === 'int'"
                                v-model="selectedAnswers[question.id]"
                                :items="question.options"
                                :label="'Selecionar ' + question.question"
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
                                    (+{{ selectedAnswers[question.id].length - 2 }} outros)
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
                                      <v-icon small color="success" 
                                        class="mr-1">mdi-check-circle</v-icon>
                                      <span class="text-caption">Sim</span>
                                    </div>
                                  </template>
                                </v-radio>
                                <v-radio
                                  :value="false"
                                  color="primary"
                                >
                                  <template #label>
                                    <div class="d-flex align-center">
                                      <v-icon small color="error" 
                                      class="mr-1">mdi-close-circle</v-icon>
                                      <span class="text-caption">Não</span>
                                    </div>
                                  </template>
                                </v-radio>
                              </v-radio-group>
                            </div>
                          </v-card-text>
                        </v-card>
                      </v-col>
                    </v-row>
                  </v-expansion-panel-content>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-col>
          </v-row>

          <!-- Tabela de Resultados -->
          <v-data-table
            :headers="headers"
            :items="filteredReportData"
            :loading="loading"
            class="elevation-1"
          >
            <template #selection="{ item }">
              <v-chip
                :color="getTypeColor(item.type)"
                small
                class="white--text"
              >
                {{ item.type }}
              </v-chip>
            </template>

            <template #[`item.type`]="{ item }">
              <v-chip
                :color="getTypeColor(item.type)"
                small
                class="white--text"
              >
                {{ item.type }}
              </v-chip>
            </template>

            <template #[`item.dataset`]="{ item }">
              <v-chip
                color="primary"
                small
                class="white--text"
              >
                {{ item.dataset }}
              </v-chip>
            </template>

            <template #[`item.label`]="{ item }">
              <v-chip
                :color="getLabelColor(item.label)"
                small
                class="white--text"
              >
                {{ item.label }}
              </v-chip>
            </template>

            <template #[`item.count`]="{ item }">
              <span class="font-weight-medium">
                {{ item.count }}
              </span>
            </template>

            <template #[`item.unique_users`]="{ item }">
              <span class="font-weight-medium">
                {{ item.unique_users }}
              </span>
            </template>

            <template #[`item.agreement`]="{ item }">
              <v-tooltip bottom>
                <template #activator="{ on, attrs }">
                  <v-chip
                    :color="getAgreementColor(item.agreement.percentage)"
                    small
                    class="white--text"
                    v-bind="attrs"
                    v-on="on"
                  >
                    {{ item.agreement.percentage >= 80 ? 'Acordo' : 'Desacordo' }}
                  </v-chip>
                </template>
                <span>
                  Concordância: {{ item.agreement.percentage }}%<br />
                  Total votos: {{ item.agreement.total }}<br />
                  Concordam: {{ item.agreement.agreed }}<br />
                  Discordam: {{ item.agreement.disagreed }}
                </span>
              </v-tooltip>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </template>

  </layout-text>
</template>

<script>
import { mapGetters } from 'vuex'
import LayoutText from '@/components/tasks/layout/LayoutText'
import { usePerspectiveApplicationService } from '@/services/application/perspective/perspectiveApplicationService'

export default {
  name: 'ProjectReport',
  components: {
    LayoutText
  },
  layout: 'project',

  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  data() {
    return {
      loading: false,
      selectedDatasets: ['all'],
      selectedType: 'all',
      selectedAgreement: 'all',
      agreementOptions: [
        { text: 'Todos', value: 'all' },
        { text: 'Concordância', value: 'agreed' },
        { text: 'Desacordo', value: 'disagreed' }
      ],
      availableDatasets: [],
      headers: [
        { text: 'Tipo', value: 'type', sortable: true },
        { text: 'Dataset', value: 'dataset', sortable: true },
        { text: 'Label', value: 'label', sortable: true },
        { text: 'Quantidade', value: 'count', sortable: true },
        { text: 'Usuários Únicos', value: 'unique_users', sortable: true },
        { text: 'Concordância', value: 'agreement', sortable: true }
      ],
      reportData: [],
      datasetSummary: null,
      perspectiveGroups: [],
      selectedAnswers: {},
      showFilters: false
    }
  },

  computed: {
    ...mapGetters('projects', ['project']),
    
    filteredReportData() {
      const selectedDatasetValues = this.selectedDatasets.includes('all')
        ? this.availableDatasets.filter(d => d.value !== 'all').map(d => d.value)
        : this.selectedDatasets

      let filtered = this.reportData.filter(item => {
        const matchesDataset = selectedDatasetValues.includes(item.dataset) || 
          selectedDatasetValues.length === 0 
        const matchesType = this.selectedType === 'all' || 
          item.type === this.selectedType
        return matchesDataset && matchesType
      })

      // Apply perspective filters
      const hasPerspectiveFilters = Object.keys(this.selectedAnswers).length > 0

      if (hasPerspectiveFilters) {
        filtered = filtered.filter(item => {
          const perspectiveAnswers = item.perspective_answers || {};
          const annotators = item.annotators || [];

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
                      // Handle boolean values
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

      return filtered;
    },

    hasActiveFilters() {
      return Object.values(this.selectedAnswers).some(values => {
        if (Array.isArray(values)) {
          return values.length > 0
        }
        return values !== null && values !== undefined
      })
    }
  },

  watch: {
    'project.id': {
      immediate: true,
      handler(newId, oldId) {
        if (newId && newId !== oldId) {
          this.loadAvailableDatasets()
          this.fetchPerspectiveGroups()
        }
      }
    }
  },

  created() {
    // Moved to watch 'project.id' to ensure project is loaded
    // this.loadAvailableDatasets()
  },

  methods: {
    formatDate(date) {
      if (!date) return '';
      return new Date(date).toLocaleDateString();
    },

    async loadAvailableDatasets() {
      this.loading = true
      try {
        console.log("DEBUG: Entrando em loadAvailableDatasets.")
        // Fetching all datasets to populate the dropdown without applying agreement filter
        const response = await this.$repositories.project.fetchReport(this.$route.params.id, {
          datasets: ['all'] 
        })
        console.log("DEBUG: Resposta da API em loadAvailableDatasets:", response.data)
        const availableBackendDatasets = response.data.available_datasets.filter(name => name !== 'all')

        this.availableDatasets = [
          { text: 'Todos os Datasets', value: 'all' },
          ...availableBackendDatasets.map(name => ({ text: name, value: name }))
        ]
        console.log("DEBUG: availableDatasets populado:", this.availableDatasets)
        
        // Ensure 'Todos os Datasets' is selected by default and its value is 'all'
        this.selectedDatasets = ['all']
        console.log("DEBUG: selectedDatasets após loadAvailableDatasets:", this.selectedDatasets)
        return true // Indicate success
      } catch (error) {
        this.$store.dispatch('notification/open', {
          message: 'Nenhum dataset encontrado.',
          type: 'error'
        })
        console.error('Erro ao carregar datasets disponíveis:', error)
        return false // Indicate failure
      } finally {
        this.loading = false
      }
    },

    async fetchPerspectiveGroups() {
      try {
        const service = usePerspectiveApplicationService()
        const response = await service.listPerspectiveGroups(this.$route.params.id)
        this.perspectiveGroups = response.results || []
      } catch (err) {
        console.error('Error fetching perspective groups:', err)
        this.$store.dispatch('notification/open', {
          message: 'Erro ao carregar grupos de perspectiva.',
          type: 'error'
        })
      }
    },

    handleDatasetChange(selected) {
      console.log("DEBUG: handleDatasetChange received (selected from v-autocomplete):", selected);
      console.log("DEBUG: selectedDatasets BEFORE logic:", [...this.selectedDatasets]); // Log a copy to see initial state

      const allOption = 'all';

      // Case 1: User explicitly selected 'Todos os Datasets'
      if (selected.includes(allOption) && !this.selectedDatasets.includes(allOption)) {
          console.log("DEBUG: Case 1 - 'Todos os Datasets' newly selected.");
          this.selectedDatasets = [allOption]; // Only select 'all'
      }
      else if (!selected.includes(allOption) && 
      this.selectedDatasets.includes(allOption) && selected.length > 0) {
          console.log("DEBUG: Case 2 - 'Todos os Datasets' deselected, keeping others.");
          // Keep only the newly selected individual datasets
          this.selectedDatasets = selected.filter(val => val !== allOption);
      }
      else if (selected.includes(allOption) && selected.length > 1) {
          console.log("DEBUG: Case 3 - 'Todos os Datasets' with other individual selections. Deselecting 'all'.");
          // Deselect 'Todos os Datasets' and keep the individual selections
          this.selectedDatasets = selected.filter(val => val !== allOption);
      }
      // Case 4: No items are selected at all, default to 'Todos os Datasets'
      else if (selected.length === 0) {
          console.log("DEBUG: Case 4 - No datasets selected. Defaulting to 'all'.");
          this.selectedDatasets = [allOption];
      }
      // Case 5: Otherwise, just update with the selected items (individual or just 'all' alone)
      else {
          console.log("DEBUG: Case 5 - Standard update with selected items.");
          this.selectedDatasets = selected;
      }
      console.log("DEBUG: selectedDatasets AFTER logic:", [...this.selectedDatasets]); // Log a copy to see final state
    },

    async generateReport() {
      this.loading = true
      try {
        // Ensure availableDatasets is populated before proceeding
        if (this.availableDatasets.length === 0 || (this.availableDatasets.length === 1 && this.availableDatasets[0].value === 'all')) {
            console.log("DEBUG: availableDatasets vazio ou apenas 'all'. Recarregando datasets.")
            const datasetsLoaded = await this.loadAvailableDatasets()
            if (!datasetsLoaded) {
                console.error("Não foi possível carregar os datasets disponíveis. Abortando geração de relatório.")
                return // Abort if loading failed
            }
        }

        let datasetsToSend = []
        console.log("DEBUG: Antes de construir datasetsToSend. selectedDatasets:", this.selectedDatasets)
        console.log("DEBUG: availableDatasets:", this.availableDatasets)

        if (this.selectedDatasets.includes('all')) {
          datasetsToSend = this.availableDatasets
            .filter(d => d.value !== 'all')
            .map(d => d.value)
          console.log("DEBUG: 'Todos os Datasets' selecionado. datasetsToSend construído:", datasetsToSend)
        } else {
          // selectedDatasets já deve conter strings, então não é necessário mapear novamente
          datasetsToSend = this.selectedDatasets
          console.log("DEBUG: Datasets específicos selecionados. datasetsToSend:", datasetsToSend)
        }

        console.log("Datasets selecionados para enviar:", datasetsToSend)

        const perspectiveAnswersForAPI = {}
        for (const [key, val] of Object.entries(this.selectedAnswers)) {
          if (typeof val === 'boolean') {
            perspectiveAnswersForAPI[key] = val ? 'Yes' : 'No'
          } else {
            perspectiveAnswersForAPI[key] = val
          }
        }

        const params = {
          datasets: datasetsToSend,
          annotation_type: this.selectedType,
          agreement: this.selectedAgreement,
          perspective_answers: JSON.stringify(perspectiveAnswersForAPI)
        }

        console.log("Parâmetros enviados para a API:", params)
        const response = await this.$repositories.project.fetchReport(this.$route.params.id, params)
        console.log("Dados recebidos da API:", response.data)
        this.reportData = response.data.report_data.filter(item => item.type !== 'dataset_summary')
        this.datasetSummary = response.data.report_data.find(item => item.type === 'dataset_summary')

        this.$store.dispatch('notification/open', {
          message: 'Relatório gerado com sucesso!',
          type: 'success'
        })
      } catch (error) {
        this.$store.dispatch('notification/open', {
          message: 'Erro ao gerar relatório: ' + (error.response?.data?.error || error.message),
          type: 'error'
        })
        console.error('Erro ao gerar relatório:', error.response?.data || error)
      } finally {
        this.loading = false
      }
    },

    getTypeColor(type) {
      const colors = {
        category: 'blue',
        span: 'green',
        relation: 'purple',
        dataset_summary: 'grey'
      }
      return colors[type] || 'grey'
    },

    getLabelColor(label) {
      // Simple hash to color, can be replaced with a more sophisticated method
      let hash = 0
      for (let i = 0; i < label.length; i++) {
        hash = label.charCodeAt(i) + ((hash << 5) - hash)
      }
      let color = '#'
      for (let i = 0; i < 3; i++) {
        const value = (hash >> (i * 8)) & 0xFF
        color += ('00' + value.toString(16)).substr(-2)
      }
      return color
    },

    getAgreementColor(agreement) {
      if (agreement >= 80) return 'green'
      if (agreement >= 50) return 'orange'
      return 'red'
    },

    getProgressColor(percentage) {
      if (percentage >= 80) return 'success';
      if (percentage >= 50) return 'warning';
      return 'error';
    },

    applyFilters() {
      console.log('Applying filters...')
      this.$forceUpdate()
      this.generateReport()
    },

    clearFilters() {
      console.log('Clearing filters...')
      this.selectedAnswers = {}
      this.$nextTick(() => {
        this.applyFilters()
      })
    }
  }
}
</script>

<style scoped>
.v-data-table {
  margin-top: 1rem;
}

.v-card-title {
  padding: 16px;
}

.v-chip {
  margin-right: 4px;
}

.filter-panel {
  border-radius: 4px;
  overflow: hidden;
  background-color: #f5f5f5;
  margin-right: 16px;
  margin-left: auto;
}

.filter-header {
  background-color: #e0e0e0 !important;
  min-height: 40px !important;
  padding: 0 12px;
}

.filter-header .v-btn {
  min-width: 0;
  padding: 0 8px;
  height: 28px;
  font-size: 0.75rem;
}

.filter-content {
  background-color: #f5f5f5;
  padding: 8px;
}

.perspective-filter-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  transition: all 0.3s ease;
  background-color: white;
}

.perspective-filter-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.v-expansion-panel-content {
  background-color: #f5f5f5;
}

.v-select ::v-deep .v-select__selections {
  flex-wrap: nowrap;
}

.v-select ::v-deep .v-chip {
  margin: 2px;
}

.v-radio ::v-deep .v-radio__label {
  font-size: 0.9rem;
  color: rgba(0, 0, 0, 0.87);
}

.v-card__text {
  padding: 8px 16px;
}

.v-card__title {
  padding: 8px 16px;
}

.v-expansion-panel-header {
  color: rgba(0, 0, 0, 0.87) !important;
  font-size: 0.875rem;
}

.clear-filters-btn {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

.clear-filters-btn:hover {
  background-color: rgba(255, 255, 255, 0.2) !important;
}
</style> 