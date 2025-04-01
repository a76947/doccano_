<template>
  <v-card>
    <v-card-title>
      <v-btn class="text-capitalize" color="primary" @click.stop="dialogCreate = true">
        Create
      </v-btn>
      <v-btn class="text-capitalize ms-2" :disabled="true" outlined>
        Delete
      </v-btn>

      <!-- Modal de Criação -->
      <v-dialog v-model="dialogCreate" max-width="500px">
        <v-card>
          <v-card-title class="headline">Nova Perspetiva</v-card-title>
          <v-card-text>
            <v-text-field
              v-model="editedItem.name"
              label="Nome"
              :error="showErrors && !editedItem.name"
              :error-messages="showErrors && !editedItem.name ? ['* Campo obrigatório'] : []"
              required
            />
            <v-select
              v-model="editedItem.data_type"
              :items="['string', 'int', 'boolean', 'opções']"
              label="Tipo de Dado"
              :error="showErrors && !editedItem.data_type"
              :error-messages="showErrors && !editedItem.data_type ? ['* Campo obrigatório'] : []"
              required
            />

            <v-combobox
              v-if="editedItem.data_type === 'opções'"
              v-model="editedItem.options"
              label="Opções"
              multiple
              chips
              deletable-chips
              clearable
              :error="showErrors && editedItem.options.length === 0"
              :error-messages="showErrors && editedItem.options.length === 0 ? 
              ['* Campo obrigatório'] : []"
            />

            <v-alert v-if="errorMessage" type="error" dense>{{ errorMessage }}</v-alert>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn text @click="close">Cancelar</v-btn>
            <v-btn color="primary" text @click="save">Guardar</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-card-title>

    <!-- Snackbar de sucesso -->
    <v-snackbar v-model="snackbar" timeout="3000" top color="success">
      {{ snackbarMessage }}
      <template #action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbar = false">Fechar</v-btn>
      </template>
    </v-snackbar>

    <!-- Snackbar de erro -->
    <v-snackbar v-model="snackbarError" timeout="3000" top color="error">
      {{ snackbarErrorMessage }}
      <template #action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbarError = false">Fechar</v-btn>
      </template>
    </v-snackbar>

    <!-- Barra de pesquisa e tabela -->
    <v-data-table
      v-model="selected"
      :headers="headers"
      :items="perspectives"
      :search="search"
      show-select
      :items-per-page="5"
      class="elevation-1"
    >
      <template #top>
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          placeholder="Search "
          single-line
          hide-details
          filled
          class="pa-4"
        />
      </template>
    </v-data-table>
  </v-card>
</template>

<script>
import { usePerspectiveApplicationService } from '@/services/application/perspective/perspectiveApplicationService'

export default {
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject', 'isProjectAdmin'],

  validate({ params }) {
    return /^\d+$/.test(params.id)
  },

  data() {
    return {
      dialogCreate: false,
      snackbar: false,
      snackbarMessage: '',
      snackbarError: false,
      snackbarErrorMessage: '',
      errorMessage: '',
      showErrors: false,
      search: '',
      selected: [],

      editedItem: {
        name: '',
        data_type: 'opções',
        options: [] 
      },

      defaultItem: {
        name: '',
        data_type: 'opções',
        options: ''
      },
      perspectives: [],
      headers: [
        { text: 'Nome', value: 'name' },
        { text: 'Tipo de Dado', value: 'data_type' }
      ]
    }
  },

  computed: {
    projectId() {
      return this.$route.params.id
    }
  },

  mounted() {
    this.fetchPerspectives()
  },

  methods: {
    async fetchPerspectives() {
      try {
        const service = usePerspectiveApplicationService()
        const response = await service.listPerspective(this.projectId)
        this.perspectives = response.results
      } catch (err) {
        console.error('Erro ao buscar perspetivas', err)
      }
    },

    async save() {
      this.showErrors = true

      if (!this.editedItem.name || !this.editedItem.data_type) {
        return
      }

      if (
        this.editedItem.data_type === 'opções' &&
        (!this.editedItem.options || this.editedItem.options.length === 0)
      ) {
        return
      }

      const nomeExiste = this.perspectives.some(p => {
        const nomeAtual = p.name.trim().toLowerCase()
        const nomeNovo = this.editedItem.name.trim().toLowerCase()
        return nomeAtual === nomeNovo
      })

      if (nomeExiste) {
        this.snackbarErrorMessage = 'Já existe uma perspetiva com esse nome!'
        this.snackbarError = true
        return
      }

      const payload = { ...this.editedItem }

      if (payload.data_type === 'boolean') {
        payload.options = ['true', 'false']
      } else if (payload.data_type !== 'opções') {
        payload.options = []
      }

      try {
        const service = usePerspectiveApplicationService()
        await service.createPerspective(this.projectId, payload)
        this.snackbarMessage = 'Perspetiva criada com sucesso!'
        this.snackbar = true
        this.close()
        this.fetchPerspectives()
      } catch (e) {
        this.snackbarErrorMessage = e.response?.data?.detail || 'Erro ao criar perspetiva'
        this.snackbarError = true
      }
    },

    close() {
      this.dialogCreate = false
      this.errorMessage = ''
      this.showErrors = false
      this.editedItem = Object.assign({}, this.defaultItem)
    }
  }
}
</script>

<style scoped>
::v-deep .v-dialog {
  width: 500px;
}
</style>
