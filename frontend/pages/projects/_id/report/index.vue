<template>
  <v-card>
    <v-card-title class="d-flex align-center justify-space-between">
      <span class="text-h6">Annotations Report</span>
      <v-btn color="primary" @click="exportCSV">Exportar CSV</v-btn>
    </v-card-title>

    <v-card-text>
      <v-row>
        <v-col cols="3">
          <v-select
            v-model="selectedUser"
            :items="users"
            label="Utilizador"
            item-text="username"
            item-value="id"
            dense outlined
          />
        </v-col>
        <v-col cols="3">
          <v-select
            v-model="selectedLabel"
            :items="labels"
            label="Label"
            dense outlined
          />
        </v-col>
        <v-col cols="3">
          <v-text-field
            v-model="textSearch"
            label="Pesquisar texto"
            dense outlined
          />
        </v-col>
        <v-col cols="3">
          <v-menu
            v-model="menu"
            :close-on-content-click="false"
            transition="scale-transition"
            offset-y
            min-width="auto"
          >
            <template v-slot:activator="{ on, attrs }">
              <v-text-field
                v-model="startDate"
                label="Data (de)"
                readonly
                v-bind="attrs"
                v-on="on"
                dense outlined
              />
            </template>
            <v-date-picker v-model="startDate" no-title scrollable />
          </v-menu>
        </v-col>
      </v-row>

      <v-data-table
        :headers="headers"
        :items="reportData"
        class="elevation-1 mt-4"
      >
        <template v-slot:no-data>
          Nenhum dado encontrado.
        </template>
      </v-data-table>
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { getAnnotationReport } from '@/repositories/report/apiReportRepository'

export default Vue.extend({
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  data() {
    return {
      selectedUser: null,
      selectedLabel: null,
      textSearch: '',
      startDate: '',
      users: [],
      labels: [],
      menu: false,
      reportData: [],
      headers: [
        { text: 'Texto', value: 'text' },
        { text: 'Label', value: 'label' },
        { text: 'Utilizador', value: 'user' },
        { text: 'Data', value: 'updated_at' },
      ],
    }
  },

  computed: {
    projectId(): number {
      return parseInt(this.$route.params.id)
    },
  },

  watch: {
    selectedUser: 'fetchData',
    selectedLabel: 'fetchData',
    textSearch: 'fetchData',
    startDate: 'fetchData',
  },

  mounted() {
    this.fetchFilters()
    this.fetchData()
  },

  methods: {
    async fetchFilters() {
      const [usersRes, labelsRes] = await Promise.all([
        this.$axios.get(`/v1/projects/${this.projectId}/members/`),
        this.$axios.get(`/v1/projects/${this.projectId}/labels/`),
      ])
      this.users = usersRes.data
      this.labels = labelsRes.data.map((l: any) => l.text || l)
    },

    async fetchData() {
      const filters = {
        user: this.selectedUser,
        label: this.selectedLabel,
        text: this.textSearch,
        start: this.startDate,
      }
      const data = await getAnnotationReport(this.projectId, filters)
      this.reportData = data.map((item: any) => ({
        text: item.text || '',
        label: item.label || '',
        user: item.user || '',
        updated_at: item.updated_at || '',
      }))
    },

    exportCSV() {
      const csv = [
        ['Texto', 'Label', 'Utilizador', 'Data'],
        ...this.reportData.map((r: any) => [r.text, r.label, r.user, r.updated_at])
      ].map(row => row.join(',')).join('\n')

      const blob = new Blob([csv], { type: 'text/csv' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = 'relatorio.csv'
      link.click()
    }
  }
})
</script>

<style scoped>
.v-card-title {
  padding-bottom: 0;
}
.v-data-table {
  margin-top: 16px;
}
</style>

