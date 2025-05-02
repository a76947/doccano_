<template>
  <v-card>
    <v-card-title>
      {{ chartTitle }}
      <v-spacer></v-spacer>
      <v-btn icon @click="refreshData" :loading="loading">
        <v-icon>mdi-refresh</v-icon>
      </v-btn>
    </v-card-title>
    
    <v-card-text>
      <!-- Filter Controls -->
      <v-row class="mb-4">
        <v-col cols="12" sm="4">
          <v-select
            v-model="selectedLabels"
            :items="availableLabels"
            label="Filter by Label"
            multiple
            chips
            small-chips
            clearable
            @change="applyFilters"
          ></v-select>
        </v-col>
        <v-col cols="12" sm="4">
          <v-select
            v-model="selectedAssignee"
            :items="availableAssignees"
            label="Filter by Assignee"
            clearable
            @change="applyFilters"
          ></v-select>
        </v-col>
        <v-col cols="12" sm="4">
          <v-select
            v-model="annotationTypeFilter"
            :items="annotationTypes"
            label="Annotation Type"
            clearable
            @change="applyFilters"
          ></v-select>
        </v-col>
      </v-row>
      
      <v-row v-if="filterActive" class="mb-2">
        <v-col cols="12">
          <v-chip-group>
            <v-chip
              v-for="(filter, i) in activeFilters"
              :key="i"
              close
              @click:close="removeFilter(filter.type, filter.value)"
            >
              {{ filter.label }}: {{ filter.value }}
            </v-chip>
            <v-btn x-small text color="primary" @click="clearFilters">
              Clear All Filters
            </v-btn>
          </v-chip-group>
        </v-col>
      </v-row>
      
      <div class="chart-container" style="position: relative; height: 300px; 
      margin-top: 60px; margin-bottom: 00px;">
        <pie-chart
          v-if="chartData && chartKey"
          :key="chartKey" 
          :chart-data="chartData"
          ref="chart"
        />
      </div>
      
      <v-row style="margin-top: 500px !important;" class="stats-row">
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
    </v-card-text>

    <v-snackbar
      v-model="snackbar"
      :color="snackbarColor"
      :timeout="5000"
      top
      center-x
    >
      {{ snackbarMessage }}
      <template v-slot:action="{ attrs }">
        <v-btn
          text
          v-bind="attrs"
          @click="snackbar = false"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </v-card>
</template>

<script>
import PieChart from './PieChart'

export default {
  components: {
    PieChart
  },
  
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
      chartKey: 0,
      
      // Span distribution data
      spanDistribution: {},
      spanTypes: [],
      
      // Add snackbar properties
      snackbar: false,
      snackbarMessage: '',
      snackbarColor: 'error',
      
      selectedLabels: [],
      selectedAssignee: null,
      annotationTypeFilter: null,
      availableLabels: [],
      availableAssignees: [],
      annotationTypes: [
        { text: 'Has Categories', value: 'category' },
        { text: 'Has Spans', value: 'span' },
        { text: 'Has Relations', value: 'relation' },
        { text: 'No Annotations', value: 'none' }
      ],
      chartColors: ['#4CAF50', '#FFC107', '#2196F3', '#F44336', '#9C27B0', '#FF9800', 
                    '#795548', '#607D8B', '#E91E63', '#3F51B5', '#009688', '#CDDC39'],
      localStats: null
    }
  },
  
  computed: {
    chartTitle() {
      const selectedSpanLabels = this.selectedLabels.filter(label => label.startsWith('span:'));
      
      if (selectedSpanLabels.length > 0) {
        return selectedSpanLabels.length === 1 ? 'Selected Label Distribution' : 'Selected Labels Distribution';
      } else if (this.selectedAssignee) {
        return `${this.selectedAssignee}'s Annotation Distribution`;
      } else if (this.annotationTypeFilter) {
        return `${this.getAnnotationTypeLabel(this.annotationTypeFilter)} Distribution`;
      } else {
        return 'Annotation Progress';
      }
    },
    
    chartData() {
      // Always return span distribution data
      return this.getSpanDistributionChartData();
    },
    
    filterActive() {
      return this.selectedLabels.length > 0 || 
             this.selectedAssignee !== null || 
             this.annotationTypeFilter !== null;
    },
    
    activeFilters() {
      const filters = [];
      
      if (this.selectedLabels.length > 0) {
        this.selectedLabels.forEach(label => {
          filters.push({
            type: 'label',
            value: label,
            label: 'Label'
          });
        });
      }
      
      if (this.selectedAssignee) {
        filters.push({
          type: 'assignee',
          value: this.selectedAssignee,
          label: 'Assignee'
        });
      }
      
      if (this.annotationTypeFilter) {
        filters.push({
          type: 'annotationType',
          value: this.getAnnotationTypeLabel(this.annotationTypeFilter),
          label: 'Annotation Type'
        });
      }
      
      return filters;
    }
  },
  
  watch: {
    stats: {
      handler() {
        this.updateChart();
      },
      deep: true
    },
    
    selectedLabels() {
      this.fetchSpanDistribution();
      this.updateChart();
    },
    
    selectedAssignee() {
      this.fetchSpanDistribution();
      this.updateChart();
    },
    
    annotationTypeFilter() {
      this.fetchSpanDistribution();
      this.updateChart();
    }
  },
  
  async mounted() {
    await this.loadFilterOptions();
    await this.fetchSpanDistribution();
    
    this.$nextTick(() => {
      this.updateChart();
    });
  },
  
  methods: {
    async loadFilterOptions() {
      try {
        const labelTypes = [];
        
        try {
          const categoryTypes = await this.$services.categoryType.list(this.projectId);
          categoryTypes.forEach(type => labelTypes.push({
            text: `Category: ${type.text}`,
            value: `category:${type.id}`
          }));
        } catch (e) { }
        
        try {
          const spanTypes = await this.$services.spanType.list(this.projectId);
          spanTypes.forEach(type => labelTypes.push({
            text: `Label: ${type.text}`,
            value: `span:${type.id}`
          }));
        } catch (e) { }
        
        try {
          const relationTypes = await this.$services.relationType.list(this.projectId);
          relationTypes.forEach(type => labelTypes.push({
            text: `Relation: ${type.text}`,
            value: `relation:${type.id}`
          }));
        } catch (e) { }
        
        this.availableLabels = labelTypes;
        
        try {
          const members = await this.$repositories.member.list(this.projectId);
          this.availableAssignees = members.map(member => ({
            text: member.username,
            value: member.username
          }));
        } catch (e) {
          console.error('Error loading members:', e);
        }
      } catch (error) {
        console.error('Error loading filter options:', error);
        this.$toasted.error('Failed to load filter options');
      }
    },
    
    async fetchSpanDistribution() {
      try {
        this.$emit('update:loading', true);
        if (this.spanTypes.length === 0) {
          try {
            this.spanTypes = await this.$services.spanType.list(this.projectId);
          } catch (error) {
            console.error('Failed to fetch span types:', error);
            // Continue with empty spanTypes array
          }
        }
        
        // Add filters to the span distribution request
        const params = new URLSearchParams();
        
        if (this.selectedLabels.length > 0) {
          // Group labels by type (category, span, relation)
          const labelsByType = {
            category: [],
            span: [],
            relation: []
          };
          
          this.selectedLabels.forEach(labelValue => {
            const [type, id] = labelValue.split(':');
            if (labelsByType[type]) {
              labelsByType[type].push(id);
            }
          });
          
          // Add parameters for each label type
          Object.entries(labelsByType).forEach(([type, ids]) => {
            if (ids.length > 0) {
              // For each label type, add one label_type parameter
              params.append('label_type', type);
              
              // Add each ID as a separate label_id parameter
              ids.forEach(id => {
                params.append('label_id', id);
              });
            }
          });
        }
        
        if (this.selectedAssignee) {
          params.append('assignee', this.selectedAssignee);
        }
        
        if (this.annotationTypeFilter) {
          const typeMapping = {
            'category': 'hasCategories',
            'span': 'hasSpans',
            'relation': 'hasRelations', 
            'none': 'noAnnotations'
          };
          
          params.append('annotation_type', typeMapping[this.annotationTypeFilter] || this.annotationTypeFilter);
        }
        
        const queryString = params.toString();
        const url = queryString ? `?${queryString}` : '';
        
        try {
this.spanDistribution = await this.$repositories.metrics.fetchSpanDistribution(this.projectId, url);
          console.log('Raw span distribution data:', this.spanDistribution);
        } catch (error) {
          // Database connectivity error
          console.error('Failed to fetch span distribution data:', error);
          
          // Different error messages based on error type
          if (error.message && error.message.includes('Network Error')) {
            this.showError('Database connection lost. Please check your network connection and try again.');
          } else if (error.response && error.response.status === 500) {
            this.showError('Couldn\'t aply filters. Database is not unreachable please try again later.');
          } else if (error.response && error.response.status === 404) {
            this.showError('API endpoint not found. Please check if the server is running.');
          } else {
            this.showError('Failed to load data. Database might be disconnected.');
          }
          
          // Keep previous data if available, or set empty object
          if (!this.spanDistribution || Object.keys(this.spanDistribution).length === 0) {
            this.spanDistribution = {};
          }
          
          // Return to prevent further processing
          return;
        }
      } catch (error) {
        console.error('Error in filter processing:', error);
        this.showError('An error occurred while applying filters. Please try again.');
        
        // Set empty data if none exists
        if (!this.spanDistribution) {
          this.spanDistribution = {};
        }
      } finally {
        this.$emit('update:loading', false);
      }
    },
    
    getSpanDistributionChartData() {
      if (!this.spanDistribution || !Object.keys(this.spanDistribution).length) {
        console.error('No span distribution data available');
        return {
          labels: [],
          datasets: [{ backgroundColor: [], data: [] }]
        };
      }
      
      // Get the spanTypes to display meaningful names instead of IDs
      const labelMap = {};
      if (this.spanTypes && this.spanTypes.length > 0) {
        this.spanTypes.forEach(type => {
          labelMap[type.id] = type.text;
        });
      }
      
      // Log label mapping for debugging
      console.log('Label ID to name mapping:', labelMap);
      
      // Combine all users' data
      const combinedData = {};
      for (const user in this.spanDistribution) {
        for (const labelId in this.spanDistribution[user]) {
          if (!combinedData[labelId]) {
            combinedData[labelId] = 0;
          }
          combinedData[labelId] += this.spanDistribution[user][labelId];
        }
      }
      
      console.log('Combined span data:', combinedData);
      
      // Get per-user data for assignee filtering
      const userTotals = {};
      for (const user in this.spanDistribution) {
userTotals[user] = Object.values(this.spanDistribution[user]).reduce((sum, count) => sum+count, 0);
      }
      console.log('User totals:', userTotals);
      
      // Calculate total annotated vs unannotated for default view
      const totalAnnotated = this.stats.annotated || 0;
      const totalPending = this.stats.unannotated || 0;
      
      // ---- HANDLE FILTERS ----
      
      // CASE 1: Label filter - show all selected labels
      const selectedSpanLabels = this.selectedLabels.filter(label => label.startsWith('span:'));
      console.log('Selected span labels for chart:', selectedSpanLabels);
      
      if (selectedSpanLabels.length > 0) {
        // Process all selected span labels
        const labelData = [];
        const labelColors = [];
        const labelNames = [];
        
        selectedSpanLabels.forEach((selectedLabel, index) => {
          const selectedLabelId = selectedLabel.split(':')[1];
          // Fix: Check the combinedData and ensure we're using the right key format
          // The issue is likely that the keys in combinedData are the label names, not IDs
          
          // Find the correct key by matching either the ID or the label name
          let selectedLabelCount = 0;
          const selectedLabelName = labelMap[selectedLabelId] || `Label ${selectedLabelId}`;
          
          // Try to find the count using the label name first
          if (combinedData[selectedLabelName] !== undefined) {
            selectedLabelCount = combinedData[selectedLabelName];
          } 
          // Then try using the ID (checking both string and number formats)
          else if (combinedData[selectedLabelId] !== undefined) {
            selectedLabelCount = combinedData[selectedLabelId];
          }
          // If still not found, try numeric ID
          else if (combinedData[Number(selectedLabelId)] !== undefined) {
            selectedLabelCount = combinedData[Number(selectedLabelId)];
          }
          
          console.log(`Processing label: ${selectedLabelName} (ID: ${selectedLabelId}) - Count: ${selectedLabelCount}`);
          console.log(`Available keys in combinedData: ${Object.keys(combinedData)}`);
          
          labelData.push(selectedLabelCount);
          labelColors.push(this.chartColors[index % this.chartColors.length]);
          labelNames.push(selectedLabelName);
        });
        
        // Fix: Calculate "Other Labels" count correctly
        const selectedLabelNames = selectedSpanLabels.map(label => {
          const id = label.split(':')[1];
          return labelMap[id] || `Label ${id}`;
        });
        
        const otherLabelsCount = Object.entries(combinedData)
          .filter(([key]) => !selectedLabelNames.includes(key))
          .reduce((sum, [, count]) => sum + count, 0);
        
        if (otherLabelsCount > 0) {
          labelData.push(otherLabelsCount);
          labelColors.push('#E0E0E0');
          labelNames.push('Other Labels');
        }
        
        console.log(`Filtering by ${selectedSpanLabels.length} labels:`, labelNames, labelData);
        
        return {
          labels: labelNames,
          datasets: [{
            backgroundColor: labelColors,
            data: labelData
          }]
        };
      }
      
      // CASE 2: Assignee filter - show spans by selected assignee
      if (this.selectedAssignee) {
        const assigneeData = this.spanDistribution[this.selectedAssignee] || {};
        
        // Create an array of [labelId, count] pairs sorted by count (descending)
        const sortedLabels = Object.entries(assigneeData)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 10); // Limit to top 10 for readability
        
        if (sortedLabels.length === 0) {
          return {
            labels: ['No span data for selected assignee'],
            datasets: [{
              backgroundColor: ['#E0E0E0'],
              data: [1]
            }]
          };
        }
        
        const labels = sortedLabels.map(([id]) => labelMap[id] || `Label ${id}`);
        const counts = sortedLabels.map(([, count]) => count);
        const colors = sortedLabels.map((_, i) => this.chartColors[i % this.chartColors.length]);
        
        return {
          labels,
          datasets: [{
            backgroundColor: colors,
            data: counts
          }]
        };
      }
      
      // CASE 3: Default view - show annotated vs pending
      if (!this.filterActive || this.annotationTypeFilter) {
        return {
          labels: ['Annotated Documents', 'Pending Documents'],
          datasets: [{
            backgroundColor: ['#4CAF50', '#FFC107'],
            data: [totalAnnotated, totalPending]
          }]
        };
      }
      
      // CASE 4: Show span distribution if other filters are active
      const sortedLabels = Object.entries(combinedData)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10); // Limit to top 10 for readability
      
      if (sortedLabels.length === 0) {
        return {
          labels: ['No span data available'],
          datasets: [{
            backgroundColor: ['#E0E0E0'],
            data: [1]
          }]
        };
      }
      
      const labels = sortedLabels.map(([id]) => labelMap[id] || `Label ${id}`);
      const counts = sortedLabels.map(([, count]) => count);
      const colors = sortedLabels.map((_, i) => this.chartColors[i % this.chartColors.length]);
      
      return {
        labels,
        datasets: [{
          backgroundColor: colors,
          data: counts
        }]
      };
    },
    
    updateChart() {
      this.chartKey += 1;
    },
    
    refreshData() {
      this.$emit('update:loading', true);
      this.fetchSpanDistribution();
    },
    
    applyFilters() {
      console.log('Applying filters:', {
        labels: this.selectedLabels,
        assignee: this.selectedAssignee,
        type: this.annotationTypeFilter
      });
      this.fetchSpanDistribution();
    },
    
    removeFilter(type, value) {
      if (type === 'label') {
        this.selectedLabels = this.selectedLabels.filter(label => label !== value);
      } else if (type === 'assignee') {
        this.selectedAssignee = null;
      } else if (type === 'annotationType') {
        this.annotationTypeFilter = null;
      }
      
      this.applyFilters();
    },
    
    clearFilters() {
      this.selectedLabels = [];
      this.selectedAssignee = null;
      this.annotationTypeFilter = null;
      this.applyFilters();
    },
    
    getAnnotationTypeLabel(value) {
      const found = this.annotationTypes.find(type => type.value === value);
      return found ? found.text : value;
    },
    
    showError(message) {
      this.snackbarMessage = message;
      this.snackbarColor = 'error';
      this.snackbar = true;
    }
  }
}
</script>

<style scoped>

.chart-container {
  position: relative;
  height: 280px !important;
  width: 100%;
  margin-top: 0px !important;
  margin-bottom: 0px !important;
}
</style>