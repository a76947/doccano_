<template>
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

<script>
export default {
  name: 'Anotacoes',
  data() {
    return {
      loading: false,
      selectedDatasets: ['all'],
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
      filteredReportData: [],
      perspectiveGroups: [],
      selectedAnswers: {},
      showFilters: false
    };
  },
  methods: {
    handleDatasetChange(_selected) {
      // Lógica para alterar os datasets selecionados
    },
    generateReport() {
      // Lógica para gerar o relatório
    },
    applyFilters() {
      // Lógica para aplicar filtros
    },
    clearFilters() {
      // Lógica para limpar filtros
    },
    getTypeColor(_type) {
      // Lógica para obter a cor do tipo
    },
    getLabelColor(_label) {
      // Lógica para obter a cor do label
    },
    getAgreementColor(_agreement) {
      // Lógica para obter a cor do acordo
    }
  }
};
</script>