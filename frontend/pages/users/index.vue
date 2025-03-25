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
import FormDelete from '~/components/project/FormDelete.vue'
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
  middleware: ['check-auth', 'auth'],

  data() {
    return {
      dialogDelete: false,
      dialogEdit: false, // controla o modal de edição
      users: {} as UserPage<UserItem>,
      selected: [] as UserItem[],
      isLoading: false
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

    remove() {
      console.log('Removendo:', this.selected)
      // TODO: Implementar a remoção
      this.dialogDelete = false
      this.selected = []
    },

    onUserSaved() {
  // Fecha o diálogo
  this.dialogEdit = false
  // Atualiza a lista de users
  this.$fetch()

  // *Se* o user que foi editado é exatamente o user logado,
  // então faz um refresh no "me"
  if (this.selectedUser && this.selectedUser.username === this.$store.state.auth.user?.username) {
    this.$store.dispatch('auth/fetchUserProfile')
  }
}
,

    onEditCancel() {
      // Se o usuário clicou em Cancelar no formulário
      this.dialogEdit = false
    }
  }
})
</script>

<style scoped>
::v-deep .v-dialog {
  width: 800px;
}
</style>
