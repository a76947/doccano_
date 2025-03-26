<template>
  <!-- Um único root element -->
  <v-card>
    <!-- Título e botões se for staff -->
    <v-card-title v-if="isStaff">
      <v-btn
        class="text-capitalize"
        color="primary"
        @click.stop="$router.push('/users/create')"
      >
        {{ $t('generic.create') }}
      </v-btn>

      <v-btn
        class="text-capitalize ms-2"
        color="primary"
        :disabled="!canEdit"
        @click.stop="dialogEdit = true"
      >
        Edit
      </v-btn>

      <v-btn
        class="text-capitalize ms-2"
        :disabled="!canDelete"
        outlined
        @click.stop="dialogDelete = true"
      >
        {{ $t('generic.delete') }}
      </v-btn>

      <!-- Diálogo de remoção -->
      <v-dialog v-model="dialogDelete" width="400">
        <form-delete
          :selected="selected"
          @cancel="dialogDelete = false"
          @remove="remove"
        />
      </v-dialog>
    </v-card-title>

    <!-- Mensagem de sucesso (snackbar) com transição fade -->
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
  </v-card>
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
      showSnackbar: false
    }
  },

  async fetch() {
    this.isLoading = true
    try {
      this.users = await this.$services.user.list(
        this.$route.query as unknown as SearchQueryData
      )
    } catch (e) {
      console.error('Erro ao carregar usuários:', e)
    } finally {
      this.isLoading = false
    }
  },

  computed: {
    ...mapGetters({
      isStaff: 'auth/isStaff',
      getUserId: 'auth/getUserId'
    }),

    canDelete(): boolean {
      return this.selected.length > 0
    },
    canEdit(): boolean {
      return this.selected.length === 1
    },
    selectedUser(): UserItem | null {
      return this.selected.length === 1 ? this.selected[0] : null
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

    // Método de remoção real (do HEAD)
    async remove() {
      console.log('Removendo:', this.selected)
      try {
        const isSingle = this.selected.length === 1

        // Deleta cada user selecionado
        for (const user of this.selected) {
          await this.$services.user.delete(user.id)
        }

        // Exibe snackbar
        this.successMessage = this.$t(
          isSingle
            ? 'UserOverview.overview.deleteUserSuccessSingle'
            : 'UserOverview.overview.deleteUserSuccessMultiple'
        ) as string

        this.showSnackbar = true
        setTimeout(() => {
          this.showSnackbar = false
        }, 3000)

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
