<template>

  <v-card>
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

      <!-- Diálogo de remover (exemplo seu) -->
      <v-dialog v-model="dialogDelete">
        <form-delete
          :selected="selected"
          @cancel="dialogDelete = false"
          @remove="remove"
        />
      </v-dialog>
    </v-card-title>

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

    <!-- DIÁLOGO DE EDIÇÃO (controlado pelo pai) -->
    <v-dialog v-model="dialogEdit" max-width="600px">
      <v-card v-if="selectedUser">
        <UserEditForm
          :user="selectedUser"
          @saved="onUserSaved"
          @cancel="onEditCancel"
        />
      </v-card>
    </v-dialog>
  </v-card>

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
          @click.stop="dialogDelete = true"
        >
          {{ $t('generic.delete') }}
        </v-btn>
        <v-dialog v-model="dialogDelete" width="400">
          <form-delete :selected="selected" @cancel="dialogDelete = false" @remove="remove" />
        </v-dialog>
      </v-card-title>

      <!-- ✅ Mensagem de sucesso com transição fade -->
      <transition name="fade">
        <div v-if="showSnackbar" class="success-message">
          <v-icon small class="mr-2" color="success">mdi-check-circle</v-icon>
          {{ successMessage }}
        </div>
      </transition>

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

  layout: 'projects', // se for preciso

  layout: 'projects',


  middleware: ['check-auth', 'auth'],

  data() {
    return {
      dialogDelete: false,
      dialogEdit: false, // controla o modal de edição
      users: {} as UserPage<UserItem>,
      selected: [] as UserItem[],
      isLoading: false,
      successMessage: '',
      showSnackbar: false
    }
  },

  async fetch() {
    this.isLoading = true
    try {
      // Ajuste para chamar seu service de listagem
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
    ...mapGetters('auth', ['isStaff']),
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
      console.log('Usuários selecionados:', this.selected)
    },

    async remove() {
      console.log('Removendo:', this.selected)

      // TODO: Implementar a remoção
      this.dialogDelete = false
      this.selected = []
    },

    onUserSaved() {
      // Fechamos o diálogo e recarregamos a lista
      this.dialogEdit = false
      this.$fetch()
    },

    onEditCancel() {
      // Se o usuário clicou em Cancelar no formulário
      this.dialogEdit = false

      try {
        const isSingle = this.selected.length === 1

        for (const user of this.selected) {
          await this.$services.user.delete(user.id)
        }

        this.successMessage = this.$t(
          isSingle
            ? 'UserOverview.overview.deleteUserSuccessSingle'
            : 'UserOverview.overview.deleteUserSuccessMultiple'
        ) as string

        this.showSnackbar = true

        setTimeout(() => {
          this.showSnackbar = false
        }, 3000)

        await this.$fetch()
        this.selected = []
        this.dialogDelete = false
      } catch (e) {
        console.error('Erro ao remover utilizador', e)
      }
    },

    edit() {
      console.log('Editando:', this.selected)

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

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-enter,
.fade-leave-to {
  opacity: 0;
}
</style>
