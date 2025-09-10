<template>
  <v-container>
    <h1 class="text-h4 mb-4">Discrepancy History</h1>

    <v-card>
      <v-card-title>
        <v-select
          :items="datasetNames"
          v-model="selectedDatasetName"
          label="Dataset"
          solo
          dense
          hide-details
          class="col-md-4 col-12 mr-2"
        ></v-select>

        <v-spacer></v-spacer>
        <v-btn color="primary" class="mr-2" :loading="loading"
         :disabled="loading" @click="generateReport">
          GENERATE DISCREPANCY REPORT
        </v-btn>
        <v-btn :disabled="!downloadReady" @click="downloadReport">
          EXPORT DISCREPANCY REPORT
        </v-btn>
      </v-card-title>

      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="discrepancies"
          :loading="loading"
          class="elevation-1"
        >
          <template #[`item.percentages`]="{ item }">
            <div v-for="(percentage, label) in item.percentages" :key="label">
              {{ label }}: {{ percentage.toFixed(2) }}%
            </div>
          </template>

          <template #[`item.is_discrepancy`]="{ item }">
            <v-chip
              :color="item.is_discrepancy ? 'error' : 'success'"
              small
            >
              {{ item.is_discrepancy ? 'Discrepancy' : 'Agreement' }}
            </v-chip>
          </template>

          <template #[`item.perspective_answers`]="{ item }">
            <div v-for="(answer, index) in item.perspective_answers" :key="index">
              <strong>{{ answer.question }}:</strong> {{ answer.answer }}
              <br>
              <small>By: {{ answer.answered_by }} on {{ answer.answer_date }}</small>
            </div>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script>
export default {
  layout: 'project',

  validate({ params }) {
    return /^\d+$/.test(params.id)
  },

  data() {
    return {
      datasetNames: [],
      selectedDatasetName: null,
      headers: [
        { text: 'Example ID', value: 'example_id' },
        { text: 'Dataset', value: 'datasetName' },
        { text: 'Text', value: 'text' },
        { text: 'Label Percentages', value: 'percentages' },
        { text: 'Status', value: 'is_discrepancy' },
        { text: 'Max Percentage', value: 'max_percentage' },
        { text: 'Different Labels', value: 'diff_count' },
        { text: 'Perspective Answers', value: 'perspective_answers' },
      ],
      discrepancies: [],
      loading: false,
      taskId: null,
      polling: null,
      downloadReady: false,
    }
  },

  computed: {
    projectId() {
      return this.$route.params.id
    }
  },

  methods: {
    async fetchDatasetNames() {
      try {
        const response = await this.$repositories.example.fetchDatasetNames(this.projectId)
        this.datasetNames = response.datasetNames
      } catch (error) {
        console.error("Error fetching dataset names:", error)
        this.$toasted.error('Error loading dataset names')
      }
    },

    async generateReport() {
      this.loading = true
      this.downloadReady = false
      this.discrepancies = []
      try {
        this.taskId = await this.$repositories.discrepancyHistory.prepare(
          this.projectId,
          this.selectedDatasetName
        )
        this.pollTaskStatus()
      } catch (error) {
        console.error("Error generating report:", error)
        this.$toasted.error('Error generating report')
        this.loading = false
      }
    },

    pollTaskStatus() {
      if (this.polling) {
        clearInterval(this.polling)
        this.polling = null
      }
      
      this.polling = setInterval(async () => {
        if (!this.taskId) {
          clearInterval(this.polling)
          this.polling = null
          return
        }

        try {
          const res = await this.$repositories.taskStatus.get(this.taskId)
          console.log("Task status response:", res)

          if (res && res.ready) {
            if (!res.error) {
              clearInterval(this.polling)
              this.polling = null
              this.loading = false
              
              const data = await this.$repositories.discrepancyHistory.fetch(
                this.projectId,
                this.taskId
              )
              
              this.discrepancies = data
              console.log("Fetched discrepancies:", this.discrepancies)
              this.downloadReady = true
              this.$toasted.success('Discrepancy report generated successfully!')
            } else {
              clearInterval(this.polling)
              this.polling = null
              this.loading = false
              this.$toasted.error(`Error generating discrepancy report: ${res.error || 'Unknown error'}`)
            }
          }
        } catch (error) {
          console.error("Error polling task status:", error)
          this.$toasted.error('Error polling report status')
          clearInterval(this.polling)
          this.polling = null
          this.loading = false
        }
      }, 1000)
    },

    async downloadReport() {
      this.loading = true
      try {
        const downloadTaskId = await this.$repositories.discrepancyHistory.prepare(
          this.projectId,
          this.selectedDatasetName
        )

        let downloadPolling = null
        downloadPolling = setInterval(async () => {
          const res = await this.$repositories.taskStatus.get(downloadTaskId)
          console.log("Download task status response:", res)
          if (res && res.ready) {
            if (!res.error) {
              clearInterval(downloadPolling)
              this.loading = false
              this.$repositories.discrepancyHistory.downloadFile(this.projectId, downloadTaskId)
              this.$toasted.success('Discrepancy report downloaded successfully!')
            } else {
              clearInterval(downloadPolling)
              this.loading = false
              this.$toasted.error(`Error downloading discrepancy report: ${res.error || 'Unknown error'}`)
            }
          }
        }, 1000)

      } catch (error) {
        console.error("Error initiating download:", error)
        this.$toasted.error('Error initiating discrepancy report download')
        this.loading = false
      }
    },

    resetReportState() {
      if (this.polling) {
        clearInterval(this.polling)
        this.polling = null
      }
      this.taskId = null
      this.downloadReady = false
      this.loading = false
      this.discrepancies = []
    },

    clearFilters() {
      this.selectedDatasetName = null
      this.generateReport()
    }
  },

  created() {
    this.fetchDatasetNames()
  },

  beforeDestroy() {
    clearInterval(this.polling)
  }
}
</script>

<style scoped>
.v-data-table {
  width: 100%;
}
</style> 