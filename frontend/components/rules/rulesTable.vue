<template>
  <div>
    <div class="bg-white relative border rounded-lg">
      <div class="flex items-center justify-between">
        <Search @search="handleSearch" />
      </div>
      <table class="w-full text-sm text-left text-gray-500">
        <thead class="text-xs text-gray-700 uppercase bg-gray-50">
          <tr>
            <th class="px-4 py-3 border-b">Regra</th>
            <th class="px-4 py-3 border-b"></th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="(item, index) in filteredItem" 
            :key="index" 
            class="border-b"
          >
            <td class="px-4 py-3 font-medium text-grey-900">
              {{ item.regra.length > 80 ? item.regra.slice(0, 80) + '...' : item.regra }}
            </td>
            <td class="px-4 py-3">
              <button 
                class="bg-blue-500 text-white px-3 py-1 rounded"
                @click="openAcaoOverlay(item)"
              >
                Ações
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Overlay de ações -->
    <v-dialog v-model="showAcao" max-width="600px">
      <v-card>
        <v-card-title class="headline">Ações para:</v-card-title>
        <v-card-text>
          <div class="mb-4">
            <strong>Regra:</strong>
            <div v-if="!isEditing">{{ selectedItem?.regra }}</div>
            <div v-else>
              <v-textarea v-model="editedRegra" label="Editar regra" required />
            </div>
          </div>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <!-- Botões para o modo não edição -->
          <template v-if="!isEditing">
            <v-btn text @click="cancelAcao">Cancel</v-btn>
            <v-btn color="error" text @click="removeAcao">Remove</v-btn>
            <v-btn color="primary" text @click="startEditing">Edit</v-btn>
          </template>
          <!-- Botões para o modo edição -->
          <template v-else>
            <v-btn text @click="cancelEdit">Cancel</v-btn>
            <v-btn color="primary" text @click="confirmEdit">Confirm</v-btn>
          </template>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import Search from './searchRule.vue';

const emit = defineEmits(['deleteRule']);

const searchFilter = ref('');
const showAcao = ref(false);
const selectedItem = ref(null);
const isEditing = ref(false);
const editedRegra = ref('');

const props = defineProps({
  items: {
    type: Array,
    required: true
  },
});

const handleSearch = (searchTerm) => {
  searchFilter.value = searchTerm;
};

const filteredItem = computed(() => {
  if (!searchFilter.value) return props.items;
  const term = searchFilter.value.toLowerCase();
  return props.items.filter(item => item.regra.toLowerCase().includes(term));
});

const openAcaoOverlay = (item) => {
  selectedItem.value = item;
  // Reseta estado de edição
  isEditing.value = false;
  editedRegra.value = '';
  showAcao.value = true;
};

const cancelAcao = () => {
  showAcao.value = false;
};

const removeAcao = () => {
  if (selectedItem.value) {
    emit('deleteRule', selectedItem.value.id);
  }
  showAcao.value = false;
};

const startEditing = () => {
  // Inicia o modo edição e preenche o campo com o valor atual
  if (selectedItem.value) {
    isEditing.value = true;
    editedRegra.value = selectedItem.value.regra;
  }
};

const cancelEdit = () => {
  // Cancelar a edição apenas volta para o modo visual sem fechar o overlay
  isEditing.value = false;
};

const confirmEdit = () => {
  console.log('Edited rule:', editedRegra.value, 'for item:', selectedItem.value);
  // Aqui você pode adicionar a lógica para atualizar a regra no back-end
  isEditing.value = false;
  showAcao.value = false;
};
</script>
