interface CustomProperties extends Vue {
  $axios: AxiosInstance;
}

declare module 'vue/types/vue' {
  interface Vue extends CustomProperties {}
}

declare module 'vuex/types/index' {
  interface Store<S> {
    getters: {
      'auth/isStaff': boolean;
      'auth/getUserId': number;
      'auth/getUsername': string;
    };
  }
} 