<template>
  <div>
    <v-card>
      <v-card-title v-if="isStaff">
        <v-btn
          class="text-capitalize"
          color="primary"
          @click.stop="$router.push('users/create')"
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

      <!-- ✅ Mensagem de erro com transição fade -->
      <transition name="fade">
        <v-alert
          v-if="errorMessage"
          type="error"
          class="ma-4"
          elevation="2"
          style="background-color: #fdecea; color: #b71c1c; border-left: 4px solid #b71c1c;"
          dense
        >
          <v-icon left color="error">mdi-alert-circle</v-icon>
          {{ errorMessage }}
        </v-alert>
      </transition>

      <!-- ✅ Mensagem de sucesso com transição fade -->
      <transition name="fade">
        <div v-if="showSnackbar" class="success-message">
          <v-icon small class="mr-2" color="success">mdi-check-circle</v-icon>
          {{ successMessage }}
        </div>
      </transition>

      <!-- LISTA DE USUÁRIOS -->
      <users-list
        v-if="!isLoading && users.items.length > 0"
        v-model="selected"
        :items="users.items"
        :is-loading="isLoading"
        :total="users.items.length"
        @update:query="updateQuery"
        @input="onSelectionChange"
      />
    </v-card>

    <!-- Diálogo de remoção -->
    <v-dialog v-model="dialogDelete" width="400">
      <form-delete
        :selected="selected"
        :current-user="currentUser"
        :has-projects="hasSelectedUserWithProjects"
        @cancel="dialogDelete = false"
        @remove="remove"
      />
    </v-dialog>

    <!-- DIÁLOGO DE EDIÇÃO -->
    <v-dialog v-model="dialogEdit" max-width="600px">
      <v-card v-if="selectedUser">
        <UserEditForm
          :key="selectedUser.id"
          :user="selectedUser"
          @saved="onUserSaved"
          @cancel="onEditCancel"
        />
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts">
import _ from 'lodash'
import { mapGetters } from 'vuex'
import Vue from 'vue'

import FormDelete from '~/components/users/FormDelete.vue'
import UsersList from '~/components/users/UsersList.vue'
import UserEditForm from '~/components/users/UserEditForm.vue'

import { UserItem } from '~/domain/models/user/user'
import { UserPage } from '~/domain/models/page'
import { SearchQueryData } from '~/services/application/user/userAplicationService'

export default Vue.extend({
  components: {
    FormDelete,
    UsersList,
    UserEditForm
  },
  layout: 'projects',
  middleware: ['check-auth', 'auth'],

  data() {
    return {
      // Dialogs
      dialogDelete: false,
      dialogEdit: false,

      // Lista de usuários e seleção
      users: {} as UserPage<UserItem>,
      selected: [] as UserItem[],
      isLoading: false,

      // Snackbar de sucesso
      successMessage: '',
      errorMessage: '',
      showSnackbar: false,
      usersWithProjects: [] as number[]
    }
  },

  async fetch() {
    this.isLoading = true
    try {
      this.users = await this.$services.user.list(
        this.$route.query as unknown as SearchQueryData
      )
      const ids = await this.$services.project.getUsersWithProjects()
      this.usersWithProjects = ids
    } catch (e) {
      console.error('Erro ao carregar usuários ou projetos:', e)
    } finally {
      this.isLoading = false
    }
  },

  computed: {
    ...mapGetters('auth', ['isStaff']),
    currentUser() {
      const id = this.$store.getters['auth/getUserId']
      const username = this.$store.getters['auth/getUsername']
      return { id, username }
    },
    canDelete() {
      return this.selected.length > 0
    },
    canEdit() {
      return this.selected.length === 1
    },
    hasSelectedUserWithProjects() {
      return this.selected.some(user => this.usersWithProjects.includes(user.id))
    }
  },

  watch: {
    '$route.query': _.debounce(function () {
      // @ts-ignore
      this.$fetch()
    }, 1000)
  },

  methods: {
    updateQuery(query: object) {
      this.$router.push(query)
    },

    onSelectionChange(selectedItems: UserItem[]) {
      this.selected = selectedItems
    },

    onDeleteClick() {
      const currentUserId = this.currentUser?.id

      const hasOwnUser = this.selected.some(user => user.id === currentUserId)
      const hasProjects = this.selected.some(user => this.usersWithProjects.includes(user.id))

      this.errorMessage = ''

      if (hasOwnUser) {
        this.errorMessage = this.$t('UserOverview.overview.deleteCurrentUser') as string
        setTimeout(() => (this.errorMessage = ''), 3000)
        return
      }

      if (hasProjects) {
        this.errorMessage = this.$t('UserOverview.overview.deleteUserWithProjects') as string
        setTimeout(() => (this.errorMessage = ''), 3000)
        return
      }

      this.dialogDelete = true
    },

    // Método de remoção real (do HEAD)
    async remove() {
      try {
        const currentUser = this.currentUser

        if (!currentUser) {
          console.error('🚨 currentUser ainda está undefined!')
          return
        }

        const usersToDelete = this.selected.filter(user => user.id !== currentUser.id)

        if (usersToDelete.length === 0) {
          console.warn('Tentativa de apagar o próprio utilizador foi evitada.')
          this.dialogDelete = false
          return
        }

        for (const user of usersToDelete) {
          try {
            await this.$services.user.delete(user.id)
          } catch (error) {
            if (error && typeof error === 'object' && 'response' in error) {
              this.errorMessage = (error as any).response.data?.detail || 'Erro ao eliminar utilizador.'
            } else {
              this.errorMessage = this.$t('UserOverview.overview.deleteUserError') as string
            }
            setTimeout(() => (this.errorMessage = ''), 3000)
            return
          }
        }

        // Exibe snackbar
        this.successMessage = this.$t(
          usersToDelete.length === 1
            ? 'UserOverview.overview.deleteUserSuccessSingle'
            : 'UserOverview.overview.deleteUserSuccessMultiple'
        ) as string

        this.showSnackbar = true
        setTimeout(() => (this.showSnackbar = false), 3000)

        // Recarrega
        await this.$fetch()
        this.selected = []
        this.dialogDelete = false
      } catch (e) {
        console.error('Erro ao remover utilizador', e)
      }
    },

    // Método que é chamado quando UserEditForm emite "saved"
    onUserSaved() {
      // Fecha modal
      this.dialogEdit = false
      // Recarrega a lista
      this.$fetch()

      // Se for o user logado que foi editado, forçamos logout (opcional)
      if (this.selectedUser && this.selectedUser.id === this.getUserId) {
        console.log('Editaste o teu próprio perfil -> logout automático...')
        this.$store.dispatch('auth/logout')
      }
    },

    onEditCancel() {
      this.dialogEdit = false
    }
  }
})
</script>

<style scoped>
.success-message {
  background-color: #e6f4ea;
  color: #2e7d32;
  padding: 12px 16px;
  border-radius: 6px;
  margin: 16px;
  display: flex;
  align-items: center;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

/* Fade para o snackbar */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-enter,
.fade-leave-to {
  opacity: 0;
}
</style>
