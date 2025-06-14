<template>
  <base-card
    :disabled="!valid"
    :title="$t('members.addMember')"
    :agree-text="$t('generic.save')"
    :cancel-text="$t('generic.cancel')"
    @agree="$emit('save')"
    @cancel="$emit('cancel')"
  >
    <template #content>
      <v-form v-model="valid">
        <v-autocomplete
          v-model="user"
          :items="users"
          :loading="isLoading"
          :search-input.sync="username"
          hide-no-data
          item-text="username"
          :label="$t('members.userSearchAPIs')"
          :placeholder="$t('members.userSearchPrompt')"
          :prepend-icon="mdiAccount"
          :rules="[rules.userRequired]"
          return-object
        />
        <v-select
          v-model="role"
          :items="roles"
          item-text="name"
          item-value="id"
          :label="$t('members.role')"
          :rules="[rules.roleRequired]"
          return-object
          :prepend-icon="mdiCreditCardOutline"
        >
          <template #item="props">
            {{ $translateRole(props.item.name, $t('members.roles')) }}
          </template>
          <template #selection="props">
            {{ $translateRole(props.item.name, $t('members.roles')) }}
          </template>
        </v-select>
        <v-alert v-show="errorMessage" prominent type="error">
          <v-row align="center">
            <v-col class="grow">
              {{ errorMessage }}
            </v-col>
          </v-row>
        </v-alert>
      </v-form>
    </template>
  </base-card>
</template>

<script lang="ts">
import { mdiAccount, mdiCreditCardOutline } from '@mdi/js'
import type { PropType } from 'vue'
import Vue from 'vue'
import BaseCard from '@/components/utils/BaseCard.vue'
import { MemberItem } from '~/domain/models/member/member'
import { RoleItem } from '~/domain/models/role/role'
import { UserItem } from '~/domain/models/user/user'

export default Vue.extend({
  components: {
    BaseCard
  },

  props: {
    value: {
      type: Object as PropType<MemberItem>,
      required: true
    },
    errorMessage: {
      type: String,
      default: ''
    }
  },

  data() {
    return {
      isLoading: false,
      valid: false,
      users: [] as UserItem[],
      roles: [] as RoleItem[],
      username: '',
      rules: {
        userRequired: (v: UserItem) => (!!v && !!v.username) || 'Required',
        roleRequired: (v: RoleItem) => (!!v && !!v.name) || 'Required'
      },
      mdiAccount,
      mdiCreditCardOutline
    }
  },

  async fetch() {
    try {
      this.isLoading = true
      const query = {
        limit: '100',
        offset: '0',
        q: this.username
      }
      const response = await this.$repositories.user.list(query)
      this.users = response.items || []
    } catch (error) {
      console.error('Error fetching users:', error)
    } finally {
      this.isLoading = false
    }
  },

  computed: {
    user: {
      get(): UserItem {
        return {
          id: this.value.user,
          username: this.value.username,
          isStaff: false,
          isSuperuser: false
        }
      },
      set(val: UserItem) {
        if (!val) return
        this.$emit('input', {
          ...this.value,
          user: val.id,
          username: val.username
        })
      }
    },
    role: {
      get(): RoleItem {
        return {
          id: this.value.role,
          name: this.value.rolename
        }
      },
      set(val: RoleItem) {
        if (!val) return
        this.$emit('input', {
          ...this.value,
          role: val.id,
          rolename: val.name
        })
      }
    }
  },

  watch: {
    username() {
      if (this.isLoading) return
      this.$fetch()
    }
  },

  async created() {
    try {
      this.roles = await this.$repositories.role.list()
    } catch (error) {
      console.error('Error fetching roles:', error)
    }
  }
})
</script>
