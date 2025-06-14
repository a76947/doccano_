<template>
    <v-container fluid>
      <v-row>
        <v-col cols="12">
          <v-card>
            <v-card-title>Dataset Entries</v-card-title>
            <v-card-text>
              <v-data-table
                :headers="headers"
                :items="datasetStats.entries"
                :loading="loadingStats"
                :options.sync="options"
                :server-items-length="datasetStats.total"
                class="elevation-1"
              >
                <template #item="{ item: _item }">
                  <tr>
                    <td>{{ _item.id }}</td>
                    <td>{{ _item.text }}</td>
                    <td>
                      <v-chip
                        :color="_item.annotated ? 'success' : 'warning'"
                        small
                      >
                        {{ _item.annotated ? 'Annotated' : 'Pending' }}
                      </v-chip>
                    </td>
                    <td>{{ _item.categoryCount || 0 }}</td>
                    <td>{{ _item.spanCount || 0 }}</td>
                    <td>{{ _item.relationCount || 0 }}</td>
                    <td style="width: 60px">
                      <div style="height: 40px">
                        <pie-chart
                          :chart-data="getChartData(_item)"
                          :options="{
                            responsive: true,
                            maintainAspectRatio: false,
                            legend: {
                              display: false
                            }
                          }"
                        />
                      </div>
                    </td>
                  </tr>
                </template>
              </v-data-table>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </template>
  
  <script>
  import { mapGetters } from 'vuex'
  import PieChart from '~/components/metrics/PieChart'
  
  export default {
    components: {
      PieChart
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
        loadingStats: false,
        headers: [
          { text: 'ID', value: 'id', width: '80px' },
          { text: 'Text', value: 'text' },
          { text: 'Status', value: 'status', width: '100px' },
          { text: 'Categories', value: 'categoryCount', width: '100px' },
          { text: 'Spans', value: 'spanCount', width: '100px' },
          { text: 'Relations', value: 'relationCount', width: '100px' },
          { text: 'Label Distribution', value: 'distribution', width: '100px' }
        ],
        options: {
          sortBy: ['id'],
          sortDesc: [false],
          page: 1,
          itemsPerPage: 10
        },
        labelTypes: {
          categories: [],
          spans: [],
          relations: []
        },
        labelDistribution: {}
      }
    },
  
    computed: {
      ...mapGetters('projects', ['project']),
  
      projectId() {
        return this.$route.params.id
      }
    },
  
    watch: {
      options: {
        handler() {
          this.fetchDatasetStats()
        },
        deep: true
      }
    },
  
    async created() {
      await Promise.all([
        this.fetchDatasetStats(),
        this.fetchLabelTypes(),
        this.fetchLabelDistribution()
      ])
    },
  
    methods: {
      async fetchDatasetStats() {
        this.loadingStats = true
        try {
          const params = new URLSearchParams()
          params.append('page', this.options.page)
          params.append('page_size', this.options.itemsPerPage)
          
          if (this.options.sortBy && this.options.sortBy.length > 0) {
            const sortDirection = this.options.sortDesc[0] ? '-' : ''
            params.append('ordering', `${sortDirection}${this.options.sortBy[0]}`)
          }
  
          const queryString = params.toString()
          const url = queryString ? `?${queryString}` : ''
  
          const stats = await this.$repositories.metrics.fetchDatasetStatistics(
            this.projectId,
            url
          )
          this.datasetStats = stats
        } catch (error) {
          console.error('Error fetching dataset stats:', error)
          this.$toasted.error('Failed to load dataset statistics')
        } finally {
          this.loadingStats = false
        }
      },
  
      async fetchLabelTypes() {
        try {
          const [categories, spans, relations] = await Promise.all([
            this.$services.categoryType.list(this.projectId),
            this.$services.spanType.list(this.projectId),
            this.$services.relationType.list(this.projectId)
          ])
          
          console.log('Fetched label types:', {
            categories,
            spans,
            relations
          })
  
          this.labelTypes = {
            categories,
            spans,
            relations
          }
        } catch (error) {
          console.error('Error fetching label types:', error)
        }
      },
  
      async fetchLabelDistribution() {
        try {
          const [categoryDist, spanDist, relationDist] = await Promise.all([
            this.$repositories.metrics.fetchCategoryDistribution(this.projectId),
            this.$repositories.metrics.fetchSpanDistribution(this.projectId),
            this.$repositories.metrics.fetchRelationDistribution(this.projectId)
          ])
  
          console.log('Fetched distributions:', {
            categories: categoryDist,
            spans: spanDist,
            relations: relationDist
          })
  
          this.labelDistribution = {
            categories: categoryDist,
            spans: spanDist,
            relations: relationDist
          }
        } catch (error) {
          console.error('Error fetching label distribution:', error)
        }
      },
  
      getChartData(_item) {
        const labels = []
        const data = []
        const colors = ['#4CAF50', '#2196F3', '#FFC107', '#9C27B0', '#FF5722', '#795548']
  
        // Focus only on span labels
        const spanDistribution = this.labelDistribution.spans || {}
        const spanTypes = this.labelTypes.spans || []
  
        // For each span type, check if it's used in this document
        spanTypes.forEach(spanType => {
          let totalCount = 0
          // Sum up all user annotations for this span type
          Object.entries(spanDistribution).forEach(([_user, userDistribution]) => {
            if (userDistribution && userDistribution[spanType.id]) {
              totalCount += parseInt(userDistribution[spanType.id]) || 0
            }
          })
          
          if (totalCount > 0) {
            labels.push(spanType.text)
            data.push(totalCount)
          }
        })
  
        // If no labels found, show a placeholder
        if (labels.length === 0) {
          return {
            labels: ['No Labels'],
            datasets: [{
              backgroundColor: ['#E0E0E0'],
              data: [1]
            }]
          }
        }
  
        return {
          labels,
          datasets: [{
            backgroundColor: colors.slice(0, labels.length),
            data
          }]
        }
      }
    }
  }
  </script>
  
  <style scoped>
  .v-card {
    margin-bottom: 1rem;
  }
  
  /* Make the chart container smaller */
  :deep(.chart-container) {
    height: 40px !important;
    width: 60px !important;
    margin: 0 auto;
  }
  
  /* Hide the chart title */
  :deep(.v-card__title) {
    display: none !important;
  }
  </style>
  