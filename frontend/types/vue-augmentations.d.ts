import Vue from 'vue';
import { NuxtAppOptions } from '@nuxt/types';

declare module 'vue/types/vue' {
  interface Vue {
    $router: NuxtAppOptions['app']['$router'];
    $route: NuxtAppOptions['app']['$route'];
    $t: NuxtAppOptions['app']['$i18n']['t'];
    $repositories: NuxtAppOptions['app']['$repositories'];
    $services: NuxtAppOptions['app']['$services'];
    $toasted: any; // Add this if you use vue-toasted
    localePath: NuxtAppOptions['app']['localePath'];
    $fetch: () => Promise<void>;
    $store: NuxtAppOptions['app']['$store'];
    // Assuming 'project' is a getter from Vuex and its type is available
    // If not, you might need to define its structure more precisely.
    project: {
      status: string;
      isImageProject: boolean;
      isAudioProject: boolean;
      projectType: string;
      labels: any[];
    };
  }
}

// Add declarations for custom modules or globally available types if needed
declare module '*.vue' {
  import Vue from 'vue';
  export default Vue;
} 