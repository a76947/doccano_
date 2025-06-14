<script>
import { Pie, mixins } from 'vue-chartjs'
const { reactiveProp } = mixins

export default {
  extends: Pie,
  mixins: [reactiveProp],
  props: {
    chartData: {
      type: Object,
      required: true
    },
    options: {
      type: Object,
      default: () => ({
        responsive: true,
        maintainAspectRatio: false,
        legend: {
          display: true,
          position: 'right',
          labels: {
            boxWidth: 12,
            padding: 10
          }
        },
        tooltips: {
          enabled: true,
          mode: 'index',
          intersect: false
        }
      })
    }
  },
  
  watch: {
    chartData: {
      handler(newData) {
        console.log('Chart data changed:', newData)
        this.$nextTick(() => {
          this.renderChart(newData, this.options)
        })
      },
      deep: true
    }
  },
  
  mounted() {
    console.log('PieChart mounted with data:', this.chartData)
    this.$nextTick(() => {
      this.renderChart(this.chartData, this.options)
    })
  }
}
</script>

<style scoped>
canvas {
  width: 100% !important;
  height: 100% !important;
  max-width: 100%;
  max-height: 100%;
}
</style>