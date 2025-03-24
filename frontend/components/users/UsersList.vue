<template>
  <div>
    <v-data-table
      :headers="headers"
      :items="sortedItems"
      :search="search"
      :loading="isLoading"
      :loading-text="$t('generic.loading')"
      :no-data-text="$t('vuetify.noDataAvailable')"
      :footer-props="{
        showFirstLastPage: true,
        'items-per-page-options': [10, 50, 100],
        'items-per-page-text': $t('vuetify.itemsPerPageText'),
        'page-text': $t('dataset.pageText')
      }"
      item-key="id"
      show-select
      @input="$emit('input', $event)"
      @update:options="updateOptions"
    >
      <template #top>
        <v-text-field
          v-model="search"
          :prepend-inner-icon="mdiMagnify"
          :label="$t('generic.search')"
          single-line
          hide-details
          filled
        />
      </template>

      <template #[`item.username`]="{ item }">
        <span>{{ item.username }}</span>
      </template>

      <template #[`item.email`]="{ item }">
        <span>{{ item.email }}</span>
      </template>

      <template #[`item.isSuperuser`]="{ item }">
        <span>{{ item.isSuperuser ? 'Yes' : 'No' }}</span>
      </template>

      <template #[`item.last_login`]="{ item }">
        <span>
          {{
            item.last_login
              ? dateFormat(dateParse(item.last_login, 'YYYY-MM-DDTHH:mm:ss'), 'YYYY/MM/DD HH:mm')
              : '-'
          }}
        </span>
      </template>

      <template #[`item.actions`]="{ item }">
        <v-btn icon small @click="openUserProfile(item)">
          <v-icon>{{ mdiEye }}</v-icon>
        </v-btn>
      </template>
    </v-data-table>

    <!-- Slideout de perfil -->
    <v-navigation-drawer
      v-model="profileDrawer"
      right
      fixed
      temporary
      width="300"
    >
      <v-list>
        <v-list-item>
          <v-list-item-content>
            <v-list-item-title class="headline">Perfil do Utilizador</v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <v-divider />

        <v-list-item>
          <v-list-item-content>
            👤 <strong>Username:</strong> {{ selectedProfile.username }}
          </v-list-item-content>
        </v-list-item>
        <v-list-item>
          <v-list-item-content>
            📧 <strong>Email:</strong> {{ selectedProfile.email }}
          </v-list-item-content>
        </v-list-item>
        <v-list-item>
          <v-list-item-content>
            ⭐ <strong>Superuser:</strong> {{ selectedProfile.isSuperuser ? 'Sim' : 'Não' }}
          </v-list-item-content>
        </v-list-item>
        <v-list-item>
          <v-list-item-content>
            🛠️ <strong>Staff:</strong> {{ selectedProfile.isStaff ? 'Sim' : 'Não' }}
          </v-list-item-content>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>
  </div>
</template>


<script lang="ts">
import { mdiMagnify, mdiEye } from '@mdi/js'
import { dateFormat } from '@vuejs-community/vue-filter-date-format'
import { dateParse } from '@vuejs-community/vue-filter-date-parse'
import type { PropType } from 'vue'
import Vue from 'vue'
import { UserItem } from '~/domain/models/user/user'

export default Vue.extend({
  props: {
    isLoading: {
      type: Boolean,
      default: false,
      required: true
    },
    items: {
      type: Array as PropType<UserItem[]>,
      default: () => [],
      required: true
    }
  },

  data() {
    return {
      search: this.$route.query.q || '',
      sortBy: 'username',
      sortDesc: false,
      mdiMagnify,
      mdiEye,
      dateFormat,
      dateParse,
      profileDrawer: false,
      selectedProfile: {}
    }
  },

  computed: {
    headers() {
      return [
        { text: this.$t('username'), value: 'username', sortable: true },
        { text: this.$t('email'), value: 'email', sortable: true },
        { text: this.$t('SuperUser'), value: 'isSuperuser', sortable: true },
        { text: this.$t('last login'), value: 'last_login', sortable: true },
        { text: 'Ações', value: 'actions', sortable: false }
      ]
    },
    filteredItems() {
      if (!this.search) return this.items
      const searchLower = this.search.toLowerCase()
      return this.items.filter(
        item =>
          item.username.toLowerCase().includes(searchLower) ||
          item.email.toLowerCase().includes(searchLower)
      )
    },
    sortedItems() {
      return [...this.filteredItems].sort((a, b) => {
        const modifier = this.sortDesc ? -1 : 1
        if (a[this.sortBy] < b[this.sortBy]) return -1 * modifier
        if (a[this.sortBy] > b[this.sortBy]) return 1 * modifier
        return 0
      })
    }
  },

  methods: {
    updateOptions(options) {
      this.sortBy = options.sortBy[0] || 'username'
      this.sortDesc = options.sortDesc[0] || false
    },
    openUserProfile(user) {
      this.selectedProfile = user
      this.profileDrawer = true
    }
  }
})
</script>

<style scoped>
::v-deep .v-data-table {
  width: 100%;
}
</style>
