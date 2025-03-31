<template>
    <form @submit.prevent="handleSubmit">
      <label>Nome da Perspetiva:</label>
      <input v-model="form.name" required />
  
      <label>Tipo de Dado:</label>
      <select v-model="form.data_type" required>
        <option value="int">Inteiro</option>
        <option value="string">Texto</option>
        <option value="boolean">Booleano</option>
      </select>
  
      <button type="submit">Criar</button>
    </form>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  import { useRoute } from 'vue-router'
  import { usePerspectiveApplicationService } from '@/services/application/perspective/perspectiveApplicationService'
  
  const route = useRoute()
  const projectId = route.params.id
  const form = ref({ name: '', data_type: 'string' })
  
  const perspectiveService = usePerspectiveApplicationService()
  
    const handleSubmit = async () => {
    await perspectiveService.createPerspective(projectId, {
    ...form.value,
    project_id: projectId
})
    alert('Perspetiva criada com sucesso!')
  }
  </script>
  