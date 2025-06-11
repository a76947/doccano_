<template>
  <v-card>
    <v-card-title>
      Dataset Statistics
      <v-spacer></v-spacer>
      <v-text-field
        v-model="search"
        append-icon="mdi-magnify"
        label="Search"
        single-line
        hide-details
        class="mx-2"
      ></v-text-field>
    </v-card-title>
    
    <v-card-text>
      <v-row>
        <v-col cols="12" sm="4">
          <v-card outlined>
            <v-card-text class="text-center">
              <div class="text-h4">{{ stats.total }}</div>
              <div>Total Documents</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="4">
          <v-card outlined color="success" dark>
            <v-card-text class="text-center">
              <div class="text-h4">{{ stats.annotated }}</div>
              <div>Annotated Documents</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="4">
          <v-card outlined color="warning" dark>
            <v-card-text class="text-center">
              <div class="text-h4">{{ stats.unannotated }}</div>
              <div>Pending Documents</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      
      <!-- Filters Section -->
      <v-row class="mt-3">
        <v-col cols="12" sm="4">
          <v-select
            v-model="statusFilter"
            :items="statusOptions"
            label="Status"
            outlined
            dense
            clearable
            @change="onFilterChange"
          ></v-select>
        </v-col>
        <v-col cols="12" sm="4">
          <v-select
            v-model="annotationTypeFilter"
            :items="annotationTypeOptions"
            label="Annotation Type"
            outlined
            dense
            clearable
            @change="onFilterChange"
          ></v-select>
        </v-col>
        <v-col cols="12" sm="4">
          <v-btn
            color="primary"
            class="mt-1"
            @click="resetFilters"
          >
            Reset Filters
          </v-btn>
        </v-col>
      </v-row>
    </v-card-text>

    <!-- Use a unique key to ensure complete re-rendering -->
    <v-data-table
      :key="renderKey"
      :headers="headers"
      :items="tableItems" 
      :loading="loading"
      :search="search"
      :options.sync="options"
      :server-items-length="stats.filtered || stats.total || 0"
      :footer-props="{
        'items-per-page-options': [10, 20, 50, 100],
        showFirstLastPage: true
      }"
      @update:options="onOptionsChange"
    >
      <template #[`item.text`]="{ item }">
        <span class="text-truncate d-inline-block" style="max-width: 300px">
          {{ item.text }}
        </span>
      </template>
      
      <template #[`item.status`]="{ item }">
        <v-chip
          :color="item.annotated ? 'success' : 'warning'"
          small
        >
          {{ item.annotated ? 'Annotated' : 'Pending' }}
        </v-chip>
      </template>
    </v-data-table>
  </v-card>
</template>

<script>
export default {
  props: {
    stats: {
      type: Object,
      required: true,
      default: () => ({
        total: 0,
        annotated: 0,
        unannotated: 0,
        entries: []
      })
    },
    loading: {
      type: Boolean,
      default: false
    },
    projectId: {
      type: String,
      required: true
    }
  },

  data() {
    return {
      renderKey: 0, // This key will force re-render when changed
      search: '',
      headers: [
        { text: 'ID', value: 'id', sortable: true },
        { text: 'Text', value: 'text', sortable: true },
        { text: 'Status', value: 'status', sortable: true },
        { text: 'Category Annotations', value: 'categoryCount', sortable: true },
        { text: 'Span Annotations', value: 'spanCount', sortable: true },
        { text: 'Relation Annotations', value: 'relationCount', sortable: true },
        { text: 'Last Updated', value: 'updatedAt', sortable: true }
      ],
      options: {
        sortBy: ['updatedAt'],
        sortDesc: [true],
        page: 1,
        itemsPerPage: 20
      },
      statusFilter: null,
      statusOptions: [
        { text: 'Annotated', value: 'annotated' },
        { text: 'Pending', value: 'pending' }
      ],
      annotationTypeFilter: null,
      annotationTypeOptions: [
        { text: 'Has Categories', value: 'hasCategories' },
        { text: 'Has Spans', value: 'hasSpans' },
        { text: 'Has Relations', value: 'hasRelations' },
        { text: 'No Annotations', value: 'noAnnotations' }
      ],
      // Field mapping for sorting
      sortFieldMapping: {
        'id': 'id',
        'text': 'text',
        'status': 'status',
        'categoryCount': 'categoryCount',
        'spanCount': 'spanCount',
        'relationCount': 'relationCount',
        'updatedAt': 'updatedAt'
      },
      lastRequestParams: null // Track the last request to avoid duplicates
    }
  },

  computed: {
    // Create a computed property for table items to ensure reactivity
    tableItems() {
      return this.stats.entries || [];
    }
  },
  
  mounted() {
    // Initial data load when component is mounted
    console.log("Component mounted, fetching initial data");
    this.fetchFilteredData();
  },
  
  methods: {
    onFilterChange() {
      // Reset to first page when filters change
      this.options.page = 1;
      this.fetchFilteredData();
    },
    
    onOptionsChange(newOptions) {
      console.log('Options changed:', JSON.stringify(newOptions));
      
      // Always fetch data when the sorting options change
      const sortingChanged = 
        JSON.stringify(this.options.sortBy) !== JSON.stringify(newOptions.sortBy) ||
        JSON.stringify(this.options.sortDesc) !== JSON.stringify(newOptions.sortDesc);
      
      const pageChanged = 
        this.options.page !== newOptions.page ||
        this.options.itemsPerPage !== newOptions.itemsPerPage;
      
      if (sortingChanged || pageChanged) {
        this.options = JSON.parse(JSON.stringify(newOptions));
        console.log('Fetching new data due to changed options');
        this.fetchFilteredData();
      }
    },
    
    async fetchFilteredData() {
      // Generate request parameters
      const params = new URLSearchParams();
      params.append('page', this.options.page);
      params.append('page_size', this.options.itemsPerPage);
      
      // Add sorting parameters
      if (this.options.sortBy && this.options.sortBy.length > 0) {
        const frontendField = this.options.sortBy[0];
        const backendField = this.sortFieldMapping[frontendField] || frontendField;
        const sortDirection = this.options.sortDesc[0] ? '-' : '';
        params.append('ordering', `${sortDirection}${backendField}`);
        
        console.log(`Sorting by: ${sortDirection}${backendField} (from ${frontendField})`);
      }
      
      if (this.statusFilter) {
        params.append('status', this.statusFilter);
      }
      
      if (this.annotationTypeFilter) {
        params.append('annotation_type', this.annotationTypeFilter);
      }
      
      // Add a cache-busting parameter
      params.append('_t', new Date().getTime());
      
      console.log('Fetching with params:', params.toString());
      
      try {
        // Use the repository method instead of direct API call
        const response = await this.$repositories.metrics.fetchDatasetStatistics(
          this.projectId,
          params.toString()
        );
        
        // Log what we got back
        console.log('Response received, entry count:', response.entries.length);
        
        // Force update the parent component with new data
        this.$emit('update:stats', JSON.parse(JSON.stringify(response)));
        
        // Update render key to force re-render
        this.renderKey++;
      } catch (error) {
        console.error('Failed to fetch filtered data:', error);
        this.$toasted.error('Error loading dataset statistics');
      } finally {
        this.$emit('update:loading', false);
      }
    },
    
    resetFilters() {
      this.statusFilter = null;
      this.annotationTypeFilter = null;
      this.search = '';
      this.options.page = 1;
      this.fetchFilteredData();
    }
  }
}
</script>