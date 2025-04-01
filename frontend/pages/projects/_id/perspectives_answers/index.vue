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
            <v-text-field v-model="editedItem.name" label="Nome" required />
            <v-select
              v-model="editedItem.data_type"
              :items="['string', 'int', 'boolean']"
              label="Tipo de Dado"
              required
            />
            <v-combobox
              v-if="editedItem.data_type === 'string'"
              v-model="editedItem.options"
              label="Opções"
              multiple
              chips
              deletable-chips
              clearable
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

    <!-- Snackbars -->
    <v-snackbar v-model="snackbar" timeout="3000" top color="success">
      {{ snackbarMessage }}
      <template #action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbar = false">Fechar</v-btn>
      </template>
    </v-snackbar>

    <v-snackbar v-model="snackbarError" timeout="3000" top color="error">
      {{ snackbarErrorMessage }}
      <template #action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbarError = false">Fechar</v-btn>
      </template>
    </v-snackbar>

    <!-- Tabela com barra de pesquisa -->
    <v-data-table
      v-model="selected"
      :headers="headers"
      :items="perspectives"
      :search="search"
      show-select
      :items-per-page="5"
      class="elevation-1"
      @click:row="showDetails"
    >
      <!-- Aqui está a barra de pesquisa -->
      <template #top>
  <v-toolbar flat color="grey lighten-4">
    <v-text-field
      v-model="search"
      prepend-inner-icon="mdi-magnify"
      placeholder="Search"
      single-line
      hide-details
      class="mx-4"
      dense
      background-color="transparent"
    />
  </v-toolbar>
</template>

    </v-data-table>

    <!-- Details Dialog -->
    <v-dialog v-model="dialogDetails" max-width="500px">
      <v-card v-if="selectedPerspective">
        <v-card-title class="headline">Perspective Details</v-card-title>
        <v-card-text>
          <v-list-item>
            <v-list-item-content>
              <v-list-item-title>Name:</v-list-item-title>
              <v-list-item-subtitle>{{ selectedPerspective.name }}</v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
          
          <v-list-item>
            <v-list-item-content>
              <v-list-item-title>Data Type:</v-list-item-title>
              <v-list-item-subtitle>{{ selectedPerspective.data_type }}</v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
          
          <v-list-item v-if="selectedPerspective.data_type === 'string' 
          && selectedPerspective.options 
          && selectedPerspective.options.length">
            <v-list-item-content>
              <v-list-item-title>Options:</v-list-item-title>
              <v-chip-group column>
                <v-chip v-for="(option, i) in selectedPerspective.options" :key="i" small>
                  {{ option }}
                </v-chip>
              </v-chip-group>
            </v-list-item-content>
          </v-list-item>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="dialogDetails = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
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
      search: '',
      selected: [],
      dialogDetails: false,
      selectedPerspective: null,

      editedItem: {
      name: '',
      data_type: 'string',
      options: [] 
      },

      defaultItem: {
        name: '',
        data_type: 'string',
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
  if (
    !this.editedItem.name || 
    !this.editedItem.data_type || 
    (this.editedItem.data_type === 'string' && this.editedItem.options.length === 0)
  ){
    this.snackbarErrorMessage = 'Preenche todos os campos obrigatórios!'
    this.snackbarError = true
    return
  }

  const payload = { ...this.editedItem }

  if (payload.data_type !== 'string') {
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
      this.editedItem = Object.assign({}, this.defaultItem)
    },

    showDetails(item) {
      this.selectedPerspective = item;
      this.dialogDetails = true;
    }
  }
}
</script>

<style scoped>
::v-deep .v-dialog {
  width: 500px;
}
</style>

