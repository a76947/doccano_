<script>
import { Bar } from 'vue-chartjs'

export default {
  name: 'BarChart',
  extends: Bar,
  props: {
    chartData: {
      type: Object,
      required: true
    },
    options: {
      type: Object,
      default: () => ({})
    }
  },

  data() {
    return {
      defaultOptions: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            display: false
          },
          x: {
            display: false
          }
        },
        plugins: {
          legend: {
            display: false
          }
        },
        barPercentage: 0.6,
        categoryPercentage: 0.6
      }
    }
  },

  mounted() {
    const chartOptions = {
      ...this.defaultOptions,
      ...this.options
    }
    
    this.renderChart(this.chartData, chartOptions)
  },
  
  watch: {
    chartData: {
      handler() {
        this.renderChart(this.chartData, {
          ...this.defaultOptions,
          ...this.options
        })
      },
      deep: true
    },
    options: {
      handler() {
        this.renderChart(this.chartData, {
          ...this.defaultOptions,
          ...this.options
        })
      },
      deep: true
    }
  }
}
</script>

<style scoped>
.chart-container {
  position: relative;
  width: 100%;
}
</style>
