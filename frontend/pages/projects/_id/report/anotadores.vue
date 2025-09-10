<template>
  <v-card>
    <v-card-text>
      <!-- Filtro de Anotadores -->
      <v-row>
        <v-col cols="12" md="6">
          <v-autocomplete
            v-model="selectedAnnotators"
            :items="annotatorsData"
            item-text="name"
            item-value="name"
            label="Anotadores"
            multiple
            chips
            :loading="loading"
            @change="filterAnnotators"
          ></v-autocomplete>
        </v-col>
        <v-col cols="12" md="6">
          <v-autocomplete
            v-model="selectedLabels"
            :items="availableLabels"
            label="Filtrar por Labels"
            multiple
            chips
            @change="filterAnnotators"
          ></v-autocomplete>
        </v-col>
      </v-row>

      <!-- Tabela de Anotadores -->
      <v-data-table
        :headers="headers"
        :items="filteredAnnotatorsData"
        :loading="loading"
        class="elevation-1"
      >
        <template #[`item.name`]="{ item }">
          <span>{{ item.name }}</span>
        </template>

        <template #[`item.labels`]="{ item }">
          <span>{{ (item.labels || []).join(', ') }}</span>
        </template>

        <template #[`item.annotations`]="{ item }">
          <span>{{ item.annotations.join(', ') }}</span>
        </template>
      </v-data-table>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'Anotadores',
  data() {
    return {
      loading: false,
      headers: [
        { text: 'Nome do Anotador', value: 'name', sortable: true },
        { text: 'Labels', value: 'labels', sortable: true },
        { text: 'Anotações', value: 'annotations', sortable: true }
      ],
      annotatorsData: [],
      filteredAnnotatorsData: [],
      selectedAnnotators: [],
      availableLabels: [], // Labels únicos disponíveis para filtro
      selectedLabels: [] // Labels selecionados para filtro
    };
  },
  methods: {
    filterAnnotators() {
      let data = this.annotatorsData;
      
      // Filtra por anotadores, se houver seleção
      if (this.selectedAnnotators.length > 0) {
        data = data.filter(annotator =>
          this.selectedAnnotators.includes(annotator.name)
        );
      }
      
      // Filtra por labels, se houver seleção
      if (this.selectedLabels.length > 0) {
        data = data.filter(annotator =>
          this.selectedLabels.some(label => (annotator.labels || []).includes(label))
        );
      }
      
      this.filteredAnnotatorsData = data;
      console.log("Anotadores filtrados:", this.filteredAnnotatorsData);
    },
    async fetchAnnotators() {
      this.loading = true;
      try {
        const projectId = this.$route.params.id;
        console.log("ID do projeto atual:", projectId);
        const response = await this.$services.project.getMembers(projectId);
        console.log("Membros recebidos:", response);
        this.annotatorsData = response.map(member => ({
          name: member.username,
          annotations: member.annotations || [],
          datasets: member.datasets || [],
          labels: [] // Inicialmente vazio
        }));
        this.filteredAnnotatorsData = this.annotatorsData;
      } catch (error) {
        console.error('Erro ao buscar membros do projeto:', error);
      } finally {
        this.loading = false;
      }
    },
    async fetchLabels() {
      try {
        const projectId = this.$route.params.id;
        const labelsResponse = await this.$services.label.list(projectId);
        console.log("Labels do projeto:", labelsResponse.categories);
        
        // Para cada anotador, associa os labels filtrados (por user)
        this.annotatorsData = this.annotatorsData.map(annotator => {
          const labelsByAnnotator = 
          labelsResponse.categories.filter(label => label.user === annotator.name);
          return {
            ...annotator,
            labels: labelsByAnnotator.map(label => label.label)
          };
        });
        console.log("Anotadores com labels:", this.annotatorsData);
        this.filteredAnnotatorsData = this.annotatorsData;
        
        // Define os labels únicos disponíveis para filtro
        this.availableLabels = [...new Set(labelsResponse.categories.map(label => label.label))];
        console.log("Available Labels:", this.availableLabels);
      } catch (error) {
        console.error("Erro ao buscar labels:", error);
      }
    }
  },
  mounted() {
    this.fetchAnnotators();
    this.fetchLabels();
  }
};
</script>