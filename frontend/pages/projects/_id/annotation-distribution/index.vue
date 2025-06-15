<template>
  <v-card>
    <v-card-title class="align-center">
      <h2 class="text-h6 mb-0">Distribuição de Votos por Label</h2>
      <v-spacer />
      <!-- Filtro antes de data -->
      <v-menu v-model="menu" :close-on-content-click="false" transition="scale-transition">
        <template #activator="{ on }">
          <v-text-field
            v-model="beforeFormatted"
            label="Antes de"
            prepend-icon="mdi-calendar"
            readonly
            dense
            v-on="on"
            hide-details
            style="max-width: 180px"
          />
        </template>
        <v-date-picker v-model="before" @change="applyFilter" scrollable />
      </v-menu>
    </v-card-title>
    <v-divider />
    <v-card-text>
      <div style="height:400px;">
        <bar-chart :labels="chartLabels" :values="chartValues" />
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
import { Bar, mixins } from 'vue-chartjs'
import ApiService from '@/services/api.service'
const { reactiveProp } = mixins

const BarChart = {
  extends: Bar,
  mixins: [reactiveProp],
  props: ['labels', 'values'],
  mounted () {
    this.render()
  },
  watch: {
    values () { this.render() },
    labels () { this.render() }
  },
  methods: {
    render () {
      this.renderChart({
        labels: this.labels,
        datasets: [{
          label: 'Votos',
          backgroundColor: '#42A5F5',
          data: this.values
        }]
      }, { responsive: true, maintainAspectRatio: false })
    }
  }
}

export default {
  name: 'AnnotationDistribution',
  components: { BarChart },
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],
  data () {
    return {
      stats: [],
      before: null,
      menu: false
    }
  },
  computed: {
    projectId () { return this.$route.params.id },
    chartLabels () { return this.stats.map(s => s.label) },
    chartValues () { return this.stats.map(s => s.votes) },
    beforeFormatted () { return this.before || '' }
  },
  mounted () { this.fetchStats() },
  methods: {
    async fetchStats () {
      const params = {}
      if (this.before) params.before = this.before
      const { data } = await ApiService.get(`/projects/${this.projectId}/stats/label-votes`, { params })
      this.stats = data
    },
    applyFilter () {
      this.menu = false
      this.fetchStats()
    }
  }
}
</script>

<style scoped>
</style>
