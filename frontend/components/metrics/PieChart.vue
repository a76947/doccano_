<script>
import { Pie } from 'vue-chartjs'

export default {
  extends: Pie,
  props: {
    chartData: {
      type: Object,
      required: true
    }
  },
  
  data() {
    return {
      options: {
        responsive: true,
        maintainAspectRatio: false,
        legend: {
          position: 'bottom'
        },
        tooltips: {
          callbacks: {
            label(tooltipItem, data) {
              const dataset = data.datasets[tooltipItem.datasetIndex];
              const total = dataset.data.reduce((prev, current) => prev + current, 0);
              const currentValue = dataset.data[tooltipItem.index];
              const percentage = Math.floor(((currentValue/total) * 100) + 0.5);
              return data.labels[tooltipItem.index] + ': ' + currentValue + ' (' + percentage + '%)';
            }
          }
        }
      }
    }
  },
  
  mounted() {
    this.renderChart(this.chartData, this.options);
  },
  
  watch: {
    chartData: {
      handler() {
        if (this._chart) {
          this._chart.destroy();
        }
        this.renderChart(this.chartData, this.options);
      },
      deep: true
    }
  }
}
</script>