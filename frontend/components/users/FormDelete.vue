<template>
    <base-card
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
  </template>
  
    
    <script lang="ts">
    import type { PropType } from 'vue'
    import Vue from 'vue'
    import BaseCard from '@/components/utils/BaseCard.vue'
    import { UserItem } from '~/domain/models/user/user'
    
    export default Vue.extend({
      components: {
        BaseCard
      },
    
      props: {
        selected: {
          type: Array as PropType<UserItem[]>,
          default: () => []
        }
      }
    })
    </script>
    