<template>
  <div class="bg-white relative border rounded-lg">
    <table class="w-full text-sm text-left text-gray-500">
      <thead class="text-xs text-gray-700 uppercase bg-gray-50">
        <tr>
          <th class="px-4 py-3 border-b">Regras</th>
          <th class="px-4 py-3 border-b">Concorda com Esta Regra?</th>
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
          <td class="px-4 py-3">
            <v-radio-group v-model="responses[index]" row>
              <v-radio label="Sim" value="sim" />
              <v-radio label="Não" value="nao" />
            </v-radio-group>
          </td>
        </tr>
      </tbody>
    </table>
    <v-btn color="success" @click="onSubmit">
      Submit
    </v-btn>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

// Atualize os nomes dos eventos para que correspondam ao que o componente pai espera.
// Por exemplo, se o pai está ouvindo o evento "onSubmit", vamos emitir "onSubmit"

const emit = defineEmits(['onSubmit']);

const props = defineProps({
  items: {
    type: Array,
    required: true
  }
});

const responses = ref([]);

watch(
  () => props.items,
  (newItems) => {
    responses.value = newItems.map(() => null);
  },
  { immediate: true }
);

function onSubmit() {
  const allAnswered = responses.value.every(r => r === 'sim' || r === 'nao');

  if (!allAnswered) {
    console.log('Nem todas as respostas foram dadas.');
    // Emite um objeto indicando que as respostas estão incompletas
    emit('onSubmit', { incomplete: true });
  } else {
    console.log('Todas as respostas foram dadas:', responses.value);
    // Emite as respostas quando estiverem completas
    emit('onSubmit', { incomplete: false, responses: responses.value });
  }
}
</script>