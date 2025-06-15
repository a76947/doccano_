<template>
  <div class="bg-white relative border rounded-lg">
    <table class="w-full text-sm text-left text-gray-500">
      <thead class="text-xs text-gray-700 uppercase bg-gray-50">
        <tr>
          <th class="px-4 py-3 border-b">Regras</th>
        </tr>
      </thead>
      <tbody>
        <tr 
          v-for="(rule, index) in items" 
          :key="index" 
          class="border-b"
        >
          <td class="px-4 py-3 font-medium text-gray-900">
            {{ rule }}
          </td>
        </tr>
      </tbody>
    </table>
    <v-btn color="red" @click="openConfirmationOverlay">
      Finalizar Sessão
    </v-btn>
    
    <v-dialog v-model="showConfirmation" max-width="400px">
      <v-card>
        <v-card-title class="headline">Confirma Finalização</v-card-title>
        <v-card-text>
          <p>Deseja finalizar esta sessão para as regras abaixo?</p>
          <ul>
            <li v-for="(rule, index) in items" :key="index">
              <strong>{{ rule }}</strong>
            </li>
          </ul>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" text @click="confirmFinalization">Confirmar</v-btn>
          <v-btn color="error" text @click="closeConfirmation">Cancelar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const emit = defineEmits(['onFinish']);

const { items } = defineProps({
  items: {
    type: Array,
    required: true
  }
});

const showConfirmation = ref(false);

// Abre o overlay (não há necessidade de selecionar uma regra em específico)
function openConfirmationOverlay() {
  showConfirmation.value = true;
}

// Fecha o overlay sem confirmar a finalização
function closeConfirmation() {
  showConfirmation.value = false;
}

// Confirma a finalização e emite o evento com as regras exibidas
function confirmFinalization() {
  emit('onFinish', { confirmed: true, rules: items });
  showConfirmation.value = false;
}
</script>