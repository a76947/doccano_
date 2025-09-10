<template>
  <v-container fluid>
    <!-- Error message as pop-up central superior -->
    <transition name="fade">
      <div v-if="errorMessage" class="error-message">
        <v-icon small class="mr-2" color="error">mdi-alert-circle</v-icon>
        {{ errorMessage }}
      </div>
    </transition>

    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            Dataset Entries
            <v-spacer></v-spacer>
            <!-- Add CSV Report Button -->
            <v-btn
              :loading="generatingCSV"
              color="primary"
              class="mr-2"
              @click="generateCSVReport"
            >
              <v-icon left>mdi-file-excel</v-icon>
              Generate CSV Report
            </v-btn>
            <!-- Add PDF Report Button -->
            <v-btn
              :loading="generatingReport"
              color="primary"
              class="mr-2"
              @click="generatePDFReport"
            >
              <v-icon left>mdi-file-pdf-box</v-icon>
              Generate PDF Report
            </v-btn>
            <!-- Add Perspective Filters -->
            <v-dialog v-model="perspectiveFilterDialog" max-width="600px">
              <template #activator="{ on, attrs }">
                <v-btn
                  class="mr-2"
                  color="primary"
                  dark
                  v-bind="attrs"
                  v-on="on"
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
                            },
                            title: {
                              display: true,
                              text: 'LABELS',
                              font: {
                                size: 14,
                                weight: 'bold'
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
      generatingReport: false,
      generatingCSV: false,
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
      selectedPerspectiveAnswers: {},
      errorMessage: null
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
        if (!error.response || (error.response.status && error.response.status >= 500)) {
          this.errorMessage = 'Database unavailable at the moment, please try again later.'
        } else {
          this.errorMessage = 'Failed to load dataset statistics'
        }
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
        
        // Store annotations for this document
        this.documentAnnotations[docId] = annotations
        return annotations
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
            data: [100], // 100% for no labels
            barThickness: 45
          }]
        }
      }

      // Get the label distribution from the item
      const labelDistribution = rawItem.labelDistribution || {}
      console.log('Label distribution:', labelDistribution)

      // Get the raw label types
      const rawLabelTypes = toRaw(this.labelTypes.categories) || []
      console.log('Raw label types:', rawLabelTypes)

      // If we have labels, use them
      if (Object.keys(labelDistribution).length > 0) {
        const labels = Object.keys(labelDistribution)
        console.log('Using labels:', labels)
        
        // Calculate total count for percentage calculation
        const totalCount = Object.values(labelDistribution).reduce((sum, count) => sum + count, 0)
        
        // Calculate percentages
        const data = labels.map(label => {
          const count = labelDistribution[label]
          return Math.round((count / totalCount) * 100)
        })
        
        const backgroundColors = labels.map(label => {
          const labelType = rawLabelTypes.find(lt => lt.text === label)
          return labelType?.backgroundColor || this.getLabelColor(label)
        })

        return {
          labels,
          datasets: [{
            label: 'Labels (%)',
            data,
            backgroundColor: backgroundColors,
            barThickness: 45
          }]
        }
      }

      // If we have category count but no specific labels, show the count as percentage
      if (categoryCount > 0) {
        return {
          labels: ['Categories'],
          datasets: [{
            label: 'Categories (%)',
            backgroundColor: ['#4CAF50'],
            data: [100], // 100% for categories
            barThickness: 45
          }]
        }
      }

      // Fallback to empty state
      return {
        labels: ['No Labels'],
        datasets: [{
          backgroundColor: ['#E0E0E0'],
          data: [100], // 100% for no labels
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
    },

    async generatePDFReport() {
      this.generatingReport = true
      try {
        // Prepare query parameters
        const params = new URLSearchParams()
        
        // Add current filters
        if (Object.keys(this.selectedPerspectiveAnswers).length > 0) {
          params.append('perspective_filters', JSON.stringify(this.selectedPerspectiveAnswers))
        }

        // Add other filters if they exist
        if (this.options.sortBy && this.options.sortBy.length > 0) {
          const sortDirection = this.options.sortDesc[0] ? '-' : ''
          params.append('ordering', `${sortDirection}${this.options.sortBy[0]}`)
        }

        const url = `/v1/projects/${this.projectId}/metrics/dataset-report?${params.toString()}`
        console.log('Making PDF request to:', url)
        console.log('Request params:', params.toString())

        // Make the request to generate PDF
        const response = await this.$axios.get(
          url,
          { 
            responseType: 'blob',
            headers: {
              'Accept': 'application/pdf, application/json'
            }
          }
        )

        console.log('Response received:', {
          type: response.headers['content-type'],
          size: response.data.size
        })

        // Check if the response is an error message
        if (response.headers['content-type'] === 'application/json') {
          const reader = new FileReader()
          reader.onload = () => {
            const errorData = JSON.parse(reader.result)
            this.errorMessage = errorData.detail || 'Failed to generate PDF report'
          }
          reader.readAsText(response.data)
          return
        }

        // Create a blob from the PDF data
        const blob = new Blob([response.data], { type: 'application/pdf' })
        const blobUrl = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = blobUrl
        link.setAttribute('download', `dataset-report-${this.projectId}.pdf`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(blobUrl)
      } catch (error) {
        console.error('Error generating PDF report:', error)
        if (!error.response || (error.response.status && error.response.status >= 500)) {
          this.errorMessage = 'Database unavailable at the moment, please try again later.'
        } else {
          this.errorMessage = 'Failed to generate PDF report'
        }
      } finally {
        this.generatingReport = false
      }
    },

    generateCSVReport() {
      this.generatingCSV = true
      try {
        const delimiter = ';'
        const rows = [
          ['ID', 'Text', 'Status', 'Label Distribution']
        ]

        // Add all entries to the CSV
        this.datasetStats.entries.forEach(entry => {
          const labelDistribution = entry.labelDistribution || {}
          const labels = Object.entries(labelDistribution)
            .map(([label, count]) => `${label}: ${count}`)
            .join(', ')
          
          rows.push([
            entry.id,
            entry.text,
            entry.annotated ? 'Annotated' : 'Pending',
            labels || 'No Labels'
          ])
        })

        // Add statistics section
        rows.push([]) // Empty row for separation
        rows.push(['Dataset Statistics'])
        rows.push(['Total Entries', this.datasetStats.total])
        rows.push(['Annotated Entries', this.datasetStats.annotated])
        rows.push(['Unannotated Entries', this.datasetStats.unannotated])
        rows.push(['Annotation Rate', `${((this.datasetStats.annotated / this.datasetStats.total) * 100).toFixed(2)}%`])

        // Add label type statistics if available
        if (this.labelTypes.categories.length > 0) {
          rows.push([])
          rows.push(['Category Label Types'])
          this.labelTypes.categories.forEach(category => {
            rows.push([category.text, category.backgroundColor])
          })
        }

        if (this.labelTypes.spans.length > 0) {
          rows.push([])
          rows.push(['Span Label Types'])
          this.labelTypes.spans.forEach(span => {
            rows.push([span.text, span.backgroundColor])
          })
        }

        if (this.labelTypes.relations.length > 0) {
          rows.push([])
          rows.push(['Relation Label Types'])
          this.labelTypes.relations.forEach(relation => {
            rows.push([relation.text, relation.backgroundColor])
          })
        }

        // Add global label distribution if available
        if (Object.keys(this.labelDistribution).length > 0) {
          rows.push([])
          rows.push(['Global Label Distribution'])
          
          if (Object.keys(this.labelDistribution.categories).length > 0) {
            rows.push(['Category Distribution'])
            Object.entries(this.labelDistribution.categories).forEach(([label, count]) => {
              rows.push([label, count])
            })
          }

          if (Object.keys(this.labelDistribution.spans).length > 0) {
            rows.push(['Span Distribution'])
            Object.entries(this.labelDistribution.spans).forEach(([label, count]) => {
              rows.push([label, count])
            })
          }

          if (Object.keys(this.labelDistribution.relations).length > 0) {
            rows.push(['Relation Distribution'])
            Object.entries(this.labelDistribution.relations).forEach(([label, count]) => {
              rows.push([label, count])
            })
          }
        }

        const csvContent = '\uFEFF' + // UTF-8 BOM for better compatibility (Excel)
          rows
            .map(r => r.map(item => {
              const field = String(item)
              const needsQuotes = field.includes(delimiter) || field.includes('"') || field.includes('\n')
              const escaped = field.replace(/"/g, '""')
              return needsQuotes ? `"${escaped}"` : escaped
            }).join(delimiter))
            .join('\r\n')

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
        const blobUrl = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = blobUrl
        link.setAttribute('download', `dataset-report-${this.projectId}-${new Date().toISOString()}.csv`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(blobUrl)
      } catch (error) {
        console.error('Error generating CSV report:', error)
        this.errorMessage = 'Failed to generate CSV report'
      } finally {
        this.generatingCSV = false
      }
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

/* Error message styles */
.error-message {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  background-color: #fdecea;
  color: #b71c1c;
  padding: 12px 24px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  font-weight: 500;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  pointer-events: none;
}

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-enter,
.fade-leave-to {
  opacity: 0;
}
</style>
