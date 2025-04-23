<script setup>
import { ref, computed } from 'vue';
import Search from './Search.vue';

const searchFilter = ref('');
const showForm = ref(false);
const selectedItem = ref(null);

const props = defineProps({
    items: {
        type: Array,
        required: true
    },
});

const emit = defineEmits(['open-create']);

const handleSearch = (searchTerm) => {
    searchFilter.value = searchTerm;
};

const filteredItem = computed(() => {
    if (!searchFilter.value) return props.items;
    const term = searchFilter.value.toLowerCase();
    return props.items.filter(item => {
        const textMatch = item.text.toLowerCase().includes(term);
        const percentageMatch = item.percentages 
            ? Object.entries(item.percentages).some(([key, value]) =>
                  key.toLowerCase().includes(term) ||
                  value.toString().toLowerCase().includes(term)
              )
            : false;
        return textMatch || percentageMatch;
    });
});

// Emite o evento para abrir o overlay no index
const handleAction = (item) => {
    emit('open-create', item);
    console.log("Evento open-create emitido para o item:", item);
};

const handleFormSubmit = (formData) => {
    // Aqui você pode tratar a submissão do formulário, por exemplo,
    // enviar os dados para a API ou atualizar o estado da aplicação
    console.log("Formulário enviado com os dados:", formData);
};

const closeForm = () => {
    showForm.value = false;
    selectedItem.value = null;
};
</script>

<template>
  <div>
    <div class="bg-white relative border rounded-lg">
      <div class="flex items-center justify-between">
        <Search @search="handleSearch" />
      </div>
      <table class="w-full text-sm text-left text-gray-500">
        <thead class="text-xs text-gray-700 uppercase bg-gray-50">
          <tr>
            <th class="px-4 py-3 border-b">Text</th>
            <th class="px-4 py-3 border-b">Percentages</th>
            <th class="px-4 py-3 border-b">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="(item, index) in filteredItem" 
            :key="index" 
            class="border-b"
          >
            <td class="px-4 py-3 font-medium text-grey-900">
              {{ item.text.length > 80 
                ? item.text.slice(0, 80) + '...' 
                : item.text }}
            </td>
            <td class="px-4 py-3">
              <span 
                v-for="(value, key, idx) in item.percentages"
                :key="idx"
                class="inline-block bg-blue-100 text-blue-800 text-xs font-semibold 
                       mr-2 px-2.5 py-0.5 rounded"
              >
                {{ key }}: {{ value }}
              </span>
            </td>
            <td class="px-4 py-3">
              <button 
                class="bg-blue-500 text-white px-3 py-1 rounded"
                @click="handleAction(item)"
              >
                Criar Perguntas
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <!-- Teleport para montar o modal fora do container atual -->
    <teleport to="body">
      <CreateQuestionsForm
        v-if="showForm"
        :item="selectedItem"
        @close="closeForm"
        @submit="handleFormSubmit"
      />
    </teleport>
  </div>
</template>
