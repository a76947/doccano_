<script>
import { HorizontalBar, mixins } from 'vue-chartjs'
const { reactiveProp } = mixins

export default {
  extends: HorizontalBar,
  mixins: [reactiveProp],
  props: {
    chartData: {
      type: Object,
      default: () => {},
      required: true
    },
    options: {
      type: Object,
      default: null
    }
  },

  mounted() {
    // Use options from props if provided, otherwise use defaults
    const chartOptions = this.options || {
      scales: {
        y: {
          barPercentage: 0.3
        },
        x: {
          ticks: {
            beginAtZero: true,
            min: 0
          }
        }
      },
      maintainAspectRatio: false,
      legend: {
        display: false
      }
    };
    
    this.renderChart(this.chartData, chartOptions)
  },
  
  watch: {
    // Re-render when options change
    options: {
      handler() {
        this.renderChart(this.chartData, this.options || {})
      },
      deep: true
    }
  }
}
</script>
