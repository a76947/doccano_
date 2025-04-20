<script setup>
import { ref, computed } from 'vue';
import Search from './Search.vue';

const searchFilter = ref('');

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
</script>

<template>
    <div class="bg-white relative border rounded-lg">
        <div class="flex items-center justify-between">
            <Search @search="handleSearch" />
        </div>

        <table class="w-full text-sm text-left text-gray-500">
            <thead class="text-xs text-gray-700 uppercase bg-gray-50">
                <tr>
                    <th class="px-4 py-3 border-b">Text</th>
                    <th class="px-4 py-3 border-b">Percentages</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="(item, index) in filteredItem" :key="index" class="border-b">
                    <td class="px-4 py-3 font-medium text-grey-900">
                        {{ item.text.length > 80 ? item.text.slice(0, 80) + '...' : item.text }}
                    </td>
                    <td class="px-4 py-3">
                        <span v-for="(value, key, idx) in item.percentages" 
                              :key="idx" 
                              class="inline-block bg-blue-100 
                              text-blue-800 text-xs 
                              font-semibold mr-2 px-2.5 py-0.5 rounded">
                            {{ key }}: {{ value }}
                        </span>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>
