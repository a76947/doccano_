<template>
  <div>
    <!-- Se não for o utilizador atual nem tiver projetos -->
    <base-card
      v-if="!containsCurrentUser && !hasProjects"
      :title="$t('UserOverview.overview.deleteUserTitle')"
      :agree-text="$t('generic.yes')"
      :cancel-text="$t('generic.cancel')"
      @agree="$emit('remove')"
      @cancel="$emit('cancel')"
    >
      <template #content>
        <div v-if="selected.length === 1">
          {{ $t('UserOverview.overview.deleteUserMessageSingle') }}
        </div>
        <div v-else>
          {{ $t('UserOverview.overview.deleteUserMessageMultiple') }}
        </div>

        <v-list dense>
          <v-list-item v-for="(item, i) in selected" :key="i">
            <v-list-item-content>
              <v-list-item-title>{{ item.username }}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </template>
    </base-card>

    <!-- Caso 1: Utilizador atual -->
    <base-card v-else-if="containsCurrentUser" :title="$t('UserOverview.overview.deleteUserTitle')">
      <template #content>
        <v-alert
          type="error"
          elevation="2"
          class="mb-4"
          style="font-weight: 500; background-color: #fdecea; color: #b71c1c;"
        >
          <v-icon left>mdi-close-circle</v-icon>
          {{ $t('UserOverview.overview.deleteCurrentUser') }}
        </v-alert>
      </template>
    </base-card>

    <!-- Caso 2: Utilizador com projetos -->
    <base-card v-else :title="$t('UserOverview.overview.deleteUserTitle')">
      <template #content>
        <v-alert
          type="error"
          elevation="2"
          class="mb-4"
          style="font-weight: 500; background-color: #fdecea; color: #b71c1c;"
        >
          <v-icon left>mdi-close-circle</v-icon>
          {{ $t('UserOverview.overview.deleteUserWithProjects') }}
        </v-alert>
      </template>
    </base-card>
  </div>
</template>

<script lang="ts">
import type { PropType } from 'vue'
import Vue from 'vue'
import BaseCard from '@/components/utils/BaseCard.vue'
import { UserItem } from '~/domain/models/user/user'

export default Vue.extend({
  components: { BaseCard },

  props: {
    selected: {
      type: Array as PropType<UserItem[]>,
      default: () => []
    },
    currentUser: {
      type: Object as PropType<UserItem>,
      required: true,
      default: () => ({ id: null })
    },
    hasProjects: {
      type: Boolean,
      default: false
    }
  },

  computed: {
    containsCurrentUser(): boolean {
      return this.selected.some(user => user.id === this.currentUser.id)
    }
  }
})
</script>
