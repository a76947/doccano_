<script>
import { Pie } from 'vue-chartjs'

export default {
  extends: Pie,
  props: {
    chartData: {
      type: Object,
      required: true
    },
    options: {
      type: Object,
      default: () => ({
        responsive: true,
        maintainAspectRatio: false
      })
    }
  },
  
  mounted() {
    // Render once on mount, no watchers to cause loops
    this.renderChart(this.chartData, this.options);
  }
  
  // No watchers - will not auto-update on data changes
  // Parent must provide a new key to force re-rendering
}
</script>