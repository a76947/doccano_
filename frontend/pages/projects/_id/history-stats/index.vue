<template>
  <v-card>
    <v-card-title class="align-center flex-wrap">
      <h2 class="text-h6 mb-4 mb-md-0 me-md-4">Estatísticas do Histórico de Anotações</h2>

      <!-- Select Dataset (placeholder, apenas um por enquanto) -->
      <v-select
        v-model="selectedDataset"
        :items="datasetOptions"
        item-text="text"
        item-value="value"
        label="Dataset"
        dense
        hide-details
        class="me-2"
        style="max-width: 200px"
        @change="onDatasetChange"
      />

      <!-- Select Versão -->
      <v-select
        v-model="selectedVersion"
        :items="versionOptions"
        label="Versão"
        dense
        hide-details
        clearable
        class="me-2"
        style="max-width: 150px"
        @change="applyFilters"
      />

      <!-- Filtro de data -->
      <v-menu v-model="dateMenu" :close-on-content-click="false" transition="scale-transition">
        <template #activator="{ on }">
          <v-text-field
            v-model="beforeFormatted"
            label="Antes de"
            prepend-icon="mdi-calendar"
            readonly
            dense
            v-on="on"
            hide-details
            style="max-width: 160px"
          />
        </template>
        <v-date-picker v-model="before" @change="applyFilters" scrollable />
      </v-menu>

      <!-- Button / dialog for filtering by Perspective answers -->
      <v-dialog v-model="perspectiveFilterDialog" max-width="600px">
        <template #activator="{ on, attrs }">
          <v-btn color="primary" dark v-bind="attrs" v-on="on" class="me-2">
            Filtrar por Perspectiva
          </v-btn>
        </template>
        <v-card>
          <v-card-title>Filtro de Perspectivas</v-card-title>
          <v-card-text>
            <v-container>
              <v-row v-for="group in perspectiveGroups" :key="group.id">
                <v-col cols="12">
                  <h3>{{ group.name }}</h3>
                  <v-row v-for="question in group.questions" :key="question.id">
                    <v-col cols="12">
                      <v-select
                        v-if="question.data_type === 'string' && question.options.length > 0"
                        v-model="selectedPerspectiveAnswers[question.id]"
                        :items="question.options"
                        :label="question.question"
                        multiple
                        chips
                        deletable-chips
                        clearable
                      />
                      <v-select
                        v-else-if="question.data_type === 'boolean'"
                        v-model="selectedPerspectiveAnswers[question.id]"
                        :items="['Yes', 'No']"
                        :label="question.question"
                        clearable
                      />
                      <v-text-field
                        v-else
                        v-model="selectedPerspectiveAnswers[question.id]"
                        :label="question.question"
                        type="number"
                        clearable
                      />
                    </v-col>
                  </v-row>
                </v-col>
              </v-row>
            </v-container>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn color="primary" text @click="applyPerspectiveFilters">Aplicar</v-btn>
            <v-btn text @click="clearPerspectiveFilters">Limpar</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <v-spacer />

      <!-- Export buttons -->
      <v-btn color="primary" outlined class="me-2" @click="exportCSV">
        Exportar CSV
      </v-btn>
      <v-btn color="primary" outlined @click="exportPDF">
        Exportar PDF
      </v-btn>
    </v-card-title>

    <v-divider />

    <v-card-text>
      <v-row>
        <v-col
          v-for="stat in displayedStats"
          :key="stat.version"
          cols="12"
          md="6"
          class="mb-8"
        >
          <v-card outlined>
            <v-card-title class="subtitle-2">
              Versão {{ stat.version }}
            </v-card-title>
            <v-card-text style="position:relative;height:400px;">
              <bar-chart
                :key="stat.version"
                :labels="stat.labels"
                :values="stat.votes"
                :chart-id="`chart_${stat.version}`"
                :ref="`chart_${stat.version}`"
              />
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Snackbar de erro -->
      <v-snackbar v-model="dbErrorVisible" :timeout="4000" color="error" top>
        {{ dbErrorMessage }}
        <v-btn text @click="dbErrorVisible = false">Fechar</v-btn>
      </v-snackbar>
    </v-card-text>
  </v-card>
</template>

<script>
import { Bar, mixins } from 'vue-chartjs'
const { reactiveProp } = mixins

const BarChart = {
  extends: Bar,
  mixins: [reactiveProp],
  props: ['labels', 'values'],
  mounted () { this.render() },
  watch: {
    values () { this.render() },
    labels () { this.render() }
  },
  methods: {
    render () {
      this.renderChart({
        labels: this.labels,
        datasets: [{ label: 'Percentagem', backgroundColor: '#42A5F5', data: this.values }]
      }, {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          yAxes: [{
            ticks: {
              beginAtZero: true,
              max: 100,
              callback: value => `${value}%`
            }
          }]
        },
        tooltips: {
          callbacks: {
            label: (tooltipItem) => `${parseFloat(tooltipItem.yLabel).toFixed(1)}%`
          }
        }
      })
    }
  }
}

export default {
  name: 'HistoryStats',
  components: { BarChart },
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],
  data () {
    return {
      stats: [],
      before: null,
      dateMenu: false,
      progress: 100,
      // Include a default "all" option so the user can view stats for all datasets
      datasetOptions: [{ text: 'Todos os Datasets', value: null }],
      selectedDataset: null,
      versionOptions: [],
      selectedVersion: null,
      // Perspective filters
      perspectiveFilterDialog: false,
      perspectiveGroups: [],
      selectedPerspectiveAnswers: {},
      // Snackbar erro BD
      dbErrorVisible: false,
      dbErrorMessage: ''
    }
  },
  computed: {
    projectId () { return this.$route.params.id },
    displayedStats () {
      if (this.selectedVersion !== null) {
        return this.stats.filter(s => s.version === this.selectedVersion)
      }
      return this.stats
    },
    beforeFormatted () { return this.before || '' }
  },
  watch: {
    // Always refetch stats when dataset changes via v-model (fallback in case @change fails)
    selectedDataset () {
      this.onDatasetChange()
    }
  },
  async mounted () {
    // load datasets
    try {
      const remoteDatasets = await this.$repositories.stats.datasets(this.projectId)
      // Always prepend the "all datasets" option
      this.datasetOptions = [{ text: 'Todos os Datasets', value: null }, ...remoteDatasets]
      // Keep previously selected value or default to "all"
      if (remoteDatasets.length && this.selectedDataset === null) {
        this.selectedDataset = null
      }
    } catch (e) {
      console.error('Erro ao carregar datasets', e)
      this.handleDbError(e, 'Erro ao carregar datasets.')
    }
    this.fetchStats()

    // Load perspective groups for filters
    try {
      const response = await this.$services.perspective.listPerspectiveGroups(this.projectId)
      this.perspectiveGroups = response.results || response.data?.results || []
    } catch (e) {
      console.error('Failed to load perspective groups', e)
      this.handleDbError(e, 'Erro ao carregar grupos de perspectiva.')
    }
  },
  methods: {
    handleDbError (err, fallbackMsg) {
      if (!err.response || (err.response.status && err.response.status >= 500)) {
        this.dbErrorMessage = 'Database unavailable at the moment, please try again later.'
      } else {
        this.dbErrorMessage = err.response?.data?.detail || fallbackMsg || 'Ocorreu um erro.'
      }
      this.dbErrorVisible = true
    },
    onDatasetChange () {
      // Reset selected version when dataset changes to avoid dangling version values
      this.selectedVersion = null
      this.applyFilters()
    },
    buildParams () {
      const params = {}
      // Apply dataset filter if selected
      if (this.selectedDataset) {
        params.dataset = this.selectedDataset
      }
      if (this.before) params.before = this.before
      if (this.progress !== null && this.progress !== 100) params.progress = this.progress

      // Perspective filters
      if (Object.keys(this.selectedPerspectiveAnswers).length > 0) {
        params.perspective_filters = JSON.stringify(this.selectedPerspectiveAnswers)
      }
      return params
    },
    async fetchStats () {
      try {
        const params = this.buildParams()
        const rawStats = await this.$repositories.stats.labelVotes(
          this.projectId,
          params
        )

        this.stats = rawStats.map(s => {
          const total = s.votes.reduce((acc, v) => acc + v, 0)
          const percentVotes = total === 0
            ? s.votes.map(() => 0)
            : s.votes.map(v => parseFloat(((v / total) * 100).toFixed(2)))
          return { ...s, votes: percentVotes }
        })

        this.versionOptions = this.stats.map(d => d.version).sort((a, b) => a - b)
      } catch (e) {
        console.error('Erro ao buscar estatísticas', e)
        this.handleDbError(e, 'Erro ao buscar estatísticas.')
      }
    },
    applyFilters () {
      this.fetchStats()
    },
    applyPerspectiveFilters () {
      this.perspectiveFilterDialog = false
      this.applyFilters()
    },
    clearPerspectiveFilters () {
      this.selectedPerspectiveAnswers = {}
      this.perspectiveFilterDialog = false
      this.applyFilters()
    },
    /* -------------------------    EXPORT  CSV / PDF   ------------------------- */
    exportCSV () {
      const delimiter = ';'
      const rows = [
        ['Versão', 'Rótulo', 'Percentagem']
      ]

      this.displayedStats.forEach(s => {
        s.labels.forEach((label, idx) => {
          rows.push([s.version, label, `${s.votes[idx]}%`])
        })
      })

      const csvContent = '\uFEFF' + // UTF-8 BOM for better compatibility (Excel)
        rows
          .map(r => r.map(item => {
            const field = String(item)
            const needsQuotes = field.includes(delimiter) || field.includes('"') || field.includes('\n')
            const escaped = field.replace(/"/g, '""')
            return needsQuotes ? `"${escaped}"` : escaped
          }).join(delimiter))
          .join('\r\n')

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `hist_stats_${new Date().toISOString()}.csv`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    },
    async loadJsPDF () {
      if (window.jspdf && window.jspdf.jsPDF) {
        // Ensure autoTable plugin is loaded as well
        if (!window.jspdf.jsPDF.API.autoTable) {
          await new Promise((resolve, reject) => {
            const script = document.createElement('script')
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.29/jspdf.plugin.autotable.min.js'
            script.onload = resolve
            script.onerror = reject
            document.body.appendChild(script)
          })
        }
        return window.jspdf.jsPDF
      }
      await new Promise((resolve, reject) => {
        const script = document.createElement('script')
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'
        script.onload = resolve
        script.onerror = reject
        document.body.appendChild(script)
      })
      // After core loaded, load autotable
      await new Promise((resolve, reject) => {
        const script = document.createElement('script')
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.29/jspdf.plugin.autotable.min.js'
        script.onload = resolve
        script.onerror = reject
        document.body.appendChild(script)
      })
      return window.jspdf.jsPDF
    },
    async exportPDF () {
      try {
        const jsPDF = await this.loadJsPDF()
        // eslint-disable-next-line new-cap
        const doc = new jsPDF({ orientation: 'p', unit: 'mm', format: 'a4' })

        let y = 10
        const pageWidth = doc.internal.pageSize.getWidth()
        const pageHeight = doc.internal.pageSize.getHeight()
        const margin = 18

        // Header bar
        doc.setFillColor(63, 81, 181) // Indigo
        doc.rect(0, 0, pageWidth, 20, 'F')
        doc.setFontSize(16)
        doc.setTextColor(255, 255, 255)
        doc.setFont(undefined, 'bold')
        doc.text('Estatísticas do Histórico de Anotações', pageWidth / 2, 13, { align: 'center' })

        // Reset default text color
        doc.setTextColor(0, 0, 0)

        y = 28
        const maxPageHeight = pageHeight - margin

        const addFooter = (pageNum, totalPages) => {
          doc.setFontSize(8)
          doc.setTextColor(150)
          doc.text(`Página ${pageNum} / ${totalPages}`, pageWidth / 2, pageHeight - 5, { align: 'center' })
          doc.setTextColor(0)
        }

        this.displayedStats.forEach(s => {
          // Section title
          doc.setFontSize(13)
          doc.setFont(undefined, 'bold')
          doc.text(`Versão ${s.version}`, margin, y)
          y += 6

          // Include table-like list under chart
          const chartCanvas = document.getElementById(`chart_${s.version}`)
          if (chartCanvas) {
            const imgData = chartCanvas.toDataURL('image/png', 1.0)
            // Calculate image dimensions (keep aspect ratio, fit width)
            const imgWidth = pageWidth - margin * 2
            const imgHeight = (chartCanvas.height / chartCanvas.width) * imgWidth

            if (y + imgHeight > maxPageHeight) {
              doc.addPage()
              y = margin
            }

            doc.addImage(imgData, 'PNG', margin, y, imgWidth, imgHeight)
            y += imgHeight + 4
          }

          // Labels table with autoTable
          const tableBody = s.labels.map((label, idx) => [label, `${s.votes[idx]}%`])
          doc.autoTable({
            head: [['Rótulo', 'Percentagem']],
            body: tableBody,
            startY: y,
            margin: { left: margin, right: margin },
            theme: 'grid',
            headStyles: { fillColor: [63, 81, 181], halign: 'center', valign: 'middle', textColor: 255 },
            bodyStyles: { halign: 'center' },
            styles: { fontSize: 9 },
            didDrawPage: (d) => {
              // Draw header bar on new pages generated by autoTable
              if (d.pageNumber > 1) {
                doc.setFillColor(63, 81, 181)
                doc.rect(0, 0, pageWidth, 20, 'F')
                doc.setFontSize(16)
                doc.setTextColor(255)
                doc.setFont(undefined, 'bold')
                doc.text('Estatísticas do Histórico de Anotações', pageWidth / 2, 13, { align: 'center' })
                doc.setTextColor(0)
              }
            }
          })

          y = doc.autoTable.previous.finalY + 8

          // Add footers with page numbers
          const totalPages = doc.getNumberOfPages()
          for (let i = 1; i <= totalPages; i++) {
            doc.setPage(i)
            addFooter(i, totalPages)
          }
        })

        doc.save(`hist_stats_${new Date().toISOString()}.pdf`)
      } catch (e) {
        console.error('Falha ao exportar PDF', e)
        this.$toast?.error?.('Não foi possível exportar o PDF')
      }
    }
  }
}
</script>

<style scoped>
</style> 