<template>
  <v-row>
    <v-col cols="12">
      <member-progress />
    </v-col>
    <v-col cols="12">
      <pie-chart-statistics 
        :stats.sync="datasetStats" 
        :loading.sync="loadingStats"
        :project-id="projectId"
        @update:stats="onStatsUpdated"
      />
    </v-col>
  </v-row>
</template>

<script>
import { mapGetters } from 'vuex'
import MemberProgress from '~/components/metrics/MemberProgress'
import PieChartStatistics from '~/components/metrics/PieChartStatistics'

export default {
  components: {
    MemberProgress,
    PieChartStatistics
  },

  layout: 'project',

  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  validate({ params }) {
    return /^\d+$/.test(params.id)
  },

  data() {
    return {
      datasetStats: {
        total: 0,
        annotated: 0,
        unannotated: 0,
        entries: []
      },
      loadingStats: false
    }
  },

  computed: {
    ...mapGetters('projects', ['project']),

    projectId() {
      return this.$route.params.id
    }
  },

  async created() {
    await this.fetchDatasetStats()
  },

  methods: {
    async fetchDatasetStats() {
      try {
        this.loadingStats = true
        const response = await this.$repositories.metrics.fetchDatasetStatistics(this.projectId)
        this.datasetStats = response
      } catch (error) {
        this.$toasted.error('Failed to fetch dataset statistics')
        console.error(error)
      } finally {
        this.loadingStats = false
      }
    },

    onStatsUpdated(newStats) {
      console.log('Parent received updated stats', {
        total: newStats.total,
        filtered: newStats.filtered,
        annotated: newStats.annotated
      });
      this.datasetStats = JSON.parse(JSON.stringify(newStats));
    }
  }
}
</script> 