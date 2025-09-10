<template>
  <layout-text>
    <template #header>
      <v-card flat>
        <v-card-title class="d-flex align-center">
          <span class="text-h5">Relatório de Anotadores</span>
          <v-spacer></v-spacer>
          <v-btn color="primary" :loading="loading" @click="generateReport">
            Gerar Relatório
          </v-btn>
        </v-card-title>
      </v-card>
    </template>

    <template #content>
      <v-card flat>
        <!-- Filtro de Anotadores e Labels -->
        <v-row>
          <v-col cols="12" md="6">
            <v-autocomplete
              v-model="selectedAnnotators"
              :items="annotatorsData"
              item-text="name"
              item-value="name"
              label="Anotadores"
              multiple
              chips
              :loading="loading"
              @change="filterAnnotators"
            ></v-autocomplete>
          </v-col>
          <v-col cols="12" md="6">
            <v-autocomplete
              v-model="selectedLabels"
              :items="availableLabels"
              label="Filtrar por Labels"
              multiple
              chips
              @change="filterAnnotators"
            ></v-autocomplete>
          </v-col>
        </v-row>

        <!-- Perspective Filters -->
        <v-row class="mt-2">
          <v-col cols="12" md="8" lg="6" class="ml-auto">
            <v-expansion-panels>
              <v-expansion-panel class="filter-panel">
                <v-expansion-panel-header class="filter-header">
                  <div class="d-flex align-center">
                    <v-icon left color="primary" class="mr-2">
                      mdi-filter-variant
                    </v-icon>
                    <span class="text-subtitle-2 font-weight-medium">
                      Filtros de Perspectiva
                    </span>
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
                      {{
                        showFilters
                          ? 'mdi-chevron-up'
                          : 'mdi-chevron-down'
                      }}
                    </v-icon>
                  </template>
                </v-expansion-panel-header>
                <v-expansion-panel-content class="filter-content">
                  <v-row>
                    <v-col
                      v-for="(group, groupIndex) in perspectiveGroups"
                      :key="groupIndex"
                      cols="12"
                      md="6"
                    >
                      <v-card flat class="perspective-filter-card">
                        <v-card-title class="py-2">
                          <v-icon left color="primary" class="mr-2">
                            mdi-account-group
                          </v-icon>
                          <span class="text-subtitle-1 font-weight-medium">
                            {{ group.name }}
                          </span>
                        </v-card-title>
                        <v-divider class="mx-4"></v-divider>
                        <v-card-text class="py-2">
                          <div
                            v-for="question in group.questions"
                            :key="question.id"
                            class="mb-4"
                          >
                            <div class="d-flex align-center mb-1">
                              <v-icon
                                small
                                color="primary"
                                class="mr-2"
                              >
                                mdi-help-circle
                              </v-icon>
                              <div class="text-subtitle-2 font-weight-medium">
                                {{ question.question }}
                              </div>
                            </div>

                            <!-- String/Int Options -->
                            <v-select
                              v-if="question.data_type === 'string' || question.data_type === 'int'"
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
                                    <v-icon
                                      small
                                      color="success"
                                      class="mr-1"
                                    >
                                      mdi-check-circle
                                    </v-icon>
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
                                    <v-icon
                                      small
                                      color="error"
                                      class="mr-1"
                                    >
                                      mdi-close-circle
                                    </v-icon>
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

        <!-- Tabela de Anotadores -->
        <v-data-table
          :headers="headers"
          :items="filteredAnnotatorsData"
          :loading="loading"
          class="elevation-1"
        >
          <template #[`item.name`]="{ item }">
            <span>{{ item.name }}</span>
          </template>

          <template #[`item.labels`]="{ item }">
            <span>{{ (item.labels || []).join(', ') }}</span>
          </template>

          <template #[`item.annotations`]="{ item }">
            <span>{{ item.annotations.join(', ') }}</span>
          </template>
        </v-data-table>
      </v-card>
    </template>
  </layout-text>
</template>

<script>
import LayoutText from '@/components/tasks/layout/LayoutText.vue'
import { usePerspectiveApplicationService } from '@/services/application/perspective/perspectiveApplicationService'

export default {
  name: 'Anotadores',
  components: {
    LayoutText
  },
  layout: 'project',
  data() {
    return {
      loading: false,
      headers: [
        { text: 'Nome do Anotador', value: 'name', sortable: true },
        { text: 'Labels', value: 'labels', sortable: true },
        { text: 'Anotações', value: 'annotations', sortable: true }
      ],
      annotatorsData: [],
      filteredAnnotatorsData: [],
      selectedAnnotators: [],
      availableLabels: [],
      selectedLabels: [],
      perspectiveGroups: [],
      selectedAnswers: {},
      perspectiveAnswers: [] // Guarda as respostas de perspectiva
    };
  },

  computed: {
    hasActiveFilters() {
      return Object.values(this.selectedAnswers).some(value => {
        return Array.isArray(value) ? value.length > 0 : value !== null && value !== undefined;
      });
    }
  },

  async mounted() {
    await this.fetchAnnotators();
    await this.fetchLabels();
    await this.fetchPerspectiveGroups();
    await this.fetchPerspectiveAnswers(); // Busca as respostas de perspectiva
  },

  methods: {
    // Função auxiliar para comparação profunda
    compareValues(a, b) {
      if (typeof a === 'object' && a !== null && typeof b === 'object' && b !== null) {
        return JSON.stringify(a) === JSON.stringify(b);
      }
      return a === b;
    },

    filterAnnotators() {
      let data = this.annotatorsData;

      // Filtra por nomes (anotadores)
      if (this.selectedAnnotators.length > 0) {
        data = data.filter(annotator =>
          this.selectedAnnotators.includes(annotator.name)
        );
      }

      // Filtra por labels
      if (this.selectedLabels.length > 0) {
        data = data.filter(annotator =>
          this.selectedLabels.some(label =>
            (annotator.labels || []).includes(label)
          )
        );
      }

      // Filtra por respostas de perspectiva se houver filtros ativos:
      if (this.hasActiveFilters) {
        data = data.filter(annotator => {
          let matchFound = false;
          for (const [questionId, selectedValue] of Object.entries(this.selectedAnswers)) {
            console.log(`Filtro: Pergunta ID ${questionId}, valor selecionado:`, selectedValue);
            if (
              selectedValue === null ||
              selectedValue === undefined ||
              (Array.isArray(selectedValue) && selectedValue.length === 0)
            ) {
              continue;
            }
            // Procura todas as respostas deste anotador para a questão
            const answers = this.perspectiveAnswers.filter(ans =>
              ans.created_by_username === annotator.name &&
              parseInt(questionId) === ans.perspective
            );
            if (answers.length === 0) {
              console.log(`Anotador ${annotator.name} - Questão ${questionId}: sem respostas.`);
              continue;
            }
            // Se o filtro for boolean, converte para "Yes"/"No"
            const convertedSelectedValue = 
              typeof selectedValue === 'boolean' ? (selectedValue ? "Yes" : "No") : selectedValue;
            
            // Verifica se pelo menos uma resposta bate com o filtro
            for (const ans of answers) {
              console.log(`Anotador ${annotator.name} - Questão ${questionId}: resposta encontrada:`, ans.answer);
              if (Array.isArray(convertedSelectedValue)) {
                if (convertedSelectedValue.some(val => this.compareValues(val, ans.answer))) {
                  console.log(`Anotador ${annotator.name} - Questão ${questionId}: resposta=${ans.answer} => MATCH`);
                  matchFound = true;
                  break;
                } else {
                  console.log(`Anotador ${annotator.name} - Questão ${questionId}: resposta=${ans.answer} => NÃO bate`);
                }
              } else if (this.compareValues(ans.answer, convertedSelectedValue)) {
                console.log(`Anotador ${annotator.name} - Questão ${questionId}: resposta=${ans.answer} => MATCH`);
                matchFound = true;
                break;
              } else {
                console.log(`Anotador ${annotator.name} - Questão ${questionId}: resposta=${ans.answer} => NÃO bate`);
              }
            }
            if (matchFound) break;
          }
          return matchFound;
        });
      }

      this.filteredAnnotatorsData = data;
      console.log("Anotadores filtrados:", this.filteredAnnotatorsData);
    },

    async fetchAnnotators() {
      this.loading = true;
      try {
        const projectId = this.$route.params.id;
        console.log("ID do projeto atual:", projectId);
        const response = await this.$services.project.getMembers(projectId);
        console.log("Membros recebidos:", response);
        // Inicialmente não há respostas de perspectiva
        this.annotatorsData = response.map(member => ({
          name: member.username,
          annotations: member.annotations || [],
          datasets: member.datasets || [],
          labels: [],
          perspective_answers: {} // será preenchido depois
        }));
        this.filteredAnnotatorsData = this.annotatorsData;
      } catch (error) {
        console.error('Erro ao buscar membros do projeto:', error);
      } finally {
        this.loading = false;
      }
    },

    async fetchLabels() {
      try {
        const projectId = this.$route.params.id;
        const labelsResponse = await this.$services.label.list(projectId);
        console.log("Labels do projeto:", labelsResponse.categories);
        this.annotatorsData = this.annotatorsData.map(annotator => {
          const labelsByAnnotator = labelsResponse.categories.filter(
            label => label.user === annotator.name
          );
          return {
            ...annotator,
            labels: labelsByAnnotator.map(label => label.label)
          };
        });
        console.log("Anotadores com labels:", this.annotatorsData);
        this.filteredAnnotatorsData = this.annotatorsData;
        this.availableLabels = [
          ...new Set(labelsResponse.categories.map(label => label.label))
        ];
        console.log("Available Labels:", this.availableLabels);
      } catch (error) {
        console.error("Erro ao buscar labels:", error);
      }
    },

    async fetchPerspectiveGroups() {
      try {
        const service = usePerspectiveApplicationService();
        const response = await service.listPerspectiveGroups(this.$route.params.id);
        this.perspectiveGroups = response.results || [];
        console.log("Grupos de perspectiva encontrados:", this.perspectiveGroups);
      } catch (err) {
        console.error('Error fetching perspective groups:', err);
        this.$store.dispatch('notification/open', {
          message: 'Erro ao carregar grupos de perspectiva.',
          type: 'error'
        });
      }
    },

    // Novo método para buscar as respostas de perspectiva
    async fetchPerspectiveAnswers() {
      try {
        const projectId = this.$route.params.id;
        const service = usePerspectiveApplicationService();
        const response = await service.listPerspectiveAnswers(projectId);
        // Ajusta a extração conforme a estrutura da resposta
        this.perspectiveAnswers = Array.isArray(response)
          ? response
          : response.results || [];
        console.log("Respostas de perspectiva recebidas:", this.perspectiveAnswers);

        // Associa as respostas aos anotadores usando "created_by_username"
        this.annotatorsData = this.annotatorsData.map(annotator => {
          // Filtra as respostas referentes ao anotador
          const answers = this.perspectiveAnswers.filter(
            answer => answer.created_by_username === annotator.name
          );
          // Organiza as respostas num objeto, usando por exemplo o ID da perspetiva
          const perspective_answers = {};
          answers.forEach(ans => {
            // Se a propriedade 'perspective' já for o ID correto para filtrar
            const key = ans.perspective; // ou converta para string se necessário
            perspective_answers[key] = ans.answer;
          });
          console.log(`Respostas de perspectiva para ${annotator.name}:`, perspective_answers);
          return {
            ...annotator,
            perspective_answers
          };
        });

        // Atualiza a tabela filtrada, se necessário
        this.filteredAnnotatorsData = this.annotatorsData;
      } catch (error) {
        console.error("Erro ao buscar respostas de perspectiva:", error);
        this.$store.dispatch('notification/open', {
          message: 'Erro ao carregar respostas de perspectiva.',
          type: 'error'
        });
      }
    },

    applyFilters() {
      this.filterAnnotators();
    },

    clearFilters() {
      console.log('Limpando filtros de perspectiva...');
      this.selectedAnswers = {};
      this.$nextTick(() => {
        this.applyFilters();
      });
    },

    generateReport() {
      alert('Relatório gerado!');
    }
  }
};
</script>