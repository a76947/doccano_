<script setup>
const emit = defineEmits(['search']);

const search = (e) => {
    emit('search', e.target.value);
};
</script>

<template>

    <form class="py-3 px-4 flex items-center">
        <label class="sr-only" >Search</label>
        
        <div class="relative w-full">
            <input 
            type="text" 
            @input="search"
            placeholder="Search" 
            class="bg-gray-50 
            border 
            border-gray-300 
            text-gray-900
            text-sm 
            block w-full 
            p-2.5
            rounded-lg 
            focus:outline-none 
            focus:ring-2 
            focus:ring-blue-500"
            required>
            

        </div>
    </form>
        
</template>