<template>
  <v-card>
    <v-card-title class="d-flex justify-space-between align-center">
      <span class="text-h6">Perfis de Utilizador</span>
      <div>
        <v-btn
          class="text-capitalize ms-2"
          :disabled="!selectedGroups.length"
          color="error"
          @click="confirmDelete"
        >
          Apagar ({{ selectedGroups.length }})
        </v-btn>
        <v-btn color="primary" dark @click="dialog = true">
          Criar Grupo
        </v-btn>
      </div>
    </v-card-title>

    <v-dialog v-model="dialogDelete" max-width="400px">
      <v-card>
        <v-card-title class="headline">Confirmar Exclusão</v-card-title>
        <v-card-text>
          Tem certeza que deseja excluir {{ selectedGroups.length }} grupo(s)?
          Esta ação não pode ser desfeita.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="dialogDelete = false">Cancelar</v-btn>
          <v-btn color="error" text @click="deleteGroups">Confirmar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialog" max-width="600px">
      <v-card>
        <v-card-title>
          <span class="text-h6">Novo Grupo</span>
        </v-card-title>
        <v-card-text>
          <v-text-field 
            v-model="newGroup.name" 
            label="Nome do Grupo" 
            required 
            :error-messages="nameError"
            @input="nameError = ''"
          />
          <v-autocomplete
            v-model="newGroup.permissions"
            :items="allPermissions"
            item-text="name"
            item-value="id"
            label="Permissões"
            multiple
            chips
            deletable-chips
            return-object
            :error-messages="permissionsError"
            @change="permissionsError = ''"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="closeDialog">Cancelar</v-btn>
          <v-btn color="primary" @click="createGroup">Criar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <div class="pa-4">
      <v-card 
        v-for="group in groups" 
        :key="group.id" 
        class="mb-4 elevation-2"
        :class="{ 'selected-group': selectedGroups.some(g => g.id === group.id) }"
        @click="toggleGroupSelection(group)"
      >
        <v-card-title class="d-flex align-center justify-space-between">
          <v-checkbox
            :input-value="selectedGroups.some(g => g.id === group.id)"
            @click.stop
            @change="toggleGroupSelection(group)"
            hide-details
            class="mr-2"
          ></v-checkbox>
          <span class="text-subtitle-1 text--secondary">ID: {{ group.id }}</span>
        </v-card-title>
        <v-card-subtitle class="pt-0">
          <span class="text-h6">{{ group.name }}</span>
        </v-card-subtitle>

        <v-card-text>
          <div class="d-flex flex-wrap gap-2">
            <v-chip
              v-for="perm in group.permissions"
              :key="perm.id"
              class="permission-chip"
              small
            >
              <v-icon left small v-if="getPermissionIcon(perm.codename)">
                {{ getPermissionIcon(perm.codename) }}</v-icon>
              {{ perm.name }}
            </v-chip>
          </div>
        </v-card-text>
      </v-card>
    </div>
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapGetters } from 'vuex'

type Permission = {
  id: number
  name: string
  codename: string
  content_type: string
}

type Group = {
  id: number
  name: string
  permissions: Permission[]
}

export default Vue.extend({
  layout: 'projects',
  middleware: ['check-auth', 'auth'],

  data() {
    return {
      groups: [] as Group[],
      isLoading: false,
      dialog: false,
      dialogDelete: false,
      allPermissions: [] as Permission[],
      selectedGroups: [] as Group[],
      nameError: '',
      permissionsError: '',

      newGroup: {
        name: '',
        permissions: [] as Permission[]
      }
    }
  },

  async fetch() {
    this.isLoading = true
    try {
      const [groupRes, permRes] = await Promise.all([
        this.$axios.get('/v1/groups/'),
        this.$axios.get('/v1/permissions/')
      ])
      this.groups = groupRes.data
      this.allPermissions = permRes.data
    } catch (err) {
      console.error('Erro ao buscar grupos ou permissões:', err)
    } finally {
      this.isLoading = false
    }
  },

  computed: {
    ...mapGetters('auth', ['isStaff'])
  },

  methods: {
    toggleGroupSelection(group: Group) {
      const index = this.selectedGroups.findIndex(g => g.id === group.id)
      if (index === -1) {
        this.selectedGroups.push(group)
      } else {
        this.selectedGroups.splice(index, 1)
      }
    },

    confirmDelete() {
      if (this.selectedGroups.length > 0) {
        this.dialogDelete = true
      }
    },

    async deleteGroups() {
      try {
        await Promise.all(
          this.selectedGroups.map(group => 
            this.$axios.delete(`/v1/groups/${group.id}/delete/`)
          )
        )
        this.dialogDelete = false
        this.selectedGroups = []
        this.$fetch()
      } catch (err) {
        console.error('Erro ao excluir grupos:', err)
      }
    },

    closeDialog() {
      this.dialog = false
      this.newGroup.name = ''
      this.newGroup.permissions = []
      this.nameError = ''
      this.permissionsError = ''
    },

    validateGroup() {
      let isValid = true
      
      if (!this.newGroup.name.trim()) {
        this.nameError = 'O nome do grupo é obrigatório'
        isValid = false
      }

      if (this.newGroup.permissions.length === 0) {
        this.permissionsError = 'Selecione pelo menos uma permissão'
        isValid = false
      }

      return isValid
    },

    async createGroup() {
      if (!this.validateGroup()) {
        return
      }

      try {
        const payload = {
          name: this.newGroup.name.trim(),
          permissions: this.newGroup.permissions.map(p => p.id)
        }
        await this.$axios.post('/v1/groups/create/', payload)
        this.closeDialog()
        this.$fetch()
      } catch (err: any) {
        console.error('Erro ao criar grupo:', err)
        if (err.response?.data?.name) {
          this.nameError = err.response.data.name[0]
        }
      }
    },
    getPermissionIcon(codename: string) {
      const icons: { [key: string]: string } = {
        'add_user': 'mdi-account-plus',
        'change_user': 'mdi-account-edit',
        'delete_user': 'mdi-account-remove',
        'view_user': 'mdi-account-eye'
      }
      return icons[codename] || 'mdi-account'
    }
  }
})
</script>

<style scoped>
.gap-2 {
  gap: 0.5rem;
}

.selected-group {
  border: 2px solid var(--v-primary-base);
}

.permission-chip {
  background-color: #E3F2FD !important; /* blue lighten-5 */
  color: #0D47A1 !important; /* blue darken-4 */
  transition: background-color 0.2s ease-in-out;
}

.permission-chip:hover {
  background-color: #BBDEFB !important; /* blue lighten-4, slightly darker */
  color: #0D47A1 !important; /* Keep original text color */
}
</style>
