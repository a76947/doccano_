<template>
  <v-card>
    <v-card-title>
      Dataset Statistics
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
      
      <div class="chart-container" style="position: relative; height: 300px; margin-bottom: 20px;">
        <pie-chart
          v-if="chartData && chartKey"
          :key="chartKey" 
          :chart-data="chartData"
          ref="chart"
        />
      </div>
      
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
    </v-card-text>
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
      chartKey: 0, // Start with 0
      
      // Filter state
      selectedLabels: [],
      selectedAssignee: null,
      annotationTypeFilter: null,
      
      // Available filter options (will be populated)
      availableLabels: [],
      availableAssignees: [],
      annotationTypes: [
        { text: 'Has Categories', value: 'category' },
        { text: 'Has Spans', value: 'span' },
        { text: 'Has Relations', value: 'relation' },
        { text: 'No Annotations', value: 'none' }
      ],
      
      // Chart customization
      chartColors: ['#4CAF50', '#FFC107', '#2196F3', '#F44336', '#9C27B0', '#FF9800'],
      
      // Add local stats copy for independent changes
      localStats: null
    }
  },
  
  computed: {
    chartData() {
      // Use the stats from props
      const data = this.stats || { total: 0, filtered: 0, annotated: 0, unannotated: 0 };
      
      // Check if we're filtering by label
      const hasLabelFilter = this.selectedLabels.length > 0;
      
      // Special case for label filtering
      if (hasLabelFilter && data.filtered !== data.total) {
        // Create a chart showing documents with the selected label vs all documents
        const withLabel = data.filtered || 0;
        const withoutLabel = data.total - withLabel;
        
        // Get the label text for display
        const labelTexts = this.selectedLabels.map(labelVal => {
          const found = this.availableLabels.find(l => l.value === labelVal);
          return found ? found.text : labelVal;
        });
        
        console.log('Label filter chart data:', {
          withLabel,
          withoutLabel,
          labelTexts
        });
        
        // Different visualization for label filtering
        return {
          labels: [
            `With ${labelTexts.join(', ')}`,
            `Without ${labelTexts.join(', ')}`
          ],
          datasets: [
            {
              backgroundColor: ['#2196F3', '#E0E0E0'], // Blue for label matches
              data: [withLabel, withoutLabel]
            }
          ]
        };
      }
      
      // Special case for assignee filtering - NEW CODE
      if (this.selectedAssignee && data.filtered !== data.total && !hasLabelFilter) {
        // The filtered count is documents assigned to this user
        const byAssignee = data.filtered || 0;
        // Total annotated minus those by this assignee = others
        const byOthers = data.annotated - byAssignee;
        
        // Make sure we don't have negative numbers
        const normalizedByOthers = byOthers < 0 ? 0 : byOthers;
        
        console.log('Assignee filter chart data:', {
          byAssignee,
          byOthers: normalizedByOthers,
          totalAnnotated: data.annotated
        });
        
        // Different visualization for assignee filtering
        return {
          labels: [
            `Annotated by ${this.selectedAssignee}`,
            `Annotated by others`
          ],
          datasets: [
            {
              backgroundColor: ['#9C27B0', '#E0E0E0'], // Purple for assignee's annotations
              data: [byAssignee, normalizedByOthers]
            }
          ]
        };
      }
      
      // For annotation type filters, use the existing method
      if (this.annotationTypeFilter) {
        return this.getAnnotationTypeChartData(data);
      }
      
      // Default: show annotated vs unannotated
      return {
        labels: ['Annotated', 'Pending'],
        datasets: [
          {
            backgroundColor: ['#4CAF50', '#FFC107'],
            data: [data.annotated, data.unannotated]
          }
        ]
      };
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
        // Simple update without deep cloning large objects
        this.updateChart();
      },
      deep: true
    },
    
    // Add watches for filters to ensure chart updates
    selectedLabels() {
      this.updateChart();
    },
    selectedAssignee() {
      this.updateChart();
    },
    annotationTypeFilter() {
      this.updateChart();
    }
  },
  
  async mounted() {
    await this.loadFilterOptions();
    // Force initial chart render
    this.$nextTick(() => {
      this.updateChart();
    });
  },
  
  methods: {
    async loadFilterOptions() {
      try {
        // Load available labels for filtering
        const labelTypes = [];
        
        // Combine category, span, and relation types if available
        try {
          const categoryTypes = await this.$services.categoryType.list(this.projectId);
          categoryTypes.forEach(type => labelTypes.push({
            text: `Category: ${type.text}`,
            value: `category:${type.id}`
          }));
        } catch (e) { /* Skip if not available */ }
        
        try {
          const spanTypes = await this.$services.spanType.list(this.projectId);
          spanTypes.forEach(type => labelTypes.push({
            text: `Span: ${type.text}`,
            value: `span:${type.id}`
          }));
        } catch (e) { /* Skip if not available */ }
        
        try {
          const relationTypes = await this.$services.relationType.list(this.projectId);
          relationTypes.forEach(type => labelTypes.push({
            text: `Relation: ${type.text}`,
            value: `relation:${type.id}`
          }));
        } catch (e) { /* Skip if not available */ }
        
        this.availableLabels = labelTypes;
        
        // Load available assignees (from members API)
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
    
    updateChart() {
      this.chartKey += 1; // Force re-render with key change
    },
    
    refreshData() {
      this.$emit('update:loading', true);
      this.fetchDatasetStats();
    },
    
    async fetchDatasetStats() {
      try {
        // Build query parameters based on active filters
        const params = new URLSearchParams();
        
        if (this.selectedLabels.length > 0) {
          // Process all selected labels
          const labelsByType = {
            category: [],
            span: [],
            relation: []
          };
          
          // Group labels by their type
          this.selectedLabels.forEach(labelValue => {
            const [type, id] = labelValue.split(':');
            if (labelsByType[type]) {
              labelsByType[type].push(id);
            }
          });
          
          // Add the first label of each type to the parameters
          Object.entries(labelsByType).forEach(([type, ids]) => {
            if (ids.length > 0) {
              params.append('label_type', type);
              params.append('label_id', ids[0]);
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
        
  const response = await this.$repositories.metrics.fetchDatasetStatistics(this.projectId, url);
        
        // Simple emit without deep cloning
        this.$emit('update:stats', response);
      } catch (error) {
        console.error('Failed to fetch dataset statistics:', error);
      } finally {
        this.$emit('update:loading', false);
      }
    },
    
    applyFilters() {
      console.log('Applying filters:', {
        labels: this.selectedLabels,
        assignee: this.selectedAssignee,
        type: this.annotationTypeFilter
      });
      this.fetchDatasetStats();
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
    
    getAnnotationTypeChartData(statsData) {
      // Create a more detailed breakdown based on annotation type
      switch (this.annotationTypeFilter) {
        case 'category':
          return {
            labels: ['Has Categories', 'No Categories'],
            datasets: [{
              backgroundColor: ['#4CAF50', '#FFC107'],
              data: [
                statsData.categoryAnnotated || 0, 
                statsData.total - (statsData.categoryAnnotated || 0)
              ]
            }]
          };
        case 'span':
          return {
            labels: ['Has Spans', 'No Spans'],
            datasets: [{
              backgroundColor: ['#2196F3', '#FFC107'],
              data: [
                statsData.spanAnnotated || 0, 
                statsData.total - (statsData.spanAnnotated || 0)
              ]
            }]
          };
        case 'relation':
          return {
            labels: ['Has Relations', 'No Relations'],
            datasets: [{
              backgroundColor: ['#9C27B0', '#FFC107'],
              data: [
                statsData.relationAnnotated || 0, 
                statsData.total - (statsData.relationAnnotated || 0)
              ]
            }]
          };
        case 'none':
          return {
            labels: ['No Annotations', 'Has Annotations'],
            datasets: [{
              backgroundColor: ['#F44336', '#4CAF50'],
              data: [
                statsData.unannotated || 0,
                statsData.annotated || 0
              ]
            }]
          };
        default:
          return {
            labels: ['Annotated', 'Pending'],
            datasets: [{
              backgroundColor: ['#4CAF50', '#FFC107'],
              data: [statsData.annotated, statsData.unannotated]
            }]
          };
      }
    }
  }
}
</script>

<style scoped>
.chart-container {
  position: relative;
  height: 300px;
  width: 100%;
}
</style>