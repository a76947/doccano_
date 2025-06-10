<template>
  <v-card>
    <v-card-title>
      <v-row align="center">
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="search"
            label="Search"
            prepend-icon="mdi-magnify"
            single-line
            hide-details
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6" class="text-right">
          <v-btn-toggle
            v-model="sortOrder"
            mandatory
            @change="updateSort"
          >
            <v-btn small value="desc">
              <v-icon>mdi-sort-descending</v-icon>
              Descending
            </v-btn>
            <v-btn small value="asc">
              <v-icon>mdi-sort-ascending</v-icon>
              Ascending
            </v-btn>
          </v-btn-toggle>
        </v-col>
      </v-row>
    </v-card-title>

    <!-- Data Table -->
    <v-data-table
      :headers="headers"
      :items="sortedDiscrepancies"
      :search="search"
      :loading="loading"
      :items-per-page="10"
      class="elevation-1"
    >
      <template #[`item.text`]="{ item }">
        <div class="text-truncate" style="max-width: 300px;">
          {{ item.text }}
        </div>
      </template>

      <template #[`item.labels`]="{ item }">
        <v-simple-table dense class="dataset-table">
          <template #default>
            <thead>
              <tr>
                <th class="dataset-header">Dataset Label</th>
                <th class="dataset-header">Percentage</th>
                <th class="dataset-header">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(percentage, label) in sortedPercentages(item.percentages)" 
              :key="label" class="dataset-row">
                <td class="dataset-cell">{{ label }}</td>
                <td class="dataset-cell">{{ percentage.toFixed(2) }}%</td>
                <td class="dataset-cell">
                  <v-chip
                    :color="percentage >= 70 ? 'success' : 'error'"
                    small
                    class="status-chip"
                  >
                    {{ percentage >= 70 ? 'Agreement' : 'Disagreement' }}
                  </v-chip>
                </td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </template>

      <template #[`item.is_discrepancy`]="{ item }">
        <v-chip
          :color="item.is_discrepancy ? 'error' : 'success'"
          small
          class="status-chip"
        >
          {{ item.is_discrepancy ? 'Disagreement' : 'Agreement' }}
        </v-chip>
      </template>

      <template #[`item.max_percentage`]="{ item }">
        <span class="percentage-value">{{ item.max_percentage.toFixed(2) }}%</span>
      </template>
    </v-data-table>

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
      sortOrder: 'desc',
      search: '',
      headers: [
        { text: 'Text', value: 'text', sortable: true },
        { text: 'Dataset Labels', value: 'labels', sortable: false },
        { text: 'Overall Status', value: 'is_discrepancy', sortable: true },
        { text: 'Max Percentage', value: 'max_percentage', sortable: true }
      ]
    };
  },

  computed: {
    projectId() {
      return this.$route.params.id;
    },
    sortedDiscrepancies() {
      return [...this.discrepancies].sort((a, b) => {
        return this.sortOrder === 'asc' ? a.max_percentage - b.max_percentage : b.max_percentage - a.max_percentage;
      });
    }
  },

  mounted() {
    this.fetchDiscrepancies();
  },

  methods: {
    async fetchDiscrepancies() {
      try {
        const response = await this.$services.discrepancy.listDiscrepancie(this.projectId);
        this.discrepancies = response.discrepancies || [];
      } catch (err) {
        console.error('Error fetching discrepancies:', err);
        this.snackbarErrorMessage = 'Failed to fetch discrepancies. Please try again later.';
        this.snackbarError = true;
      } finally {
        this.loading = false;
      }
    },

    updateSort() {
      // A ordenação é feita automaticamente pelo computed property
    },

    sortedPercentages(percentages) {
      const sorted = Object.entries(percentages).sort((a, b) => {
        return this.sortOrder === 'asc' ? a[1] - b[1] : b[1] - a[1];
      });
      return Object.fromEntries(sorted);
    }
  }
};
</script>

<style scoped>
.v-data-table {
  width: 100%;
}

.dataset-table {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  margin: 8px 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.dataset-header {
  background-color: #f5f5f5 !important;
  font-weight: 600 !important;
  color: #424242 !important;
  padding: 8px 16px !important;
  border-bottom: 2px solid #e0e0e0 !important;
}

.dataset-row {
  border-bottom: 1px solid #e0e0e0;
}

.dataset-row:last-child {
  border-bottom: none;
}

.dataset-cell {
  padding: 12px 16px !important;
  font-size: 0.9rem;
}

.status-chip {
  font-weight: 500;
  min-width: 100px;
  justify-content: center;
}

.percentage-value {
  font-weight: 600;
  color: #424242;
}

/* Estilo para o texto truncado */
.text-truncate {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

/* Estilo para a tabela principal */
.v-data-table ::v-deep th {
  font-weight: 600 !important;
  color: #424242 !important;
  background-color: #f5f5f5 !important;
}

.v-data-table ::v-deep td {
  padding: 16px !important;
}

/* Estilo para as linhas alternadas */
.v-data-table ::v-deep tbody tr:nth-of-type(odd) {
  background-color: #fafafa;
}

/* Estilo para hover nas linhas */
.v-data-table ::v-deep tbody tr:hover {
  background-color: #f5f5f5;
}
</style>