<template>
  <v-btn
    outlined
    @click="$emit('click')"
    :disabled="disabled"
  >
    <v-icon left>mdi-compare</v-icon>
    {{ $t('compare') || 'Compare' }}
  </v-btn>
</template>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  props: {
    disabled: {
      type: Boolean,
      default: false
    }
  }
})
</script>