<template>
  <v-card>
    <v-card-title>
      <span class="text-h5">Editar Usuário</span>
    </v-card-title>

    <v-card-text>
      <v-form ref="form" v-if="user">
        <v-text-field
          v-model="formData.username"
          label="Username"
          required
        />
        <v-text-field
          v-model="formData.email"
          label="Email"
          type="email"
          required
        />
        <v-text-field
          v-model="formData.password"
          label="Nova Senha"
          type="password"
        />
      </v-form>
    </v-card-text>

    <v-card-actions>
      <v-btn color="primary" text @click="onCancel">Cancelar</v-btn>
      <v-btn color="primary" @click="onSave">Salvar</v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import userService from '~/services/userService'

export default {
  name: 'UserEditForm',
  props: {
    user: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      formData: {
        id: null,
        username: '',
        email: '',
        password: ''
      }
    }
  },
  watch: {
  'user.id': {
    immediate: true,
    handler(newId) {
      // Se "selectedUser" mudar de ID, atualiza formData
      this.formData.id = newId
      this.formData.username = this.user.username
      this.formData.email = this.user.email
      this.formData.password = ''
    }
  }
}
,
  methods: {
    onCancel() {
      this.$emit('cancel')
    },
    async onSave() {
      try {
        console.log('Atualizando utilizador ID:', this.formData.id)

        await userService.updateUser(this.formData.id, {
          username: this.formData.username,
          email: this.formData.email,
          password: this.formData.password
        })

        // Limpar o campo da senha
        this.formData.password = ''

        // Emite para o pai que salvou
        this.$emit('saved')
      } catch (error) {
        console.error('Erro ao atualizar usuário:', error)
        // Aqui podes exibir um snackbar ou alerta
      }
    }
  }
}
</script>
