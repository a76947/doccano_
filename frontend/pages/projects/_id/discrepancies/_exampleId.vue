<template>
  <v-card>
    <v-card-title>
      <v-btn icon @click="$router.back()">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <span class="ml-2 font-weight-medium">Discussão do Exemplo #{{ exampleId }}</span>
      <v-spacer />
    </v-card-title>
    <v-card-text>
      <div v-if="loading" class="text-center pa-10">
        <v-progress-circular indeterminate color="primary" />
      </div>

      <div v-else>
        <!-- Texto original -->
        <v-card outlined class="mb-6 pa-4">
          <h3 class="subtitle-1 mb-2">Texto Original</h3>
          <p style="white-space: pre-wrap">{{ example?.text }}</p>
        </v-card>

        <!-- Placeholder para futuro diff / comentários -->
        <v-alert type="info" outlined>
          Aqui podes implementar o componente completo de comparação e comentários.
        </v-alert>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
import ApiService from '@/services/api.service'

export default {
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],
  async asyncData({ params, error }) {
    const projectId = params.id
    const exampleId = params.exampleId
    try {
      const url = `/projects/${projectId}/examples/${exampleId}`
      const resp = await ApiService.get(url)
      return {
        projectId,
        exampleId,
        example: resp.data,
        loading: false
      }
    } catch (e) {
      error({ statusCode: 404, message: 'Exemplo não encontrado' })
    }
  }
}
</script>

<style scoped>
/*****  Podes colocar estilos adicionais aqui *****/
</style> 