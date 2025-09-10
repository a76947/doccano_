<template>
  <div class="form-container">
    <v-card class="user-form">
      <v-card-title>
        <span class="text-h5">Create User</span>
        <v-spacer></v-spacer>
      </v-card-title>

      <!-- Error message as pop-up central superior -->
      <transition name="fade">
        <div v-if="errorMessage" class="error-message">
          <v-icon small class="mr-2" color="error">mdi-alert-circle</v-icon>
          {{ errorMessage }}
        </div>
      </transition>

      <!-- Success message with transition -->
      <transition name="fade">
        <div v-if="showSuccess" class="success-message">
          <v-icon small class="mr-2" color="success">mdi-check-circle</v-icon>
          User created successfully!
        </div>
      </transition>

      <v-card-text>
        <v-form v-model="valid">
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
            v-model="userData.first_name"
            label="First Name" 
            name="first_name"
            :prepend-icon="mdiAccount"
            dense
          />
          <v-text-field
            v-model="userData.last_name"
            label="Last Name"
            name="last_name" 
            :prepend-icon="mdiAccount"
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
import { mdiAccount, mdiLock, mdiEmail, mdiCheckCircle, mdiMapMarker, mdiAlertCircle } from '@mdi/js'
import { userNameRules, passwordRules } from '@/rules/index'
import { APIAuthRepository } from '@/repositories/auth/apiAuthRepository'

export default Vue.extend({
  layout: 'projects',

  data() {
    return {
      valid: false,
      showSuccess: false,
      errorMessage: '',
      userData: {
        username: '',
        first_name: '',
        last_name: '',
        email: '',
        password1: '',
        password2: '',
      },
      userNameRules,
      passwordRules,
      mdiAccount,
      mdiLock,
      mdiEmail,
      mdiCheckCircle,
      mdiMapMarker,
      mdiAlertCircle,
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
        this.errorMessage = '' // Clear any previous error message
        const apiAuthRepository = new APIAuthRepository()
        await apiAuthRepository.createUser(this.userData)
        
        this.showSuccess = true
      } catch (error) {
        console.error('Error creating user:', error.response ? error.response.data : error.message)
        this.errorMessage = 'Database unavailable at the moment, please try again later.'
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
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  background-color: #e6f4ea;
  color: #2e7d32;
  padding: 12px 24px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  font-weight: 500;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  pointer-events: none;
}

/* Fade para o snackbar */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-enter,
.fade-leave-to {
  opacity: 0;
}

.error-message {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  background-color: #fdecea;
  color: #b71c1c;
  padding: 12px 24px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  font-weight: 500;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  pointer-events: none;
}
</style>