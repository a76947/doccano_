<template>
  <v-card>
    <v-card-title class="d-flex justify-space-between align-center">
      <span class="text-h6">Perfis de Utilizador</span>
      <v-btn color="primary" dark @click="dialog = true">
        Criar Grupo
      </v-btn>
    </v-card-title>

    <v-dialog v-model="dialog" max-width="600px">
      <v-card>
        <v-card-title>
          <span class="text-h6">Novo Grupo</span>
        </v-card-title>
        <v-card-text>
          <v-text-field v-model="newGroup.name" label="Nome do Grupo" required />
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
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="dialog = false">Cancelar</v-btn>
          <v-btn color="primary" @click="createGroup">Criar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-list two-line>
      <v-list-item v-for="group in groups" :key="group.id" class="border-b">
        <v-list-item-content>
          <v-list-item-title>
            <span class="text-subtitle-2 text--secondary">ID: {{ group.id }}</span><br />
            {{ group.name }}
          </v-list-item-title>

          <v-list-item-subtitle>
            <v-chip-group column>
              <v-chip
                v-for="perm in group.permissions"
                :key="perm.id"
                class="ma-1 permission-chip"
                small
                outlined
              >
                <v-icon left>{{ getPermissionIcon(perm.codename) }}</v-icon>
                {{ perm.name }}
              </v-chip>
            </v-chip-group>
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </v-list>
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

export default Vue.extend({
  layout: 'projects',
  middleware: ['check-auth', 'auth'],

  data() {
    return {
      groups: [],
      isLoading: false,
      dialog: false,
      allPermissions: [] as Permission[],

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
    async createGroup() {
      try {
        const payload = {
          name: this.newGroup.name,
          permissions: this.newGroup.permissions.map(p => p.id)
        }
        await this.$axios.post('/v1/groups/create/', payload)
        this.dialog = false
        this.newGroup.name = ''
        this.newGroup.permissions = []
        this.$fetch()
      } catch (err) {
        console.error('Erro ao criar grupo:', err)
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
.permission-chip {
  border-color: #2196f3;
  color: #2196f3;
  transition: all 0.2s ease-in-out;
}

.permission-chip:hover {
  background-color: #2196f3 !important;
  color: white !important;
}
</style>
