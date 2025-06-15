<template>
  <v-card>
    <v-card-title class="align-center flex-wrap">
      <h2 class="text-h6 mb-4 mb-md-0 me-md-4">Estatísticas do Histórico de Anotações</h2>

      <!-- Select Dataset (placeholder, apenas um por enquanto) -->
      <v-select
        v-model="selectedDataset"
        :items="datasetOptions"
        item-text="text"
        item-value="value"
        label="Dataset"
        dense
        hide-details
        class="me-2"
        style="max-width: 200px"
        @change="onDatasetChange"
      />

      <!-- Select Versão -->
      <v-select
        v-model="selectedVersion"
        :items="versionOptions"
        label="Versão"
        dense
        hide-details
        clearable
        class="me-2"
        style="max-width: 150px"
        @change="applyFilters"
      />

      <!-- Filtro de data -->
      <v-menu v-model="dateMenu" :close-on-content-click="false" transition="scale-transition">
        <template #activator="{ on }">
          <v-text-field
            v-model="beforeFormatted"
            label="Antes de"
            prepend-icon="mdi-calendar"
            readonly
            dense
            v-on="on"
            hide-details
            style="max-width: 160px"
          />
        </template>
        <v-date-picker v-model="before" @change="applyFilters" scrollable />
      </v-menu>

      <!-- Button / dialog for filtering by Perspective answers -->
      <v-dialog v-model="perspectiveFilterDialog" max-width="600px">
        <template #activator="{ on, attrs }">
          <v-btn color="primary" dark v-bind="attrs" v-on="on" class="me-2">
            Filtrar por Perspectiva
          </v-btn>
        </template>
        <v-card>
          <v-card-title>Filtro de Perspectivas</v-card-title>
          <v-card-text>
            <v-container>
              <v-row v-for="group in perspectiveGroups" :key="group.id">
                <v-col cols="12">
                  <h3>{{ group.name }}</h3>
                  <v-row v-for="question in group.questions" :key="question.id">
                    <v-col cols="12">
                      <v-select
                        v-if="question.data_type === 'string' && question.options.length > 0"
                        v-model="selectedPerspectiveAnswers[question.id]"
                        :items="question.options"
                        :label="question.question"
                        multiple
                        chips
                        deletable-chips
                        clearable
                      />
                      <v-select
                        v-else-if="question.data_type === 'boolean'"
                        v-model="selectedPerspectiveAnswers[question.id]"
                        :items="['Yes', 'No']"
                        :label="question.question"
                        clearable
                      />
                      <v-text-field
                        v-else
                        v-model="selectedPerspectiveAnswers[question.id]"
                        :label="question.question"
                        type="number"
                        clearable
                      />
                    </v-col>
                  </v-row>
                </v-col>
              </v-row>
            </v-container>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn color="primary" text @click="applyPerspectiveFilters">Aplicar</v-btn>
            <v-btn text @click="clearPerspectiveFilters">Limpar</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-card-title>

    <!-- Slider de Progresso -->
    <v-card-subtitle class="px-6">
      Progresso (% de exemplos resolvidos)
      <v-slider
        v-model="progress"
        :max="100"
        :step="10"
        ticks="always"
        class="mt-2"
        @change="applyFilters"
      />
    </v-card-subtitle>

    <v-divider />

    <v-card-text>
      <v-row>
        <v-col
          v-for="stat in displayedStats"
          :key="stat.version"
          cols="12"
          md="6"
          class="mb-8"
        >
          <v-card outlined>
            <v-card-title class="subtitle-2">
              Versão {{ stat.version }}
            </v-card-title>
            <v-card-text style="position:relative;height:400px;">
              <bar-chart
                :key="stat.version"
                :labels="stat.labels"
                :values="stat.votes"
              />
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script>
import { Bar, mixins } from 'vue-chartjs'
const { reactiveProp } = mixins

const BarChart = {
  extends: Bar,
  mixins: [reactiveProp],
  props: ['labels', 'values'],
  mounted () { this.render() },
  watch: {
    values () { this.render() },
    labels () { this.render() }
  },
  methods: {
    render () {
      this.renderChart({
        labels: this.labels,
        datasets: [{ label: 'Votos', backgroundColor: '#42A5F5', data: this.values }]
      }, { responsive: true, maintainAspectRatio: false })
    }
  }
}

export default {
  name: 'HistoryStats',
  components: { BarChart },
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],
  data () {
    return {
      stats: [],
      before: null,
      dateMenu: false,
      progress: 100,
      datasetOptions: [{ text: 'Dataset Principal', value: 'default' }],
      selectedDataset: 'default',
      versionOptions: [],
      selectedVersion: null,
      // Perspective filters
      perspectiveFilterDialog: false,
      perspectiveGroups: [],
      selectedPerspectiveAnswers: {}
    }
  },
  computed: {
    projectId () { return this.$route.params.id },
    displayedStats () {
      if (this.selectedVersion !== null) {
        return this.stats.filter(s => s.version === this.selectedVersion)
      }
      return this.stats
    },
    beforeFormatted () { return this.before || '' }
  },
  watch: {
    // Always refetch stats when dataset changes via v-model (fallback in case @change fails)
    selectedDataset () {
      this.onDatasetChange()
    }
  },
  async mounted () {
    // load datasets
    try {
      this.datasetOptions = await this.$repositories.stats.datasets(this.projectId)
      if (this.datasetOptions.length) this.selectedDataset = this.datasetOptions[0].value
    } catch (e) { /* ignore */ }
    this.fetchStats()

    // Load perspective groups for filters
    try {
      const response = await this.$services.perspective.listPerspectiveGroups(this.projectId)
      this.perspectiveGroups = response.results || response.data?.results || []
    } catch (e) {
      // ignore errors silently for now
      console.error('Failed to load perspective groups', e)
    }
  },
  methods: {
    onDatasetChange () {
      // Reset selected version when dataset changes to avoid dangling version values
      this.selectedVersion = null
      this.applyFilters()
    },
    buildParams () {
      const params = {}
      // Apply dataset filter if selected
      if (this.selectedDataset) {
        params.dataset = this.selectedDataset
      }
      if (this.before) params.before = this.before
      if (this.progress !== null && this.progress !== 100) params.progress = this.progress

      // Perspective filters
      if (Object.keys(this.selectedPerspectiveAnswers).length > 0) {
        params.perspective_filters = JSON.stringify(this.selectedPerspectiveAnswers)
      }
      return params
    },
    async fetchStats () {
      this.stats = await this.$repositories.stats.labelVotes(this.projectId, this.buildParams())
      this.versionOptions = this.stats.map(d => d.version).sort((a, b) => a - b)
    },
    applyFilters () {
      this.fetchStats()
    },
    applyPerspectiveFilters () {
      this.perspectiveFilterDialog = false
      this.applyFilters()
    },
    clearPerspectiveFilters () {
      this.selectedPerspectiveAnswers = {}
      this.perspectiveFilterDialog = false
      this.applyFilters()
    }
  }
}
</script>

<style scoped>
</style> 