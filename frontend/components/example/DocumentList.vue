<template>
  <v-data-table
    :value="value"
    :headers="headers"
    :items="items"
    :options.sync="options"
    :server-items-length="total"
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
  >
    <template #top>
      <v-text-field
        v-model="search"
        :prepend-inner-icon="mdiMagnify"
        :label="$t('generic.search') + ' (e.g. label:positive)'"
        single-line
        hide-details
        filled
      />
    </template>
    <template #[`item.isConfirmed`]="{ item }">
      <v-chip :color="item.isConfirmed ? 'success' : 'warning'" text small>
        {{ item.isConfirmed ? 'Finished' : 'In progress' }}
      </v-chip>
    </template>
    <template #[`item.text`]="{ item }">
      <span class="d-flex d-sm-none">{{ item.text | truncate(50) }}</span>
      <span class="d-none d-sm-flex">{{ item.text | truncate(200) }}</span>
    </template>
    <template #[`item.meta`]="{ item }">
      {{ JSON.stringify(item.meta, null, 4) }}
    </template>
    <template #[`item.assignee`]="{ item }">
      <v-combobox
        :value="toSelected(item)"
        :items="members"
        item-text="username"
        no-data-text="No one"
        multiple
        chips
        dense
        flat
        hide-selected
        hide-details
        small-chips
        solo
        style="width: 200px"
        @change="onAssignOrUnassign(item, $event)"
      >
        <template #selection="{ attrs, item, parent, selected }">
          <v-chip v-bind="attrs" :input-value="selected" small class="mt-1 mb-1">
            <span class="pr-1">{{ item.username }}</span>
            <v-icon small @click="parent.selectItem(item)"> $delete </v-icon>
          </v-chip>
        </template>
      </v-combobox>
    </template>
    <template #[`item.action`]="{ item }">
      <v-btn class="me-1" small color="primary text-capitalize" @click="$emit('edit', item)">
        Edit
      </v-btn>
      <v-btn small color="primary text-capitalize" @click="toLabeling(item)">
        {{ $t('dataset.annotate') }}
      </v-btn>
      <v-btn small color="success text-capitalize" @click="$emit('vote', item)">
        Votações
      </v-btn>
    </template>
  </v-data-table>
</template>

<script lang="ts">
import { mdiMagnify } from '@mdi/js'
import type { PropType } from 'vue'
import Vue from 'vue'
import { DataOptions } from 'vuetify/types'
import { ExampleDTO } from '~/services/application/example/exampleData'
import { MemberItem } from '~/domain/models/member/member'

export default Vue.extend({
  props: {
    isLoading: {
      type: Boolean,
      default: false,
      required: true
    },
    items: {
      type: Array as PropType<ExampleDTO[]>,
      default: () => [],
      required: true
    },
    value: {
      type: Array as PropType<ExampleDTO[]>,
      default: () => [],
      required: true
    },
    total: {
      type: Number,
      default: 0,
      required: true
    },
    members: {
      type: Array as PropType<MemberItem[]>,
      default: () => [],
      required: true
    },
    isAdmin: {
      type: Boolean,
      default: false
    }
  },

  data(): any {
    return {
      search: '',
      options: {} as DataOptions,
      mdiMagnify
    }
  },

  computed: {
    headers(): any {
      const headers = [
        {
          text: 'Status',
          value: 'isConfirmed',
          sortable: false
        },
        {
          text: this.$t('dataset.text'),
          value: 'text',
          sortable: false
        },
        {
          text: this.$t('dataset.metadata'),
          value: 'meta',
          sortable: false
        },
        {
          text: this.$t('dataset.action'),
          value: 'action',
          sortable: false
        }
      ]
      if (this.isAdmin) {
        headers.splice(3, 0, {
          text: 'Assignee',
          value: 'assignee',
          sortable: false
        })
      }
      return headers
    }
  },

  watch: {
    options: {
      handler(): any {
        this.$emit('update:query', {
          query: {
            limit: this.options.itemsPerPage.toString(),
            offset: ((this.options.page - 1) * this.options.itemsPerPage).toString(),
            q: this.search
          }
        })
      },
      deep: true
    },
    search(): any {
      this.$emit('update:query', {
        query: {
          limit: this.options.itemsPerPage.toString(),
          offset: '0',
          q: this.search
        }
      })
      this.options.page = 1
    }
  },

  methods: {
    toLabeling(item: ExampleDTO): any {
      const index = this.items.indexOf(item)
      const offset = (this.options.page - 1) * this.options.itemsPerPage
      const page = (offset + index + 1).toString()
      this.$emit('click:labeling', { page, q: this.search })
    },

    toSelected(item: ExampleDTO): any {
      if (!item.assignments) {
        return [];
      }
      const assigneeIds = item.assignments.map((assignment) => assignment.assignee_id);
      const selectedMembers
       = this.members.filter((member: MemberItem) => assigneeIds.includes(member.user));
      return selectedMembers;
    },

    onAssignOrUnassign(item: ExampleDTO, newAssignees: MemberItem[]): any {
      const newAssigneeIds = newAssignees.map((assignee) => assignee.user);
      const oldAssigneeIds = item.assignments.map((assignment) => assignment.assignee_id);
      
      for (const assignment of item.assignments) {
        if (!newAssigneeIds.includes(assignment.assignee_id)) {
          this.$emit('unassign', assignment.id);
        }
      }
      
      for (const newAssigneeId of newAssigneeIds) {
        if (!oldAssigneeIds.includes(newAssigneeId)) {
          this.$emit('assign', item.id, newAssigneeId);
        }
      }
    }
  }
})
</script>
