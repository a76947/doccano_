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
      selectedVersion: null
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
  async mounted () {
    // load datasets
    try {
      this.datasetOptions = await this.$repositories.stats.datasets(this.projectId)
      if (this.datasetOptions.length) this.selectedDataset = this.datasetOptions[0].value
    } catch (e) { /* ignore */ }
    this.fetchStats()
  },
  methods: {
    buildParams () {
      const params = {}
      if (this.before) params.before = this.before
      if (this.progress !== null && this.progress !== 100) params.progress = this.progress
      return params
    },
    async fetchStats () {
      this.stats = await this.$repositories.stats.labelVotes(this.projectId, this.buildParams())
      this.versionOptions = this.stats.map(d => d.version).sort((a, b) => a - b)
    },
    applyFilters () {
      this.fetchStats()
    }
  }
}
</script>

<style scoped>
</style> 