<template>
  <v-container>
    <h1 class="text-h4 mb-4">History of Annotations</h1>

    <!-- Tabs for Annotations and Annotators -->
    <v-tabs v-model="selectedTab" class="mb-4">
      <v-tab href="#tab-annotations">
        Annotations
      </v-tab>
      <v-tab href="#tab-annotators">
        Annotators
      </v-tab>
    </v-tabs>

    <v-card>
      <v-card-title>
        <!-- Report Type dropdown -->
        <v-select
          v-model="selectedReportType"
          :items="reportTypes"
          label="Report Type"
          outlined
          dense
          class="mb-2"
        ></v-select>

        <v-spacer></v-spacer>
        <v-btn color="primary" class="mr-2" :loading="loading"
         :disabled="loading" @click="generateReport">
          <v-icon left>mdi-file-document-outline</v-icon>
          Generate Report
        </v-btn>
        <v-btn color="primary" outlined :disabled="!downloadReady" @click="showExportDialog = true">
          <v-icon left>mdi-download</v-icon>
          Export Report
        </v-btn>
      </v-card-title>

      <v-card-text>
        <!-- Content for Annotations Tab -->
        <v-tabs-items v-model="selectedTab">
          <v-tab-item value="tab-annotations">
            <template v-if="selectedReportType === 'Annotation History'">
              <v-toolbar flat dense class="mb-4">
                <v-spacer></v-spacer>
                <v-select
                  v-model="selectedDatasetName"
                  :items="datasetNames"
                  label="Dataset"
                  outlined
                  dense
                  class="mb-2"
                  @change="handleDatasetChange"
                ></v-select>
                <v-select
                  v-model="selectedAnnotationStatus"
                  :items="annotationStatuses"
                  label="Annotation Status"
                  outlined
                  dense
                  class="mb-2"
                  @change="handleAnnotationStatusChange"
                ></v-select>
                <v-btn text @click="clearFilters">
                  CLEAR FILTERS
                </v-btn>
              </v-toolbar>
              <v-data-table
                :headers="headers"
                :items="annotations"
                :loading="loading"
                class="elevation-1 mb-4"
              ></v-data-table>

              <!-- Perspectives Table -->
              <v-divider class="my-6"></v-divider>
              
              <v-card-title class="px-0">
                <h2 class="text-h5">Perspectives</h2>
                <v-spacer></v-spacer>
                <v-btn color="primary" class="mr-2" :loading="loadingPerspectives"
                 :disabled="loadingPerspectives" @click="generatePerspectivesReport">
                  <v-icon left>mdi-file-document-outline</v-icon>
                  Generate Perspectives
                </v-btn>
                <v-btn color="primary" outlined :disabled="
                !perspectivesDownloadReady" @click="downloadPerspectivesReport">
                  <v-icon left>mdi-download</v-icon>
                  Export Perspectives
                </v-btn>
              </v-card-title>

              <v-data-table
                :headers="perspectiveHeaders"
                :items="perspectives"
                :loading="loadingPerspectives"
                class="elevation-1"
              ></v-data-table>
            </template>
            <template v-else>
              <!-- Placeholder for Discrepancy Report content under Annotations tab -->
              <p>Content for Discrepancy Report (Annotations view)</p>
            </template>
          </v-tab-item>

          <!-- Content for Annotators Tab -->
          <v-tab-item value="tab-annotators">
            <!-- This content will change based on selectedReportType too -->
            <template v-if="selectedReportType === 'Annotation History'">
              <p>Content for Annotation History (Annotators view)</p>
            </template>
            <template v-else>
              <p>Content for Discrepancy Report (Annotators view)</p>
            </template>
          </v-tab-item>
        </v-tabs-items>
      </v-card-text>
    </v-card>

    <!-- Export Format Dialog -->
    <v-dialog v-model="showExportDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h5">
          <v-icon left color="primary">mdi-download</v-icon>
          Choose Export Format
        </v-card-title>
        <v-card-text>
          <v-radio-group v-model="selectedExportFormat" class="mt-4">
            <v-radio label="PDF" value="pdf">
              <template v-slot:label>
                <div class="d-flex align-center">
                  <v-icon left color="red" class="mr-2">mdi-file-pdf-box</v-icon>
                  PDF Format
                </div>
              </template>
            </v-radio>
            <v-radio label="CSV" value="csv">
              <template v-slot:label>
                <div class="d-flex align-center">
                  <v-icon left color="green" class="mr-2">mdi-file-excel</v-icon>
                  CSV Format
                </div>
              </template>
            </v-radio>
          </v-radio-group>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="showExportDialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="handleExport">
            <v-icon left>mdi-download</v-icon>
            Export
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { mdiMagnify } from '@mdi/js'

export default {
  name: 'AnnotationHistory',
  layout: 'project',

  validate({ params }) {
    return /^\d+$/.test(params.id)
  },

  data() {
    return {
      selectedTab: 'tab-annotations', // Default selected tab
      selectedReportType: 'Annotation History', // Default selected report type
      reportTypes: ['Annotation History', 'Discrepancy Report'], // Report types
      datasetNames: [], // Dynamically loaded dataset names
      selectedDatasetName: null,
      annotationStatuses: ['All', 'Finished', 'In progress', 'Not started'], // Annotation statuses
      selectedAnnotationStatus: null, // Default annotation status to null for empty filter
      headers: [
        { text: 'Annotator', value: 'annotator' },
        { text: 'Label', value: 'label' },
        { text: 'Date', value: 'date' },
        { text: 'Example Text', value: 'example_text' },
        { text: 'Number of Annotations', value: 'numberOfAnnotations' },
      ],
      perspectiveHeaders: [
        { text: 'Perspective Question', value: 'question' },
        { text: 'Perspective Answer', value: 'answer' },
        { text: 'Answered By', value: 'answered_by' },
        { text: 'Answer Date', value: 'answer_date' },
      ],
      annotations: [], // Initialize as empty array
      perspectives: [], // Initialize perspectives array
      loading: false,
      loadingPerspectives: false,
      taskId: null,
      perspectivesTaskId: null,
      polling: null,
      perspectivesPolling: null,
      downloadReady: false,
      perspectivesDownloadReady: false,
      mdiMagnify,
      showExportDialog: false,
      selectedExportFormat: 'pdf',
    };
  },
  computed: {
    projectId() {
      return this.$route.params.id
    }
  },
  methods: {
    async fetchDatasetNames() {
      try {
        const response = await this.$repositories.example.fetchDatasetNames(this.projectId);
        this.datasetNames = response.datasetNames;
      } catch (error) {
        console.error("Error fetching dataset names:", error);
        this.$toasted.error('Error loading dataset names');
      }
    },

    async generateReport() {
      this.loading = true;
      this.downloadReady = false;
      this.annotations = []; // Clear previous annotations
      try {
        this.taskId = await this.$repositories.annotationHistory.prepare(
          this.projectId,
          this.selectedDatasetName,
          this.selectedAnnotationStatus
        );
        this.pollTaskStatus();
      } catch (error) {
        console.error("Error generating report:", error);
        this.$toasted.error('Error generating report');
        this.loading = false;
      }
    },

    async generatePerspectivesReport() {
      this.loadingPerspectives = true;
      this.perspectivesDownloadReady = false;
      this.perspectives = []; // Clear previous perspectives
      try {
        this.perspectivesTaskId = await this.$repositories.annotationHistory.prepare(
          this.projectId,
          this.selectedDatasetName,
          this.selectedAnnotationStatus
        );
        this.pollPerspectivesTaskStatus();
      } catch (error) {
        console.error("Error generating perspectives report:", error);
        this.$toasted.error('Error generating perspectives report');
        this.loadingPerspectives = false;
      }
    },

    pollTaskStatus() {
      if (this.polling) {
        clearInterval(this.polling);
        this.polling = null;
      }
      
      this.polling = setInterval(async () => {
        if (!this.taskId) {
          clearInterval(this.polling);
          this.polling = null;
          return;
        }

        try {
          const res = await this.$repositories.taskStatus.get(this.taskId);
          console.log("Task status response for annotations:", res);

          if (res && res.ready) {
            if (!res.error) { // Consider success if ready and no error
              clearInterval(this.polling);
              this.polling = null;
              this.loading = false;
              
              // Fetch the actual data for the table
              const data = await this.$repositories.annotationHistory.fetch(
                this.projectId,
                this.taskId
              );
              
              this.annotations = data.map(item => ({
                ...item,
                date: new Date(item.date).toLocaleString() // Format date
              }));
              
              console.log("Fetched annotations:", this.annotations);
              this.downloadReady = true;
              this.$toasted.success('Annotations report generated successfully!');
            } else { // Consider failure if ready and has error
              clearInterval(this.polling);
              this.polling = null;
              this.loading = false;
              this.$toasted.error(`Error generating annotations report: ${res.error || 'Unknown error'}`);
            }
          }
        } catch (error) {
          console.error("Error polling task status:", error);
          this.$toasted.error('Error polling report status');
          clearInterval(this.polling);
          this.polling = null;
          this.loading = false;
        }
      }, 1000);
    },

    pollPerspectivesTaskStatus() {
      if (this.perspectivesPolling) {
        clearInterval(this.perspectivesPolling);
        this.perspectivesPolling = null;
      }
      
      this.perspectivesPolling = setInterval(async () => {
        if (!this.perspectivesTaskId) {
          clearInterval(this.perspectivesPolling);
          this.perspectivesPolling = null;
          return;
        }

        try {
          const res = await this.$repositories.taskStatus.get(this.perspectivesTaskId);
          console.log("Task status response for perspectives:", res);

          if (res && res.ready) {
            if (!res.error) { // Consider success if ready and no error
              clearInterval(this.perspectivesPolling);
              this.perspectivesPolling = null;
              this.loadingPerspectives = false;
              
              // Fetch the actual data for the table
              const data = await this.$repositories.annotationHistory.fetch(
                this.projectId,
                this.perspectivesTaskId
              );
              console.log("Raw data fetched for perspectives:", data);
              
              // Process only perspectives data
              const perspectivesData = data.reduce((acc, item, index) => {
                let currentPerspectives = [];
                console.log(`Processing item ${index}: item.perspectives type: ${typeof item.perspectives}, value:`, item.perspectives);

                // Ensure item.perspectives is a non-empty string before attempting JSON.parse
                if (typeof item.perspectives === 'string') {
                  if (item.perspectives.trim().length > 0) { 
                    try {
                      // Log the string before parsing
                      console.log(`Attempting to parse JSON string for item ${index}:`, item.perspectives);
                      currentPerspectives = JSON.parse(item.perspectives);
                    } catch (e) {
                      console.error("Error parsing perspectives data (string):", e, item.perspectives);
                      currentPerspectives = [];
                    }
                  } else {
                    console.log(`Item ${index}.perspectives is an empty or whitespace-only string, setting to empty array.`);
                    currentPerspectives = [];
                  }
                } else if (Array.isArray(item.perspectives)) {
                  console.log(`Item ${index}.perspectives is already an array:`, item.perspectives);
                  currentPerspectives = item.perspectives;
                } else {
                  console.log(`Item ${index}.perspectives is neither a string nor an array (or is null/undefined). Setting to empty array.`, item.perspectives);
                  currentPerspectives = []; // Ensure it's an array if it's null/undefined/other
                }

                if (Array.isArray(currentPerspectives)) {
                  currentPerspectives.forEach(perspective => {
                    acc.push({
                      ...perspective,
                      answer_date: new Date(perspective.answer_date).toLocaleString()
                    });
                  });
                }
                return acc;
              }, []);
              
              this.perspectives = perspectivesData;
              console.log("Fetched perspectives (after processing):", this.perspectives);
              this.perspectivesDownloadReady = true;
              this.$toasted.success('Perspectives report generated successfully!');
            } else { // Consider failure if ready and has error
              clearInterval(this.perspectivesPolling);
              this.perspectivesPolling = null;
              this.loadingPerspectives = false;
              this.$toasted.error(`Error generating perspectives report: ${res.error || 'Unknown error'}`);
            }
          }
        } catch (error) {
          console.error("Error polling perspectives task status:", error);
          this.$toasted.error('Error polling perspectives report status');
          clearInterval(this.perspectivesPolling);
          this.perspectivesPolling = null;
          this.loadingPerspectives = false;
        }
      }, 1000);
    },

    async downloadReport() {
      this.loading = true;
      try {
        const downloadTaskId = await this.$repositories.annotationHistory.prepare(
          this.projectId,
          this.selectedDatasetName,
          this.selectedAnnotationStatus
        );

        let downloadPolling = null;
        downloadPolling = setInterval(async () => {
          const res = await this.$repositories.taskStatus.get(downloadTaskId);
          console.log("Download task status response for annotations:", res);
          if (res && res.ready) {
            if (!res.error) { // Consider success if ready and no error
              clearInterval(downloadPolling);
              this.loading = false;
              this.$repositories.annotationHistory.downloadFile(this.projectId, downloadTaskId);
              this.$toasted.success('Annotations report downloaded successfully!');
            } else { // Consider failure if ready and has error
              clearInterval(downloadPolling);
              this.loading = false;
              this.$toasted.error(`Error downloading annotations report: ${res.error || 'Unknown error'}`);
            }
          }
        }, 1000);

      } catch (error) {
        console.error("Error initiating download:", error);
        this.$toasted.error('Error initiating annotations report download');
        this.loading = false;
      }
    },

    async downloadPerspectivesReport() {
      this.loadingPerspectives = true;
      try {
        const downloadTaskId = await this.$repositories.annotationHistory.prepare(
          this.projectId,
          this.selectedDatasetName,
          this.selectedAnnotationStatus
        );

        let downloadPolling = null;
        downloadPolling = setInterval(async () => {
          const res = await this.$repositories.taskStatus.get(downloadTaskId);
          console.log("Download task status response for perspectives:", res);
          if (res && res.ready) {
            if (!res.error) { // Consider success if ready and no error
              clearInterval(downloadPolling);
              this.loadingPerspectives = false;
              this.$repositories.annotationHistory.downloadFile(this.projectId, downloadTaskId);
              this.$toasted.success('Perspectives report downloaded successfully!');
            } else { // Consider failure if ready and has error
              clearInterval(downloadPolling);
              this.loadingPerspectives = false;
              this.$toasted.error(`Error downloading perspectives report: ${res.error || 'Unknown error'}`);
            }
          }
        }, 1000);

      } catch (error) {
        console.error("Error initiating perspectives download:", error);
        this.$toasted.error('Error initiating perspectives report download');
        this.loadingPerspectives = false;
      }
    },

    resetReportState() {
      if (this.polling) {
        clearInterval(this.polling);
        this.polling = null;
      }
      if (this.perspectivesPolling) {
        clearInterval(this.perspectivesPolling);
        this.perspectivesPolling = null;
      }
      this.taskId = null;
      this.perspectivesTaskId = null;
      this.downloadReady = false;
      this.perspectivesDownloadReady = false;
      this.loading = false;
      this.loadingPerspectives = false;
      this.annotations = []; // Clear table data on reset
      this.perspectives = []; // Clear perspectives data on reset
    },

    clearFilters() {
      this.selectedDatasetName = null;
      this.selectedAnnotationStatus = null;
      // Optionally regenerate report after clearing filters
      this.generateReport();
    },

    fetchData() {
      // This method was a placeholder. Now it will be called by pollTaskStatus
      // No longer needed for direct data fetching on created hook.
    },

    async handleExport() {
      this.showExportDialog = false
      if (this.selectedExportFormat === 'pdf') {
        await this.exportPDF()
      } else {
        await this.exportCSV()
      }
    },

    async exportPDF() {
      try {
        // First, trigger the PDF generation task
        const response = await this.$axios.get(
          `/v1/projects/${this.projectId}/annotation-history-pdf`,
          {
            params: {
              dataset_name: this.selectedDatasetName,
              annotation_status: this.selectedAnnotationStatus
            }
          }
        )

        const taskId = response.data.task_id
        let attempts = 0
        const maxAttempts = 30 // 30 seconds timeout

        // Poll for task completion
        const pollInterval = setInterval(async () => {
          try {
            const statusResponse = await this.$axios.post(
              `/v1/projects/${this.projectId}/annotation-history-pdf`,
              { task_id: taskId }
            )

            if (statusResponse.data.status === 'processing') {
              attempts++
              if (attempts >= maxAttempts) {
                clearInterval(pollInterval)
                this.$toasted.error('PDF generation timed out')
              }
              return
            }

            // Task is complete, download the PDF
            clearInterval(pollInterval)
            const blob = new Blob([statusResponse.data], { type: 'application/pdf' })
            const url = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', `annotation_history_${new Date().toISOString()}.pdf`)
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            window.URL.revokeObjectURL(url)
            this.$toasted.success('PDF exported successfully!')
          } catch (error) {
            clearInterval(pollInterval)
            console.error('Error polling PDF status:', error)
            this.$toasted.error('Failed to export PDF')
          }
        }, 1000)
      } catch (error) {
        console.error('Error initiating PDF export:', error)
        this.$toasted.error('Failed to export PDF')
      }
    },

    exportCSV() {
      try {
        const delimiter = ';'
        const rows = [
          ['Annotator', 'Label', 'Date', 'Example Text', 'Number of Annotations']
        ]

        // Add annotations data
        const annotationRows = this.annotations.map(item => [
          item.annotator,
          item.label,
          item.date,
          item.example_text,
          item.numberOfAnnotations
        ])
        rows.push(...annotationRows)

        // Add perspectives data if available
        if (this.perspectives && this.perspectives.length > 0) {
          rows.push([]) // Empty row as separator
          rows.push(['Perspectives'])
          rows.push(['Question', 'Answer', 'Answered By', 'Answer Date'])
          
          const perspectiveRows = this.perspectives.map(item => [
            item.question,
            item.answer,
            item.answered_by,
            item.answer_date
          ])
          rows.push(...perspectiveRows)
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
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `annotation_history_${new Date().toISOString()}.csv`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        this.$toasted.success('CSV exported successfully!')
      } catch (error) {
        console.error('Error exporting CSV:', error)
        this.$toasted.error('Failed to export CSV')
      }
    }
  },
  created() {
    this.fetchDatasetNames();
    // this.fetchData(); // No longer calling fetchData directly on created
  },
  beforeDestroy() {
    clearInterval(this.polling);
    clearInterval(this.perspectivesPolling);
  },
};
</script>

<style scoped>
</style> 