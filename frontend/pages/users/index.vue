<template>
  <v-card>
    <v-card-title v-if="isStaff">
      <v-btn class="text-capitalize" color="primary" @click.stop="$router.push('/users/create')">
        {{ $t('generic.create') }}
      </v-btn>
      <v-btn class="text-capitalize ms-2" color="primary" :disabled="!canEdit" @click.stop="edit">
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
      <v-dialog v-model="dialogDelete">
        <form-delete :selected="selected" @cancel="dialogDelete = false" @remove="remove" />
      </v-dialog>
    </v-card-title>

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
</template>

<script lang="ts">
import _ from 'lodash'
import { mapGetters } from 'vuex'
import Vue from 'vue'
import FormDelete from '~/components/project/FormDelete.vue'
import UsersList from '~/components/users/UsersList.vue'
import { UserItem } from '~/domain/models/user/user'
import { UserPage } from '~/domain/models/page'
import { SearchQueryData } from '~/services/application/user/userAplicationService'

export default Vue.extend({
  components: {
    FormDelete,
    UsersList
  },
  layout: 'projects', // verificar se temos algum erro por usar este layout

  middleware: ['check-auth', 'auth'],

  data() {
    return {
      dialogDelete: false,
      users: {} as UserPage<UserItem>,
      selected: [] as UserItem[],
      isLoading: false
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
    ...mapGetters('auth', ['isStaff']),
    canDelete(): boolean {
      return this.selected.length > 0
    },
    canEdit(): boolean {
      return this.selected.length === 1
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

    edit() {
      console.log('Editando:', this.selected)
      // TODO: Implementar a edição
    }
  }
})
</script>

<style scoped>
::v-deep .v-dialog {
  width: 800px;
}
</style>