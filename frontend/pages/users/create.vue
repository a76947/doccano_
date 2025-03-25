<template>
  <div class="form-container">
    <v-card class="user-form">
      <v-card-title>
        <span class="text-h5">Create User</span>
        <v-spacer></v-spacer>
      </v-card-title>

      <!-- Success message with transition -->
      <transition name="fade">
        <div v-if="showSuccess" class="success-message">
          <v-icon small class="mr-2" color="success">mdi-check-circle</v-icon>
          User created successfully!
        </div>
      </transition>

      <v-card-text>
        <v-form v-model="valid">
          <v-alert v-show="showError" v-model="showError" type="error" dismissible>
            {{ errorMessage }}
          </v-alert>
          <v-text-field
            v-model="userData.username"
            :rules="userNameRules('Username is required')"
            label="Username"
            name="username"
            :prepend-icon="mdiAccount"
            type="text"
            autofocus
            dense
          />
          <v-text-field
            v-model="userData.email"
            :rules="emailRules"
            label="Email"
            name="email"
            :prepend-icon="mdiEmail"
            type="email"
            dense
          />
          <v-text-field
            v-model="userData.password1"
            :rules="passwordRules('Password is required')"
            label="Password"
            name="password1"
            :prepend-icon="mdiLock"
            type="password"
            dense
          />
          <v-text-field
            v-model="userData.password2"
            :rules="[...passwordRules('Confirm password is required'), passwordMatchRule]"
            label="Confirm Password"
            name="password2"
            :prepend-icon="mdiLock"
            type="password"
            dense
          />
          <v-text-field
            v-model="userData.location"
            label="Location"
            name="location"
            :prepend-icon="mdiMapMarker"
            dense
          />
        </v-form>
        <v-text-field
            v-model="userData.phoneNumber"
            label="PhoneNumber"
            name="PhoneNumber"
            :prepend-icon="mdiPhone"
            dense
          />
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          class="text-capitalize mr-3"
          outlined
          color="error"
          @click= "goBack"
        >
          {{ $t('generic.cancel') || 'Cancel' }}
        </v-btn>
        <v-btn
          :disabled="!valid"
          color="primary"
          class="text-capitalize"
          @click="createUser"
        >
          {{ $t('generic.create') || 'Create User' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { mdiAccount, mdiLock, mdiEmail, mdiCheckCircle, mdiMapMarker, mdiPhone } from '@mdi/js'
import { userNameRules, passwordRules } from '@/rules/index'
import { APIAuthRepository } from '@/repositories/auth/apiAuthRepository'

export default Vue.extend({
  layout: 'projects',

  data() {
    return {
      valid: false,
      showError: false,
      showSuccess: false,
      errorMessage: '',
      userData: {
        username: '',
        email: '',
        password1: '',
        password2: '',
        location: '',
        phoneNumber: '',
      },
      userNameRules,
      passwordRules,
      mdiAccount,
      mdiLock,
      mdiEmail,
      mdiCheckCircle,
      mdiMapMarker,
      mdiPhone,
      emailRules: [
        (v: string) => !!v || 'Email is required',
        (v: string) => /.+@.+\..+/.test(v) || 'Email must be valid'
      ]
    }
  },

  computed: {
    passwordMatchRule() {
      return () => 
        this.userData.password1 === this.userData.password2 || 
        'Passwords must match'
    }
  },

  methods: {
    async createUser() {
      if (!this.valid) return

      try {
        this.showError = false
        const apiAuthRepository = new APIAuthRepository()
        await apiAuthRepository.createUser(this.userData)
        
        this.showSuccess = true
      } catch (error) {
        console.error('Error creating user:', error.response ? error.response.data : error.message)
        
        this.showError = true
        if (error.response && error.response.data) {
          if (error.response.data.non_field_errors) {
            this.errorMessage = error.response.data.non_field_errors.join(', ')
          } else if (typeof error.response.data === 'object') {
            this.errorMessage = Object.entries(error.response.data)
              .map(([field, errors]) => {
                const errorValue = Array.isArray(errors) ? errors.join(', ') : errors
                return `${field}: ${errorValue}`
              })
              .join('; ')
          } else {
            this.errorMessage = 'Failed to create user'
          }
        } else {
          this.errorMessage = error.message || 'Failed to create user'
        }
      }
    },
    goBack() {
      this.$router.push('/users')
    }
  }
})
</script>

<style scoped>
.form-container {
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
  padding: 16px;
}

.user-form {
  max-width: 1500px;
  width: 100%;
  margin-left: 0;
}

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