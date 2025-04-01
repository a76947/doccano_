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

<script>
export default {
  data() {
    return {
      form: { 
        name: '', 
        data_type: 'string' 
      }
    }
  },
  
  computed: {
    projectId() {
      return this.$route.params.id
    }
  },
  
  methods: {
    async handleSubmit() {
      try {
        await this.$services.perspective.createPerspective(this.projectId, {
          ...this.form,
          project_id: this.projectId
        })
        
        this.$emit('created')
        this.form = { name: '', data_type: 'string' }
        alert('Perspetiva criada com sucesso!')
      } catch (error) {
        console.error('Error creating perspective:', error)
        alert('Erro ao criar a perspetiva')
      }
    }
  }
}
</script>

<style scoped>
form {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 400px;
  margin: 0 auto;
}

button {
  margin-top: 10px;
  padding: 8px;
}
</style>
