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
          :items="reportTypes"
          v-model="selectedReportType"
          label="Report Type"
          solo
          dense
          hide-details
          class="col-md-4 col-12 mr-2"
        ></v-select>

        <v-spacer></v-spacer>
        <v-btn color="primary" class="mr-2" :loading="loading"
         :disabled="loading" @click="generateReport">
          GENERATE REPORT
        </v-btn>
        <v-btn :disabled="!downloadReady" @click="downloadReport">
          EXPORT REPORT
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
                  :items="datasetNames"
                  v-model="selectedDatasetName"
                  label="Total de Anotações"
                  solo
                  dense
                  hide-details
                  style="max-width: 250px; margin-right: 16px;"
                ></v-select>
                <v-select
                  :items="annotationStatuses"
                  v-model="selectedAnnotationStatus"
                  label="Annotation Status"
                  solo
                  dense
                  hide-details
                  style="max-width: 200px; margin-right: 16px;"
                ></v-select>
                <v-btn text @click="clearFilters">
                  CLEAR FILTERS
                </v-btn>
              </v-toolbar>
              <v-data-table
                :headers="headers"
                :items="annotations"
                :loading="loading"
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
  </v-container>
</template>

<script>
import { mdiMagnify } from '@mdi/js'

export default {
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
      annotations: [], // Initialize as empty array
      loading: false,
      taskId: null,
      polling: null,
      downloadReady: false,
      mdiMagnify,
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

    pollTaskStatus() {
      if (this.polling) {
        clearInterval(this.polling);
      }
      
      this.polling = setInterval(async () => {
        if (this.taskId) {
          try {
            const res = await this.$repositories.taskStatus.get(this.taskId);
            if (res.ready) {
              clearInterval(this.polling);
              this.loading = false;
              // Fetch the actual data for the table
              const data = await this.$repositories.annotationHistory.fetch
              (this.projectId, this.taskId);
              this.annotations = data.map(item => ({
                ...item,
                date: new Date(item.date).toLocaleString() // Format date
              }));
              console.log("Fetched annotations:", this.annotations);
              this.downloadReady = true;
              this.$toasted.success('Report generated successfully!');
            }
          } catch (error) {
            console.error("Error polling task status:", error);
            this.$toasted.error('Error polling report status');
            clearInterval(this.polling);
            this.loading = false;
          }
        }
      }, 1000);
    },

    async downloadReport() {
      // This method should trigger the actual file download
      this.loading = true;
      try {
        // Re-initiate the backend task specifically for downloading the file
        // The backend `AnnotationHistoryAPI` will handle the file download based on a POST request
        const downloadTaskId = await this.$repositories.annotationHistory.prepare(
          this.projectId,
          this.selectedDatasetName,
          this.selectedAnnotationStatus // Pass the selected status to the backend
        ); // Re-use prepare, or create a new method for pure download initiation

        // Poll for the download task status (similar to generateReport but for FileResponse)
        const downloadPolling = setInterval(async () => {
          try {
            const res = await this.$repositories.taskStatus.get(downloadTaskId);
            if (res.ready) {
              clearInterval(downloadPolling);
              this.loading = false;
              // Call a new method on the repository specifically for file download
              this.$repositories.annotationHistory.downloadFile(this.projectId, downloadTaskId);
              this.$toasted.success('Report downloaded successfully!');
            }
          } catch (error) {
            console.error("Error polling download task status:", error);
            this.$toasted.error('Error downloading report');
            clearInterval(downloadPolling);
            this.loading = false;
          }
        }, 1000);

      } catch (error) {
        console.error("Error initiating download:", error);
        this.$toasted.error('Error initiating report download');
        this.loading = false;
      }
    },

    resetReportState() {
      this.taskId = null;
      this.downloadReady = false;
      this.loading = false;
      this.annotations = []; // Clear table data on reset
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
  },
  created() {
    this.fetchDatasetNames();
    // this.fetchData(); // No longer calling fetchData directly on created
  },
  beforeDestroy() {
    clearInterval(this.polling);
  },
};
</script>

<style scoped>
</style> 