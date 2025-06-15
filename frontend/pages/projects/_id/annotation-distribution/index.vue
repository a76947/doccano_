<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            Dataset Entries
            <v-spacer></v-spacer>
            <!-- Add Perspective Filters -->
            <v-dialog v-model="perspectiveFilterDialog" max-width="600px">
              <template v-slot:activator="{ on, attrs }">
                <v-btn
                  color="primary"
                  dark
                  v-bind="attrs"
                  v-on="on"
                  class="mr-2"
                >
                  Filter by Perspective
                </v-btn>
              </template>
              <v-card>
                <v-card-title>Filter by Perspective</v-card-title>
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
                            ></v-select>
                            <v-select
                              v-else-if="question.data_type === 'boolean'"
                              v-model="selectedPerspectiveAnswers[question.id]"
                              :items="['Yes', 'No']"
                              :label="question.question"
                              clearable
                            ></v-select>
                            <v-text-field
                              v-else
                              v-model="selectedPerspectiveAnswers[question.id]"
                              :label="question.question"
                              type="number"
                              clearable
                            ></v-text-field>
                          </v-col>
                        </v-row>
                      </v-col>
                    </v-row>
                  </v-container>
                </v-card-text>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn color="primary" text @click="applyPerspectiveFilters">
                    Apply Filters
                  </v-btn>
                  <v-btn text @click="clearPerspectiveFilters">
                    Clear Filters
                  </v-btn>
                </v-card-actions>
              </v-card>
            </v-dialog>
          </v-card-title>
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
                  <td style="width: 150px">
                    <div style="height: 120px; width: 100%; position: relative; margin: 0 auto;">
                      <bar-chart
                        :chart-data="getChartData(_item)"
                        :options="{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              display: false
                            },
                            tooltip: {
                              callbacks: {
                                label: function(context) {
                                  return context.dataset.label || context.label
                                }
                              }
                            }
                          },
                          scales: {
                            x: {
                              display: true,
                              stacked: true,
                              ticks: {
                                display: true,
                                font: {
                                  size: 12
                                }
                              }
                            },
                            y: {
                              display: false,
                              stacked: true,
                              beginAtZero: true,
                              max: 100
                            }
                          },
                          barPercentage: 1,
                          categoryPercentage: 1,
                          animation: {
                            duration: 0
                          }
                        }"
                        :height="118"
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
import { toRaw } from 'vue'
import { mapGetters } from 'vuex'
import BarChart from '~/components/metrics/ChartBar'
import { APIAnnotationRepository } from '~/repositories/annotation/apiAnnotationRepository'

export default {
  components: {
    BarChart
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
      labelDistribution: {},
      documentAnnotations: {}, // Cache for document annotations
      annotationsRepository: new APIAnnotationRepository(),
      // Add new data properties for perspective filtering
      perspectiveFilterDialog: false,
      perspectiveGroups: [],
      selectedPerspectiveAnswers: {}
    }
  },

  computed: {
    ...mapGetters('projects', ['project']),
    ...mapGetters('auth', ['getUsername', 'getUserId']),

    projectId() {
      return this.$route.params.id
    }
  },

  watch: {
    options: {
      async handler() {
        await this.fetchDatasetStats()
        // Fetch annotations for new documents when page changes
        if (this.datasetStats.entries) {
          await Promise.all(
            this.datasetStats.entries.map(entry => 
              this.fetchDocumentAnnotations(entry.id)
            )
          )
        }
      },
      deep: true
    }
  },

  async created() {
    await Promise.all([
      this.fetchDatasetStats(),
      this.fetchLabelTypes(),
      this.fetchLabelDistribution(),
      this.fetchPerspectiveGroups()
    ])

    // Fetch annotations for all documents in the current page
    if (this.datasetStats.entries) {
      await Promise.all(
        this.datasetStats.entries.map(entry => 
          this.fetchDocumentAnnotations(entry.id)
        )
      )
    }
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

        // Add perspective filters to the query
        if (Object.keys(this.selectedPerspectiveAnswers).length > 0) {
          params.append('perspective_filters', JSON.stringify(this.selectedPerspectiveAnswers))
        }

        const queryString = params.toString()
        const url = queryString ? `?${queryString}` : ''

        const stats = await this.$repositories.metrics.fetchDatasetStatistics(
          this.projectId,
          url
        )
        this.datasetStats = stats
        console.log('Dataset stats sample:', stats.entries[0])
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
        
        console.log('Raw categories from API:', categories)
        console.log('Raw spans from API:', spans)
        console.log('Raw relations from API:', relations)

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

        console.log('Raw category distribution:', JSON.stringify(categoryDist, null, 2))
        console.log('Raw span distribution:', JSON.stringify(spanDist, null, 2))
        console.log('Raw relation distribution:', JSON.stringify(relationDist, null, 2))

        // Initialize the distribution object with empty objects for each user
        this.labelDistribution = {
          categories: categoryDist || {},
          spans: spanDist || {},
          relations: relationDist || {}
        }
      } catch (error) {
        console.error('Error fetching label distribution:', error)
        // Initialize with empty objects if there's an error
        this.labelDistribution = {
          categories: {},
          spans: {},
          relations: {}
        }
      }
    },

    async fetchDocumentAnnotations(docId) {
      if (this.documentAnnotations[docId]) {
        return this.documentAnnotations[docId]
      }

      try {
        // Get annotations for the current document
        const url = `/projects/${this.projectId}/annotations?doc_id=${docId}`
        const response = await this.$axios.get(url)
        const annotations = response.data || []
        
        // Ensure annotations is an array and filter for this document
        const docAnnotations = Array.isArray(annotations) 
        ? annotations.filter(ann => ann.example === docId) : []
        
        // Store filtered annotations for this document
        this.documentAnnotations[docId] = docAnnotations
        return docAnnotations
      } catch (error) {
        console.error(`Error fetching annotations for document ${docId}:`, error)
        return []
      }
    },

    getChartData(_item) {
      // Convert reactive object to raw data
      const rawItem = toRaw(_item)
      console.log('Processing item:', rawItem)
      
      // Get the category count from the raw item
      const categoryCount = rawItem.categoryCount || 0
      console.log('Category count:', categoryCount)

      // If no categories, show empty state
      if (categoryCount === 0) {
        return {
          labels: ['No Labels'],
          datasets: [{
            label: 'No Labels',
            backgroundColor: ['#E0E0E0'],
            data: [1],
            barThickness: 45
          }]
        }
      }

      // Get the raw category distribution
      const rawCategoryDist = toRaw(this.labelDistribution?.categories)
      console.log('Raw category distribution:', rawCategoryDist)

      // Get the document's annotations
      const annotations = this.documentAnnotations[rawItem.id] || []
      console.log('Document annotations:', annotations)

      // Get the raw label types
      const rawLabelTypes = toRaw(this.labelTypes.categories)
      console.log('Raw label types:', rawLabelTypes)

      // First try to get the label from annotations
      let labelName = null
      let labelType = null

      if (annotations.length > 0) {
        // Get the first annotation's label
        const firstAnnotation = annotations[0]
        labelType = rawLabelTypes.find(lt => lt.id === firstAnnotation.label)
        if (labelType) {
          labelName = labelType.text
        }
      }

      // If we couldn't find the label from annotations, try to get it from the distribution
      if (!labelName && rawCategoryDist) {
        // Get the document's position in the dataset
        const docIndex = this.datasetStats.entries.findIndex(entry => entry.id === rawItem.id)
        console.log('Document index:', docIndex)

        if (docIndex !== -1) {
          // Look through each user's distribution
          for (const [, userDist] of Object.entries(rawCategoryDist)) {
            // Find all labels that have a count > 0
            const usedLabels = Object.entries(userDist)
              .filter(([_, count]) => count > 0)
              .map(([label]) => label)

            // If we have exactly one label used, use it
            if (usedLabels.length === 1) {
              labelName = usedLabels[0]
              labelType = rawLabelTypes.find(lt => lt.text === labelName)
              break
            }
            // If we have multiple labels, use the one that matches our document's position
            else if (usedLabels.length > 1) {
              // Use the label at the document's position (modulo the number of labels)
              const labelIndex = docIndex % usedLabels.length
              labelName = usedLabels[labelIndex]
              labelType = rawLabelTypes.find(lt => lt.text === labelName)
              break
            }
          }
        }
      }

      console.log('Found label for document:', labelName)

      // If we found a label, use it
      if (labelName && labelType) {
        return {
          labels: [labelName],
          datasets: [{
            label: labelName,
            backgroundColor: [labelType.backgroundColor || this.getLabelColor(labelName)],
            data: [categoryCount],
            barThickness: 45
          }]
        }
      }

      // Fallback to generic category if we couldn't determine the label
      return {
        labels: ['Categories'],
        datasets: [{
          label: 'Categories',
          backgroundColor: ['#4CAF50'],
          data: [categoryCount],
          barThickness: 45
        }]
      }
    },

    getLabelColor(labelName) {
      // Generate a consistent color for each label name
      const colors = [
        '#4CAF50', // Green
        '#2196F3', // Blue
        '#FFC107', // Yellow
        '#F44336', // Red
        '#9C27B0', // Purple
        '#00BCD4', // Cyan
        '#FF9800', // Orange
        '#795548', // Brown
        '#607D8B', // Blue Grey
        '#E91E63'  // Pink
      ]
      
      // Use the label name to generate a consistent index
      const index = labelName.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % colors.length
      return colors[index]
    },

    async fetchPerspectiveGroups() {
      try {
        const response = await this.$services.perspective.listPerspectiveGroups(this.projectId)
        this.perspectiveGroups = response.results || response.data?.results || []
      } catch (error) {
        console.error('Error fetching perspective groups:', error)
        this.$toasted.error('Failed to load perspective groups')
      }
    },

    applyPerspectiveFilters() {
      this.perspectiveFilterDialog = false
      this.fetchDatasetStats()
    },

    clearPerspectiveFilters() {
      this.selectedPerspectiveAnswers = {}
      this.perspectiveFilterDialog = false
      this.fetchDatasetStats()
    }
  }
}
</script>

<style scoped>
.v-card {
  margin-bottom: 1rem;
}

/* Ensure the chart container clips content and is sized by its child */
:deep(.chart-container) {
  width: 100% !important; 
  margin: 0 auto;
  background-color: #f9f9f9;
  border-radius: 6px;
  overflow: hidden !important;
}

/* Ensure bars are fully visible */
:deep(.chart-container canvas) {
  min-height: 118px !important;
  min-width: 60px !important;
}
</style>
