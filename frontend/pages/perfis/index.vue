<template>
  <div>
    <v-card>
      <v-card-title v-if="isStaff">
        <v-btn
          class="text-capitalize"
          color="primary"
          @click.stop="dialog = true"
        >
          {{ $t('generic.create') }}
        </v-btn>
        <v-btn
          class="text-capitalize ms-2"
          color="primary"
          :disabled="!canEdit"
          @click.stop="edit"
        >
          Edit
        </v-btn>
        <v-btn
          class="text-capitalize ms-2"
          :disabled="!canDelete"
          outlined
          @click.stop="onDeleteClick"
        >
          {{ $t('generic.delete') }}
        </v-btn>
      </v-card-title>

      <v-card-text>
        <v-text-field
          v-model="search"
          :prepend-inner-icon="mdiMagnify"
          :label="$t('generic.search')"
          single-line
          hide-details
          filled
        />
      </v-card-text>

      <!-- ✅ Mensagem de erro com transição fade -->
      <v-snackbar
        v-model="showErrorSnackbar"
        color="error"
        timeout="3000"
        top
      >
        {{ errorMessage }}
        <template v-slot:action="{ attrs }">
          <v-btn
            text
            v-bind="attrs"
            @click="showErrorSnackbar = false"
          >
            Close
          </v-btn>
        </template>
      </v-snackbar>

      <!-- ✅ Mensagem de sucesso com transição fade -->
      <v-snackbar
        v-model="showSnackbar"
        color="success"
        timeout="3000"
        top
      >
        {{ successMessage }}
        <template v-slot:action="{ attrs }">
          <v-btn
            text
            v-bind="attrs"
            @click="showSnackbar = false"
          >
            Close
          </v-btn>
        </template>
      </v-snackbar>

      <!-- LISTA DE PERFIS -->
      <v-data-table
        v-model="selectedGroups"
        :headers="headers"
        :items="filteredGroups"
        item-key="id"
        show-select
        :footer-props="{
          showFirstLastPage: true,
          'items-per-page-options': [10, 50, 100],
          'items-per-page-text': $t('vuetify.itemsPerPageText'),
          'page-text': $t('dataset.pageText')
        }"
      >
        <template #[`item.name`]="{ item }">
          {{ item.name }}
        </template>

        <template #[`item.permissions`]="{ item }">
          <div class="d-flex flex-wrap gap-2">
            <v-chip
              v-for="perm in item.permissions"
              :key="perm.id"
              class="permission-chip"
              small
            >
              <v-icon
                v-if="getPermissionIcon(perm.codename)"
                left
                small
              >
                {{ getPermissionIcon(perm.codename) }}
              </v-icon>
              {{ perm.name }}
            </v-chip>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Diálogo de remoção -->
    <v-dialog v-model="dialogDelete" max-width="400px">
      <v-card>
        <v-card-title class="headline">Confirmar Exclusão</v-card-title>
        <v-card-text>
          Tem certeza que deseja excluir {{ selectedGroups.length }} perfil(is)?
          Esta ação não pode ser desfeita.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="dialogDelete = false">Cancelar</v-btn>
          <v-btn color="error" text @click="deleteGroups">Confirmar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Diálogo de criação -->
    <v-dialog v-model="dialog" max-width="600px">
      <v-card>
        <v-card-title>
          <span class="text-h6">New Profile</span>
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newGroup.name"
            label="Profile Name"
            required
            :error-messages="nameError"
            @input="nameError = ''"
          />
          <v-autocomplete
            v-model="newGroup.permissions"
            :items="allPermissions"
            item-text="name"
            item-value="id"
            label="Permissions"
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
          <v-btn text @click="closeDialog">Cancel</v-btn>
          <v-btn color="primary" @click="createGroup">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Diálogo de edição -->
    <v-dialog v-model="dialogEdit" max-width="600px">
      <v-card v-if="selectedGroupForEdit">
        <v-card-title>
          <span class="text-h6">Edit Profile</span>
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="selectedGroupForEdit.name"
            label="Profile Name"
            required
            :error-messages="nameError"
            @input="nameError = ''"
          />
          <v-autocomplete
            v-model="selectedGroupForEdit.permissions"
            :items="allPermissions"
            item-text="name"
            item-value="id"
            label="Permissions"
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
          <v-btn text @click="closeEditDialog">Cancel</v-btn>
          <v-btn color="primary" @click="saveEditedGroup">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { mapGetters } from 'vuex'
import { AxiosInstance } from 'axios'
import { mdiMagnify } from '@mdi/js'

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

interface VueWithAxios extends Vue {
  $axios: AxiosInstance
  $store: {
    getters: {
      'auth/getUserId': number
      'auth/getUsername': string
    }
  }
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
      dialogEdit: false,
      allPermissions: [] as Permission[],
      selectedGroups: [] as Group[],
      nameError: '',
      permissionsError: '',
      errorMessage: '',
      successMessage: '',
      showSnackbar: false,
      showErrorSnackbar: false,
      search: '',
      mdiMagnify,
      selectedGroupForEdit: null as Group | null,

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
        (this as unknown as VueWithAxios).$axios.get('/v1/groups/'),
        (this as unknown as VueWithAxios).$axios.get('/v1/permissions/')
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
    ...mapGetters('auth', ['isStaff']),
    canDelete() {
      return this.selectedGroups.length > 0
    },
    canEdit() {
      return this.selectedGroups.length === 1
    },
    filteredGroups(): Group[] {
      if (!this.search) return this.groups
      const searchLower = this.search.toLowerCase()
      return this.groups.filter(group =>
        group.name.toLowerCase().includes(searchLower)
      )
    },
    headers() {
      return [
        { text: 'Nome do perfil', value: 'name' },
        { text: 'Permissões', value: 'permissions', sortable: false }
      ]
    }
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

    onDeleteClick() {
      if (this.selectedGroups.length > 0) {
        this.dialogDelete = true
      }
    },

    async deleteGroups() {
      try {
        await Promise.all(
          this.selectedGroups.map(group =>
            (this as unknown as VueWithAxios).$axios.delete(`/v1/groups/${group.id}/`)
          )
        )
        this.dialogDelete = false
        this.selectedGroups = []
        this.successMessage = 'Perfis excluídos com sucesso!'
        this.showSnackbar = true
        setTimeout(() => (this.showSnackbar = false), 3000)
        this.$fetch()
      } catch (err) {
        console.error('Erro ao excluir perfis:', err)
        this.errorMessage = 'Erro ao excluir perfis'
        this.showErrorSnackbar = true
        setTimeout(() => (this.showErrorSnackbar = false), 3000)
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
        this.nameError = 'Profile name is required'
        isValid = false
      }

      if (this.newGroup.permissions.length === 0) {
        this.permissionsError = 'Select at least one permission'
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
        await (this as unknown as VueWithAxios).$axios.post('/v1/groups/create/', payload)
        this.closeDialog()
        this.successMessage = 'Profile created successfully!'
        this.showSnackbar = true
        setTimeout(() => (this.showSnackbar = false), 3000)
        this.$fetch()
      } catch (err: any) {
        console.error('Error creating profile:', err)
        if (err.response?.data?.name) {
          this.nameError = err.response.data.name[0]
          this.errorMessage = 'A profile with this name already exists'
          this.showErrorSnackbar = true
          setTimeout(() => (this.showErrorSnackbar = false), 3000)
        } else {
          this.errorMessage = 'Error creating profile'
          this.showErrorSnackbar = true
          setTimeout(() => (this.showErrorSnackbar = false), 3000)
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
    },

    edit() {
      if (this.selectedGroups.length === 1) {
        this.selectedGroupForEdit = { ...this.selectedGroups[0] }
        this.dialogEdit = true
      } else {
        console.warn('Please select exactly one group to edit.')
      }
    },

    closeEditDialog() {
      this.dialogEdit = false
      this.selectedGroupForEdit = null
      this.nameError = ''
      this.permissionsError = ''
    },

    async saveEditedGroup() {
      if (!this.selectedGroupForEdit) return

      // Basic validation for the edited group
      let isValid = true
      if (!this.selectedGroupForEdit.name.trim()) {
        this.nameError = 'Profile name is required'
        isValid = false
      }
      if (this.selectedGroupForEdit.permissions.length === 0) {
        this.permissionsError = 'Select at least one permission'
        isValid = false
      }
      if (!isValid) return

      try {
        const payload = {
          name: this.selectedGroupForEdit.name.trim(),
          permissions_ids: this.selectedGroupForEdit.permissions.map(p => p.id)
        }
        await (this as unknown as VueWithAxios).$axios.put(`/v1/groups/${this.selectedGroupForEdit.id}/`, payload)
        this.closeEditDialog()
        this.successMessage = 'Profile updated successfully!'
        this.showSnackbar = true
        setTimeout(() => (this.showSnackbar = false), 3000)
        this.$fetch()
      } catch (err: any) {
        console.error('Error updating profile:', err)
        if (err.response?.data?.name) {
          this.nameError = err.response.data.name[0]
          this.errorMessage = 'A profile with this name already exists'
          this.showErrorSnackbar = true
          setTimeout(() => (this.showErrorSnackbar = false), 3000)
        } else {
          this.errorMessage = 'Error updating profile'
          this.showErrorSnackbar = true
          setTimeout(() => (this.showErrorSnackbar = false), 3000)
        }
      }
    }
  }
})
</script>

<style scoped>
.gap-2 {
  gap: 0.25rem;
}

.selected-group {
  border: 2px solid var(--v-primary-base);
}

.permission-chip {
  background-color: #E3F2FD !important; /* blue lighten-5 */
  color: #0D47A1 !important; /* blue darken-4 */
  transition: background-color 0.2s ease-in-out;
  padding: 2px 6px; /* Reduced padding */
  font-size: 0.75rem; /* Smaller font size */
}

.permission-chip:hover {
  background-color: #BBDEFB !important; /* blue lighten-4, slightly darker */
  color: #0D47A1 !important; /* Keep original text color */
}

.success-message {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background-color: #4CAF50;
  color: white;
  padding: 12px 24px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  z-index: 1000;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>