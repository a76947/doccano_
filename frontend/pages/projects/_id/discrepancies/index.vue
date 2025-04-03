<template>
  <v-card>
    <v-card-title>
      <template v-if="!hasDiscrepancies">
        <v-alert type="info" dense class="mb-0">
          No discrepancies found for this project.
        </v-alert>
      </template>
      <template v-else>
        <v-alert type="info" dense class="mb-0">
          Below are the discrepancies identified for this project.
        </v-alert>
      </template>
    </v-card-title>

    <!-- Order Selector -->
    <v-row justify="end" class="mb-3">
      <v-btn small @click="toggleSortOrder">
        Sort by Percentage: {{ sortOrder === 'asc' ? 'Ascending' : 'Descending' }}
      </v-btn>
    </v-row>

    <!-- List of Discrepancies -->
    <v-expansion-panels v-if="hasDiscrepancies">
      <v-expansion-panel v-for="discrepancy in discrepancies" :key="discrepancy.id">
        <v-expansion-panel-header>
          <div class="d-flex align-center">
            <span class="font-weight-bold">Discrepancy Details</span>
            <v-spacer></v-spacer>
          </div>
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <div class="mb-2">
            <p><strong>Text:</strong> {{ truncateText(discrepancy.text, 200) }}</p>
            <p><strong>Percentages:</strong></p>
            <v-simple-table>
              <template #default>
                <thead>
                  <tr>
                    <th>Label</th>
                    <th>Percentage</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(percentage, label) in sortedPercentages(discrepancy.percentages)"
                    :key="label"
                  >
                    <td>{{ label }}</td>
                    <td>{{ percentage.toFixed(2) }}%</td>
                  </tr>
                </tbody>
              </template>
            </v-simple-table>
          </div>
        </v-expansion-panel-content>
      </v-expansion-panel>
    </v-expansion-panels>

    <!-- Snackbars -->
    <v-snackbar v-model="snackbar" timeout="3000" top color="success">
      {{ snackbarMessage }}
      <template #action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>

    <v-snackbar v-model="snackbarError" timeout="3000" top color="error">
      {{ snackbarErrorMessage }}
      <template #action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbarError = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-card>
</template>

<script>
export default {
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  data() {
    return {
      discrepancies: [],
      snackbar: false,
      snackbarMessage: '',
      snackbarError: false,
      snackbarErrorMessage: '',
      loading: true,
      sortOrder: 'asc',
    };
  },

  computed: {
    projectId() {
      return this.$route.params.id;
    },

    hasDiscrepancies() {
      return this.discrepancies && this.discrepancies.length > 0;
    },
  },

  mounted() {
    this.fetchDiscrepancies();
  },

  methods: {
    async fetchDiscrepancies() {
      try {
        const response = await this.$services.discrepancy.listDiscrepancie(this.projectId);
        console.log('API response:', response); // Debug response
        this.discrepancies = response.discrepancies || [];
        console.log('Discrepancies:', this.discrepancies); // Debug discrepancies
      } catch (err) {
        console.error('Error fetching discrepancies:', err);
        this.snackbarErrorMessage = 'Failed to fetch discrepancies. Please try again later.';
        this.snackbarError = true;
      } finally {
        this.loading = false;
      }
    },

    truncateText(text, maxLength) {
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },

    toggleSortOrder() {
      this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
    },

    sortedPercentages(percentages) {
      const sorted = Object.entries(percentages).sort((a, b) => {
        return this.sortOrder === 'asc' ? a[1] - b[1] : b[1] - a[1];
      });
      return Object.fromEntries(sorted);
    },
  },
};
</script>

<style scoped>
.discrepancies-page {
  font-family: Arial, sans-serif;
  padding: 20px;
}

.loading {
  font-size: 18px;
  color: #666;
}

.no-data {
  font-size: 16px;
  color: #999;
}

.discrepancy-item {
  margin-bottom: 20px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
}

.discrepancy-item p {
  margin: 5px 0;
}

.discrepancy-item ul {
  margin: 5px 0 0 20px;
}
</style>