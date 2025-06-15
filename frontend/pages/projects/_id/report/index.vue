<template>
  <layout-text>
    <template #header>
      <v-toolbar flat color="primary" dark>
        <v-btn text @click="activeTab = 'anotacoes'">Anotações</v-btn>
        <v-btn text @click="activeTab = 'anotadores'">Anotadores</v-btn>
      </v-toolbar>

      <v-card flat>
        <v-card-title class="d-flex align-center">
          <span v-if="activeTab === 'anotacoes'" class="text-h5">Relatório de Anotações</span>
          <span v-if="activeTab === 'anotadores'" class="text-h5">Relatório de Anotadores</span>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            :loading="loading"
            @click="generateReport"
          >
            Gerar Relatório
          </v-btn>
        </v-card-title>
      </v-card>
    </template>

    <template #content>
      <Anotacoes v-if="activeTab === 'anotacoes'" />
      <Anotadores v-if="activeTab === 'anotadores'"/>
    </template>
  </layout-text>
</template>

<script>
import Anotacoes from './anotacoes.vue';
import Anotadores from './anotadores.vue';
import LayoutText from '@/components/tasks/layout/LayoutText';

export default {
  name: 'ProjectReport',
  components: {
    LayoutText,
    Anotacoes,
    Anotadores
  },
  layout: 'project',

  data() {
    return {
      activeTab: 'anotacoes', // Define o conteúdo inicial
      loading: false // Estado para o botão "Gerar Relatório"
    };
  },
  methods: {
    generateReport() {
      this.loading = true;
      // Simulação de geração de relatório
      setTimeout(() => {
        this.loading = false;
        alert('Relatório gerado com sucesso!');
      }, 2000);
    }
  }
};
</script>

<style scoped>
.v-toolbar {
  margin-bottom: 16px;
}
</style>