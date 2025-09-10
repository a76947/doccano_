<template>
  <v-card>
    <v-card-title>
      {{ $t('Compare Annotations') || 'Compare Annotations' }}
    </v-card-title>
    <v-card-text>
      <v-container>
        <v-row>
          <v-col cols="12">
            <v-select
              v-model="selectedDocument"
              :items="documents"
              item-text="text"
              item-value="id"
              :label="$t('Select Document') || 'Select Document'"
              required
            ></v-select>
          </v-col>
          <v-col cols="12">
            <v-select
              v-model="user1"
              :items="projectUsers"
              item-text="username"
              item-value="id"
              :label="$t('First User') || 'First User'"
              required
            ></v-select>
          </v-col>
          <v-col cols="12">
            <v-select
              v-model="user2"
              :items="projectUsers"
              item-text="username"
              item-value="id"
              :label="$t('Second User') || 'Second User'"
              required
            ></v-select>
          </v-col>
        </v-row>
      </v-container>
    </v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn text @click="$emit('cancel')">{{ $t('Cancel') || 'Cancel' }}</v-btn>
      <v-btn
        color="primary"
        text
        @click="compare"
        :disabled="!isValid"
      >
        {{ $t('Compare') || 'Compare' }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  props: {
    projectId: {
      type: [Number, String],
      required: true
    },
    documents: {
      type: Array,
      default: () => []
    },
    projectUsers: {
      type: Array,
      default: () => []
    }
  },

  data() {
    return {
      selectedDocument: null,
      user1: null,
      user2: null,
      isChecking: false
    }
  },

  computed: {
    isValid() {
      return this.selectedDocument && this.user1 && this.user2 && this.user1 !== this.user2
    }
  },

  methods: {
    async compare() {
      if (!this.isValid || this.isChecking) return;
      
      this.isChecking = true;
      try {
        // Check if we can get the comparison data before emitting
        await this.$services.annotation.getComparisonData(
          this.projectId,
          this.selectedDocument,
          this.user1,
          this.user2
        );
        
        // Only emit if no error occurred
        this.$emit('compare', {
          documentId: this.selectedDocument,
          user1: this.user1,
          user2: this.user2
        });
      } catch (error) {
        console.error('Error checking comparison data:', error);
        this.$emit('error', 'Database unavailable at the moment, please try again later.');
        // Don't emit compare event when there's an error
        return;
      } finally {
        this.isChecking = false;
      }
    }
  }
})
</script>